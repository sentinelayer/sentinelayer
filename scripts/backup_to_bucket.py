"""Private encrypted bucket backup; optional restore into a newly created test DB.

Owner credentials belong only to this offline job. Never accepts a restore target.
The manifest and dump share a PostgreSQL snapshot, including row counts.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
from datetime import UTC, datetime

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import parse_dsn

MAGIC = b"SLBK01"
CHUNK = 65536


def crypt_file(source: Path, target: Path, key: bytes, decrypt: bool = False) -> None:
    with source.open("rb") as src, target.open("wb") as dst:
        if decrypt:
            if source.stat().st_size < len(MAGIC) + 12 + 16:
                raise ValueError("Truncated backup")
            if src.read(len(MAGIC)) != MAGIC:
                raise ValueError("Invalid backup format")
            nonce = src.read(12)
            src.seek(-16, 2)
            tag = src.read(16)
            remaining = src.tell() - len(MAGIC) - 12 - 16
            src.seek(len(MAGIC) + 12)
            context = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
        else:
            nonce = secrets.token_bytes(12)
            dst.write(MAGIC + nonce)
            remaining = source.stat().st_size
            context = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
        context.authenticate_additional_data(MAGIC)
        while remaining:
            block = src.read(min(CHUNK, remaining))
            if not block:
                raise ValueError("Truncated backup")
            remaining -= len(block)
            dst.write(context.update(block))
        dst.write(context.finalize())
        if not decrypt:
            dst.write(context.tag)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def counts(connection) -> dict[str, int]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        tables = [row[0] for row in cursor.fetchall()]
        result = {}
        for table in tables:
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM public.{}").format(sql.Identifier(table)))
            result[table] = cursor.fetchone()[0]
        return result


def pg_env(dsn: dict[str, str], database: str | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for field, variable in {"host": "PGHOST", "port": "PGPORT", "user": "PGUSER",
                            "password": "PGPASSWORD", "dbname": "PGDATABASE",
                            "sslmode": "PGSSLMODE"}.items():
        if field in dsn:
            env[variable] = dsn[field]
    if database:
        env["PGDATABASE"] = database
    return env


def run_pg(args: list[str], env: dict[str, str]) -> None:
    # Do not forward subprocess errors or DSNs into platform logs.
    result = subprocess.run(args, env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE, timeout=600, check=False)
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed (exit {result.returncode})")


def main() -> None:
    import boto3
    from botocore.config import Config

    os.umask(0o077)
    url = os.environ["BACKUP_DATABASE_URL"]
    key = base64.urlsafe_b64decode(os.environ["KMS_KEY"])
    if len(key) != 32:
        raise ValueError("Invalid encryption key")
    key = hashlib.sha256(b"sentinel-backup-encryption-v1\0" + key).digest()
    dsn = parse_dsn(url)
    bucket = os.environ["S3_BUCKET"]
    client = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"],
                          region_name=os.environ["S3_REGION"],
                          aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
                          aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
                          config=Config(connect_timeout=10, read_timeout=60,
                                        retries={"max_attempts": 3},
                                        s3={"addressing_style": "path"},
                                        request_checksum_calculation="when_required",
                                        response_checksum_validation="when_required"))
    prefix = "sentinelayer/" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    with tempfile.TemporaryDirectory(prefix="sentinel-backup-") as directory:
        root = Path(directory)
        dump, encrypted, downloaded, restored = [root / name for name in
                                                  ("backup.dump", "backup.enc", "download.enc", "restore.dump")]
        with psycopg2.connect(url) as source:
            source.set_session(isolation_level="REPEATABLE READ", readonly=True)
            with source.cursor() as cursor:
                cursor.execute("SELECT pg_export_snapshot()")
                snapshot = cursor.fetchone()[0]
            expected = counts(source)
            run_pg(["pg_dump", "--format=custom", "--no-owner", "--no-privileges",
                    "--snapshot=" + snapshot, "--file=" + str(dump)], pg_env(dsn))
        if dump.stat().st_size > int(os.getenv("BACKUP_MAX_BYTES", str(300 * 1024 * 1024))):
            raise ValueError("Backup exceeds job disk budget")
        crypt_file(dump, encrypted, key)
        manifest = {"format": 1, "created_at": datetime.now(UTC).isoformat(),
                    "encrypted_sha256": digest(encrypted), "dump_sha256": digest(dump),
                    "table_counts": expected}
        dump.unlink()
        payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
        auth_key = hashlib.sha256(b"sentinel-backup-manifest-v1\0" + key).digest()
        signature = hmac.new(auth_key, payload, hashlib.sha256).hexdigest()
        client.upload_file(str(encrypted), bucket, prefix + ".enc")
        encrypted.unlink()
        client.put_object(Bucket=bucket, Key=prefix + ".json",
                          Body=json.dumps({"manifest": manifest, "hmac_sha256": signature}).encode(),
                          ContentType="application/json")
        # Read back both objects and authenticate before any restore.
        remote = json.loads(client.get_object(Bucket=bucket, Key=prefix + ".json")["Body"].read())
        remote_payload = json.dumps(remote["manifest"], sort_keys=True, separators=(",", ":")).encode()
        if not hmac.compare_digest(remote["hmac_sha256"], hmac.new(auth_key, remote_payload, hashlib.sha256).hexdigest()):
            raise ValueError("Backup manifest authentication failed")
        client.download_file(bucket, prefix + ".enc", str(downloaded))
        if digest(downloaded) != remote["manifest"]["encrypted_sha256"]:
            raise ValueError("Encrypted backup checksum mismatch")
        crypt_file(downloaded, restored, key, decrypt=True)
        if digest(restored) != remote["manifest"]["dump_sha256"]:
            raise ValueError("Backup plaintext checksum mismatch")
        run_pg(["pg_restore", "--list", str(restored)], pg_env(dsn))
        print("Encrypted bucket backup uploaded and read-back verified", flush=True)
        if os.getenv("BACKUP_RESTORE_DRILL", "0") == "1":
            test_name = "sentinel_restore_" + secrets.token_hex(16)
            admin = psycopg2.connect(url)
            admin.autocommit = True
            created = False
            try:
                with admin.cursor() as cursor:
                    cursor.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(test_name)))
                created = True
                run_pg(["pg_restore", "--no-owner", "--no-privileges", "--exit-on-error",
                        "--single-transaction", str(restored)], pg_env(dsn, test_name))
                target_dsn = dict(dsn, dbname=test_name)
                with psycopg2.connect(**target_dsn) as target:
                    if counts(target) != remote["manifest"]["table_counts"]:
                        raise ValueError("Restore row counts differ from snapshot")
                    with target.cursor() as cursor:
                        cursor.execute("SELECT version_num FROM alembic_version")
                        version = cursor.fetchone()[0]
                print(f"Isolated restore PASS: {len(expected)} tables; schema {version}; snapshot row counts match", flush=True)
            finally:
                if created:
                    with admin.cursor() as cursor:
                        cursor.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(test_name)))
                    print("Disposable restore database removed", flush=True)
                admin.close()
        print("Backup job completed", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Backup job failed: {type(error).__name__}; credentials and database errors withheld", flush=True)
        raise SystemExit(1) from None
