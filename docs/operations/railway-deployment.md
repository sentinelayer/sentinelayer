# Railway deployment

Set service build and deploy settings explicitly. Legacy root railway.toml was
removed: it overrode the dedicated migrator Dockerfile despite the service setting.
Railway's connector now rejects custom Config as Code paths as deprecated.

| Service | Dockerfile | Start command | Restart | Public |
| --- | --- | --- | --- | --- |
| sentinelayer | Dockerfile | /app/scripts/start_single_service.sh | ON_FAILURE | Gateway port 8080 |
| sentinel-migrate | Dockerfile.migrate | sh /app/scripts/migrate_database.sh | NEVER | No |
| sentinel-backup | Dockerfile.backup | /opt/backup/bin/python /app/backup_to_bucket.py | NEVER | No |

Provision private PostgreSQL 18 and Redis with persistent volumes. Run migration
and configure_database_roles before the API. Inject migration-owned credentials
only into the migrator and offline backup job. The API uses sentinel_app,
sentinel_auth and sentinel_worker URLs, production environment, startup migration
disabled, auto schema creation disabled, and stable platform-managed secrets.

The backup job requires BACKUP_DATABASE_URL, KMS_KEY, S3_BUCKET, S3_ENDPOINT,
S3_REGION, S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY. Use private bucket reference
variables. Set BACKUP_RESTORE_DRILL=1 for the initial drill, then 0 for daily jobs.
Daily schedule: 0 3 * * *. Do not attach a healthcheck or public domain.

Backups use a consistent PostgreSQL snapshot, streaming AES-256-GCM encryption,
an authenticated manifest, ciphertext and plaintext checksums, and bucket
read-back verification. Restore drills create a random, fresh database, restore
there, compare every public table's snapshot row count, check the Alembic version,
and remove the test database in a finally block. They never accept an external
restore target or overwrite the active database. The default compressed dump
limit is 300 MiB to stay within the Hobby job disk budget; BACKUP_MAX_BYTES can
change it after scaling disk capacity. The first implementation retains
all bucket objects; configure retention/lifecycle separately as storage grows.

Preserve the encryption key independently in the platform secret manager. A
backup cannot be recovered after its key is lost; retain older keys during key
rotation. A same-account bucket is not an independent disaster-recovery copy.
The drill checks data/schema recovery; role grants must be reapplied using the
migrator after a full replacement database restore.
