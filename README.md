# SentinelLayer

**SentinelLayer** adalah security platform **multi-tenant** untuk melindungi API dan workflow sensitif melalui satu data plane terintegrasi. Platform ini menggabungkan normalisasi request, inspeksi body, WAF berbasis **OWASP CRS/Coraza**, rate limiting Redis, behavior assessment, risk scoring, decision safety, upstream proxy, control plane, dan dashboard.

> **Status proyek:** SentinelLayer masih berada pada tahap pengembangan dan pembuktian kesiapan operasional. Keberhasilan build atau test pada repository ini bukan bukti bahwa deployment production telah memiliki availability, kalibrasi, HA, atau kesiapan komersial tertentu.

## Mengapa SentinelLayer?

SentinelLayer dirancang untuk membantu tim keamanan menerapkan pertahanan berlapis di depan API tanpa memisahkan telemetry, policy, risk decision, dan audit trail ke banyak komponen yang tidak terkoordinasi. Setiap request dapat dinormalisasi, diperiksa, diberi konteks risiko, lalu diteruskan atau ditolak berdasarkan policy yang dapat diaudit.

## Kapabilitas utama

| Komponen | Yang tersedia di repository | Evidence lanjutan yang masih diperlukan |
|---|---|---|
| **Gateway / data plane** | Request normalization, body inspection, Coraza + OWASP CRS, SSRF/desync guard, atomic rate limiting, behavior/risk/decision pipeline, dan upstream proxy | Traffic nyata, load test, failure drill, latency/error budget, dan upstream customer |
| **Control plane** | FastAPI, PostgreSQL/Alembic, tenant scoping, session dan API-key lifecycle, MFA gate, RBAC, audit events, policy, risk records, dan dashboard SPA | Evidence PostgreSQL/RLS di production, backup/restore drill, HA, dan independent review |
| **Policy safety** | Versioned policy records, Ed25519 signature metadata, verification saat rollback, approval workflow, dan capability execution terbatas | KMS/HSM lifecycle, key rotation, signed release admission, dan independent review |
| **Runtime state** | Behavior frequency/sequence state dan risk correlation dengan Redis; memory fallback untuk development | Redis HA/failover, retention/eviction policy, konsistensi multi-region, dan chaos evidence |
| **Integrasi** | Webhook registration, HMAC timestamp/nonce/attempt metadata, retry/DLQ worker, dan encrypted secret storage | Endpoint customer nyata, alert routing, secret rotation, dan operational SLA |
| **Observability** | Prometheus endpoint, security metrics, runtime events, risk decisions, dan dashboard pages | Central logs, traces, alert escalation, retention, redaction, dan cardinality governance |

## Arsitektur singkat

Pada deployment awal Railway, satu service menjalankan public Gateway dan komponen internal pada loopback: control plane di port `8005`, risk engine di `8090`, behavior engine di `8091`, serta maintenance worker. Dashboard disajikan oleh control plane pada domain yang sama, sedangkan API tersedia di bawah `/api/v1`.

```text
Client
  │
  ▼
Gateway ──► Request normalization ──► WAF / rate limit
  │                                      │
  │                                      ▼
  │                            Behavior + risk decision
  │                                      │
  └──────────────────────────────────────┴──► Upstream API

Control plane ──► PostgreSQL     Runtime state ──► Redis
       │
       ├── Policies, tenants, RBAC, audit events
       └── Dashboard + API (/api/v1)
```

Topology ini merupakan pilihan tahap awal untuk memulihkan alur end-to-end; **bukan klaim HA atau enterprise production readiness**. Untuk scale-out, service perlu dipisah dan state PostgreSQL/Redis perlu dibuktikan melalui failover, backup/restore, load, chaos, dan observability evidence.

## Quick start lokal

### Prasyarat

Development membutuhkan **Python 3.11+**, **Node.js 22+**, **Go 1.25+**, PostgreSQL, dan Redis.

### Opsi A — menjalankan dengan Docker Compose

