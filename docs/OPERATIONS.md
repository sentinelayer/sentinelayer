# SentinelLayer Operations Runbook

Dokumen ini menjelaskan operasi yang harus dilakukan setelah branch perbaikan di-review. **Pull request tetap harus direview dan di-merge secara eksplisit; deployment production tidak dilakukan otomatis oleh repository change ini.**

## Preflight production

Set `DATABASE_URL`, `POSTGRES_PASSWORD`, `JWT_SECRET` dengan minimal 32 karakter acak, `METRICS_TOKEN`, dan `WEBHOOK_SECRET` dari secret manager. Set `SL_ENV=production` dan `SL_AUTO_CREATE_SCHEMA=0`. Gateway production juga membutuhkan `SL_APPROVED_ARTIFACT_HASH` dan `SL_RUNNING_ARTIFACT_HASH` yang sama-sama berasal dari artefak yang telah diverifikasi.

Jalankan migration hanya dari control-plane deployment:

```sh
PYTHONPATH=/app alembic -c alembic.ini upgrade head
```

Aplikasi production tidak boleh memakai `Base.metadata.create_all`; migration adalah satu-satunya schema lifecycle. Setelah migration, verifikasi bahwa RLS aktif pada seluruh tabel tenant-scoped dan bahwa `app.tenant_id` di-set pada setiap transaksi request.

## Maintenance worker

Worker dijalankan sebagai service terpisah menggunakan:

```sh
PYTHONPATH=/app python -m control_plane.app.workers.runner --loop
```

`WORKER_INTERVAL_SECONDS` minimal 10 detik dan default 300 detik. Worker menjalankan evidence expiry dan offboarding purge. File lock mencegah dua worker pada instance yang sama berjalan bersamaan. Untuk HA multi-instance, gunakan distributed lock/leader election di deployment platform; file lock saja tidak cukup lintas host.

## Backup dan restore

Backup menggunakan PostgreSQL custom format `.dump`, bukan ekstensi `.sql` yang menyesatkan. Backup disimpan di `BACKUP_DIR` dan setiap hasil mencantumkan ukuran serta SHA-256. Sebelum restore, jalankan verification; restore destructive harus memanggil `restore_backup(path, allow_destructive=True)` secara eksplisit. Restore selalu memakai `--clean --if-exists --no-owner --exit-on-error --single-transaction`.

Contoh inspeksi backup melalui Python application context:

```python
from control_plane.app.backup.backup import BackupManager
manager = BackupManager()
print(manager.list_backups())
print(manager.verify_backup("backups/full_YYYYMMDD_HHMMSS.dump"))
```

Lakukan restore drill berkala pada database sementara, ukur RTO/RPO, verifikasi row counts dan tenant isolation, lalu simpan hasilnya sebagai evidence. Jangan melakukan restore ke production tanpa change approval dan backup current-state terlebih dahulu.

## Monitoring dan alerting

Scrape `/metrics` menggunakan `X-Metrics-Token: $METRICS_TOKEN`. Endpoint mengembalikan 503 di production apabila `METRICS_TOKEN` belum dikonfigurasi. Endpoint `/health` hanya liveness; `/api/v1/health/readiness` memeriksa koneksi database dan mengembalikan 503 apabila database belum siap.

Runtime security events dikirim ke `POST /api/v1/events` dengan `event_type`, `source`, `severity`, `risk_score`, `outcome`, serta data terstruktur. Metrics, heatmap, user risk, dan SLA report hanya membaca event milik tenant caller dalam bounded time window.

## Offboarding

Soft offboarding menandai aplikasi dan membuat retention schedule. Hard offboarding tidak menghapus resource langsung; request masuk status `scheduled` dan purge baru boleh terjadi setelah `hard_delete_at`. Record offboarding dan audit event dipertahankan setelah resource dihapus sehingga deletion evidence tetap tersedia.

## Remaining production evidence

Repository sekarang memiliki code path dan automated tests untuk fitur-fitur di atas, tetapi bukti environment nyata masih harus dikumpulkan: PostgreSQL RLS cross-tenant test, restore drill, load/chaos test, signed runtime attestation dengan credential nyata, multi-region failover, dan independent security review.
