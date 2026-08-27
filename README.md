# SentinelLayer

SentinelLayer adalah security platform multi-tenant yang sedang dibangun untuk melindungi API dan workflow sensitif melalui satu data plane terintegrasi: normalisasi request, OWASP CRS/Coraza WAF, rate limiting Redis, behavior assessment, risk scoring, decision safety, upstream proxy, control plane, dan dashboard.

> Status repository tidak sama dengan status production. Build dan test yang lulus membuktikan code path pada commit yang diuji; status deployment, availability, calibration, dan kesiapan komersial memerlukan evidence dari environment nyata.

## Kemampuan yang tersedia di repository

| Area | Implementasi saat ini | Batas yang masih harus dibuktikan |
|---|---|---|
| Data plane | Gateway Go dengan request normalization, body inspection, Coraza + OWASP CRS, SSRF/desync guard, rate limiting atomic, behavior/risk/decision pipeline, dan upstream proxy | Traffic Railway nyata, load, failure drill, latency/error budget, serta upstream customer nyata |
| Control plane | FastAPI dengan PostgreSQL/Alembic, tenant scoping, session/API-key lifecycle, MFA gate, RBAC, audit events, policies, risk records, dan dashboard SPA | PostgreSQL/RLS production evidence, external review, backup/restore drill, dan HA |
| Policy safety | Versioned policy records, Ed25519 signature metadata, signature verification pada rollback, approval workflow, dan capability execution terbatas | External KMS/HSM lifecycle, key rotation tanpa invalidasi tak terkelola, signed release admission, dan independent review |
| Runtime state | Behavior frequency/sequence state dan risk correlation menggunakan Redis pada production; memory fallback hanya untuk development | Redis HA/failover, retention/eviction policy, multi-region consistency, dan chaos evidence |
| Integrations | Webhook registration, HMAC timestamp/nonce/attempt metadata, retry/DLQ worker, dan encrypted secret storage | Delivery ke endpoint customer nyata, alert routing, secret rotation, dan operational SLA |
| Observability | Prometheus endpoint, security metrics, runtime events, risk decisions, dan dashboard pages | Central logs, traces, alert escalation, retention, redaction, dan cardinality governance |

## Runtime topology awal

Tahap awal Railway memakai satu service dengan satu public Gateway. Launcher internal menjalankan control plane pada loopback `8005`, risk engine pada `8090`, behavior engine pada `8091`, maintenance worker, lalu Gateway pada `PORT` yang diberikan platform. Dashboard disajikan dari control plane pada domain yang sama; route API tetap berada di bawah `/api/v1`.

Topology ini dipilih untuk memulihkan alur end-to-end pada tahap awal. **Topology ini bukan klaim HA atau enterprise production readiness.** Untuk scale-out, service perlu dipisah, state Redis/PostgreSQL perlu diuji lintas instance, dan deployment membutuhkan failover, backup/restore, load, chaos, serta observability evidence.

## Menjalankan secara lokal

Development membutuhkan Python 3.11+, Node.js, Go 1.25+, PostgreSQL, dan Redis. Salin konfigurasi dari `.env.example`, gunakan secret development lokal, lalu jalankan migration melalui Alembic. Jangan menaruh secret production pada repository atau issue.

```bash
alembic -c alembic.ini upgrade head
npm --prefix dashboard ci
npm --prefix dashboard run build
(cd gateway && go test ./... && go build ./...)
pytest -q tests/unit
```

Production menggunakan `SL_AUTO_CREATE_SCHEMA=0`; schema harus dimigrasikan oleh Railway pre-deploy command. Gateway membutuhkan `JWT_SECRET` minimal 32 byte dan koneksi Redis. Untuk bootstrap admin, gunakan `BOOTSTRAP_ADMIN_EMAIL` dan `BOOTSTRAP_ADMIN_TOKEN` sebagai secret Railway; token tersebut hanya boleh digunakan sekali dan tidak disimpan plaintext oleh aplikasi.

`SL_ENFORCE_PROVENANCE` tetap harus diaktifkan hanya setelah organisasi memiliki signed image/attestation dan nilai approved-versus-running yang berasal dari proses release yang dapat diaudit. `KMS_KEY`, JWT secret, metrics token, bootstrap token, dan credential lain harus dibuat serta dirotasi melalui secret manager platform. Jangan kirim nilai secret melalui chat.

## Evidence dan status penerimaan

CI pada `main` menjalankan unit/integration tests, Go build, Docker image build, security scans, SBOM, dan E2E security checks. Evidence tersebut tetap berstatus repository/CI evidence. SentinelLayer belum boleh disebut Technical GA, Commercial GA, certified, memiliki uptime tertentu, atau bebas insiden/false positive sampai production deployment, labelled calibration data, customer pilot, restore/failover drill, independent security review, dan acceptance record benar-benar tersedia.

## Lisensi

MIT © 2026 SentinelLayer.