```bash
git clone https://github.com/sentinelayer/sentinelayer.git
cd sentinelayer
cp .env.example .env
# Sesuaikan secret development lokal di .env

docker compose up --build
```

Setelah service aktif, gunakan URL dan port yang dipetakan oleh `docker-compose.yml`. Jangan gunakan secret dari file contoh untuk production.

### Opsi B — menjalankan pipeline build dan test

```bash
cp .env.example .env

alembic -c alembic.ini upgrade head
npm --prefix dashboard ci
npm --prefix dashboard run build

(cd gateway && go test ./... && go build ./...)
pytest -q tests/unit
```

Untuk menjalankan integration atau security test, lihat workflow CI di [`.github/workflows`](https://github.com/sentinelayer/sentinelayer/tree/main/.github/workflows) dan dokumentasi operasi di [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

## Konfigurasi penting

| Variabel | Fungsi | Catatan |
|---|---|---|
| `DATABASE_URL` | Koneksi PostgreSQL | Gunakan database terkelola untuk deployment production |
| `REDIS_URL` / `REDIS_ADDR` | Runtime state dan rate limiting | HA, failover, serta policy retention harus diuji |
| `JWT_SECRET` | Signing session/token | Minimal 32 byte dan wajib berasal dari secret manager |
| `METRICS_TOKEN` | Akses endpoint metrics | Jangan commit nilainya ke repository |
| `KMS_KEY` | Proteksi secret atau material kriptografi | Production harus menggunakan secret-manager/KMS-backed key |
| `SL_ENFORCE_PROVENANCE` | Enforcement image/attestation provenance | Aktifkan hanya jika signed artifact dan approved hash sudah diaudit |

Untuk bootstrap admin, gunakan `BOOTSTRAP_ADMIN_EMAIL` dan `BOOTSTRAP_ADMIN_TOKEN` sebagai secret deployment. Token bootstrap hanya boleh digunakan satu kali dan tidak boleh dikirim melalui chat, issue, atau commit.

## Dokumentasi

| Topik | Dokumentasi |
|---|---|
| API dan endpoint | [`docs/api.md`](docs/api.md) |
| OpenAPI control plane | [`docs/api/openapi-control-plane.yaml`](docs/api/openapi-control-plane.yaml) |
| Arsitektur dan data flow | [`docs/architecture/`](docs/architecture/) |
| Operasional | [`docs/OPERATIONS.md`](docs/OPERATIONS.md) |
| Production readiness | [`docs/operations/production-readiness.md`](docs/operations/production-readiness.md) |
| Webhook security | [`docs/api/webhook-security.md`](docs/api/webhook-security.md) |
| Disaster recovery | [`docs/runbooks/dr-restore.md`](docs/runbooks/dr-restore.md) |
| Pilot deployment | [`docs/pilot/PILOT.md`](docs/pilot/PILOT.md) |

## Evidence dan batas klaim

CI pada branch `main` menjalankan unit/integration tests, Go build, Docker image build, security scans, SBOM, dan E2E security checks. Semua hasil tersebut harus diperlakukan sebagai **repository/CI evidence**.

SentinelLayer belum boleh disebut **Technical GA**, **Commercial GA**, certified, memiliki uptime tertentu, atau bebas insiden/false positive sebelum tersedia deployment production, labelled calibration data, customer pilot, restore/failover drill, independent security review, dan acceptance record yang sesuai.

## Security disclosure

Jangan membuka kerentanan keamanan melalui issue publik. Sertakan detail secukupnya untuk reproduksi secara aman dan gunakan jalur disclosure privat yang disepakati oleh maintainer.

## Kontribusi

Perubahan yang menyentuh gateway, policy, tenant isolation, authentication, secret handling, atau deployment harus disertai test dan dokumentasi yang relevan. Sebelum membuka pull request, jalankan setidaknya build dan test lokal pada bagian yang terdampak.

## Lisensi

MIT © 2026 SentinelLayer.
