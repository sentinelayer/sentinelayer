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

## Owned signed-policy pilot

The owned Railway hostname uses policy `6f01d176-58df-4e6a-bbd0-5be014259cee`
in tenant `sentinel-pilot`; backend and policy fetch/ack address numeric loopback
port 8005 directly. Public signing material was derived in the isolated bootstrap
job from the trusted deployment key, then pinned in the gateway environment.
The gateway service account is active, non-admin, and uses a 90-day API key.

The third persistent volume mounts at `/var/lib/sentinelayer-policy`. Its private
`runtime` directory holds the version floor. Railway mounts volumes as root, so
RAILWAY_RUN_UID=0 initializes only that fixed, verified mount before `setpriv`
drops to UID/GID 1000, clears supplementary groups/capabilities, and enables
no-new-privileges. Initialization uses Python isolated mode without site imports,
directory descriptors and no-follow opens. Launcher files and parent directories
are root-owned; the application processes run as UID 1000.

Owner access: the one-off bootstrap job requires SL_PILOT_BOOTSTRAP=1 and
platform variables PILOT_ADMIN_EMAIL, PILOT_ADMIN_PASSWORD,
PILOT_ADMIN_MFA_SECRET, PILOT_SERVICE_PASSWORD and PILOT_GATEWAY_API_KEY.
Keep their values private in `sentinel-migrate` Railway variables. The owner
must import the MFA seed into their own authenticator and use its current code
at login. The account cannot receive a login token without MFA. Re-running
bootstrap refuses conflicting identities and never resets existing credentials.

Run `python /app/scripts/verify_pilot.py` as a private one-off job with
SL_PILOT_VERIFY=1. PILOT_HOT_UPDATE=1 enables a temporary deny-rule update and
restores the original rules as a higher signed version in a finally block.
The verifier checks real owner MFA, path boundary enforcement, gateway receipts,
and logout revocation; it never prints passwords, API keys or MFA seeds.
Set PILOT_HOT_UPDATE=0 when repeating it after a restart. Health alone does not
prove policy enforcement; the signed probe and current receipt are required.
