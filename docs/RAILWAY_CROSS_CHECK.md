# Railway Cross-Check Checklist

Dokumen ini dipakai setelah deployment dari `main` selesai. **CI green membuktikan repository dan image build; checklist ini mengumpulkan bukti runtime Railway yang tidak dapat dibuktikan dari GitHub saja.** Jangan memasukkan nilai secret ke screenshot atau log yang dibagikan.

## 1. Deployment dan migration

Pastikan service production mendeploy commit terbaru dari branch `main`, memakai builder **Dockerfile**, bukan Nixpacks. Pre-deploy command harus menyelesaikan `PYTHONPATH=/app alembic -c alembic.ini upgrade head` tanpa error. Catat commit SHA, waktu deployment, hasil migration, dan status healthcheck.

## 2. Runtime topology

Log startup harus menunjukkan control-plane pada loopback `8005`, risk engine pada `8090`, behavior engine pada `8091`, maintenance worker, lalu Gateway pada port yang diberikan Railway. Bila salah satu child process mati, container harus berhenti dan Railway harus melakukan restart; container tidak boleh terlihat sehat ketika security dependency mati.

Buka endpoint berikut dari domain publik yang sama:

| Check | Expected evidence |
|---|---|
| `/health` | HTTP 200 dan readiness Gateway berhasil memeriksa control-plane, risk, serta behavior |
| `/` | Shell dashboard SentinelLayer tampil dari domain yang sama |
| `/events` | SPA fallback tampil tanpa `404` |
| `/docs` | FastAPI docs tampil bila endpoint tersebut memang diizinkan untuk environment evaluasi |

## 3. Environment contract

Pertahankan `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `KMS_KEY`, `METRICS_TOKEN`, `SL_ENV=production`, `SL_AUTO_CREATE_SCHEMA=0`, `SL_ENFORCE_PROVENANCE=0`, `BACKUP_DIR`, konfigurasi webhook, dan konfigurasi worker. `BOOTSTRAP_ADMIN_EMAIL` serta `BOOTSTRAP_ADMIN_TOKEN` hanya digunakan untuk akun admin pertama. `PORT` disediakan Railway dan tidak perlu diketik manual. Jangan mengaktifkan provenance enforcement sebelum proses signed artifact/attestation dan approved-versus-running digest benar-benar tersedia.

## 4. Bootstrap dan authentication

Gunakan email yang sama persis dengan `BOOTSTRAP_ADMIN_EMAIL` dan bootstrap token hanya sekali untuk membuat admin pertama. Setelah berhasil, nonaktifkan atau hapus `BOOTSTRAP_ADMIN_TOKEN`, deploy ulang, lalu pastikan token lama tidak dapat membuat admin kedua. Login ulang dengan akun admin, aktifkan TOTP/backup code, dan uji bahwa mutasi policy serta risk calibration menolak token admin yang tidak membawa MFA terverifikasi.

## 5. Data-plane smoke test

Gunakan upstream aman yang memang dimiliki atau diizinkan untuk pengujian. Request normal harus diteruskan ke upstream dan decision harus tercatat. Payload SQL injection/XSS/traversal harus ditolak oleh CRS/body WAF. Request gzip harus dinormalisasi sebelum inspeksi. Payload di atas batas inspeksi 2 MiB harus ditolak, bukan diteruskan tanpa pemeriksaan. Uji rate limit dengan traffic yang sah dan pastikan limit hit menghasilkan `429`, sedangkan kegagalan Redis mengikuti failure matrix dan tidak diam-diam fail-open pada endpoint critical.

## 6. Dashboard dan audit evidence

Pastikan login, register, Risk, Events, Policies, dan halaman dashboard menggunakan domain serta API prefix yang sama. Setelah request smoke test, verifikasi decision/event tenant-scoped muncul di dashboard. Buat satu perubahan policy setelah MFA aktif, pastikan `signature`, `signing_key_id`, dan `signature_valid` muncul, lalu uji rollback hanya terhadap versi yang signature-nya valid.

## 7. Secret rotation dan evidence retention

Setelah deployment stabil dan bootstrap selesai, rotate `JWT_SECRET`, `METRICS_TOKEN`, `KMS_KEY`, bootstrap token, serta credential PostgreSQL/Redis yang sebelumnya pernah tampil di screenshot atau chat. Lakukan rotation melalui Railway/secret manager, bukan melalui chat. Simpan hanya bukti non-secret: deployment SHA, status migration, status health, HTTP status, error class, timestamp, dan screenshot yang sudah disensor.

## 8. Evidence yang masih diperlukan sebelum GA

Technical GA dan Commercial GA belum dapat disimpulkan dari checklist ini saja. Masih diperlukan production/staging traffic yang disetujui, signed runtime attestation, KMS/secret lifecycle, HA/failover, load dan chaos tests, restore drill dengan RTO/RPO, labelled calibration data, central alerting, pilot outcomes, SLA/support process, dan independent security review.
