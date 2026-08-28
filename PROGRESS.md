# SentinelLayer Progress

## Status repository

SentinelLayer sudah memiliki satu alur data plane yang terintegrasi pada repository: Gateway Go melakukan normalisasi request dan body, Coraza memuat OWASP CRS, rate limiting atomic memakai Redis, behavior assessment dan risk scoring dijalankan melalui HTTP internal, decision safety menentukan tindakan, lalu request aman diteruskan ke control plane/upstream. Dashboard disajikan dari control plane pada satu domain dan endpoint API memakai namespace `/api/v1`.

Control plane sekarang mencakup PostgreSQL/Alembic persistence, tenant scoping, JWT sessions, API keys, MFA enforcement untuk privileged actions, RBAC, one-use bootstrap admin grant, versioned policy signatures, high-risk token-revocation capability, audit events, webhook retry/DLQ worker, dan dashboard contract untuk risk decisions.

## Evidence yang tersedia

| Evidence | Status |
|---|---|
| Unit dan integration tests | Lulus pada local/CI untuk scope yang dijalankan |
| Gateway Go build dan tests | Lulus |
| Dashboard TypeScript/Vite build | Lulus |
| Docker image build | Lulus pada GitHub Actions |
| Security, Trivy, SBOM, dan machine-enforced gate workflows | Lulus pada commit yang diuji |
| PostgreSQL/RLS CI matrix | Lulus pada workflow CI yang menjalankan service PostgreSQL |
| Railway deployment dan register/login pada environment user | Belum terverifikasi dari sesi ini |
| Real customer traffic, load, chaos, backup restore, HA/failover | Belum tersedia |
| Labelled calibration data, FP/FN budget, pilot outcome, SLA, independent review | Belum tersedia |

## Gap yang masih blocking acceptance

Status code dan CI green tidak sama dengan Technical GA atau Commercial GA. Masih diperlukan deployment staging/production yang dapat diaudit, signed runtime attestation, secret/KMS lifecycle nyata, Redis/PostgreSQL failover, load dan chaos testing, restore drill dengan RTO/RPO, central observability dan alerting, labelled calibration data, customer pilot, independent security review, serta acceptance record pihak kedua.

Single-service Railway adalah topology awal untuk memulihkan domain dan alur end-to-end. Ia bukan HA deployment. Untuk scale-out, Gateway, control plane, risk engine, behavior engine, dan worker perlu dipisah atau dijalankan dengan process supervision yang setara, sementara shared state, traffic draining, failover, dan policy consistency harus diuji.

## Next engineering priorities

Repository sekarang menyediakan backup PostgreSQL atomik dengan checksum dan opsi enkripsi, restore validation/dry-run dengan konfirmasi eksplisit, job backup manual Docker Compose berprofil, runtime configuration guard, Makefile verification targets, serta operational-readiness CI. Prioritas berikutnya tetap verifikasi Railway setelah deploy `main` terbaru, pengujian request nyata melewati Gateway hingga upstream, shared-state failure matrix, observability redaction/alert routing, serta perbaikan key lifecycle agar policy signing dapat berotasi tanpa memutus verification terhadap versi yang masih berlaku. Fitur yang belum memiliki adapter nyata tidak boleh dipasarkan sebagai implemented.

## Acceptance language

Jangan gunakan label “10/10”, “tanpa celah”, “100% uptime”, “zero incidents”, “zero false positive”, “Technical GA”, “Commercial GA”, certified, atau enterprise-ready sebelum evidence eksternal yang relevan benar-benar tersedia dan direview.

## Audit update — 2026-08-28

Frontend API lifecycle audit selesai pada commit `6cf7114`. Seluruh halaman dashboard yang melakukan fetch dalam `useEffect` kini memakai `AbortController`; polling Live Protection membatalkan request sebelumnya sebelum refresh berikutnya; client error responses hanya menampilkan pesan yang dipetakan dari HTTP status atau safe error code; dan tiga halaman visual lama tidak lagi menggunakan loading mentah atau `any` untuk payload utama.

Cloudflare workflow diubah menjadi manual-only pada commit berikutnya yang akan dicatat bersama perubahan ini, karena Railway tetap menjadi jalur utama dan rollout Cloudflare belum boleh dipicu otomatis.

Bukti lokal terbaru: `npm --prefix dashboard run build` lulus setelah perubahan terakhir; `git diff --check` lulus; Python compile dan shell syntax check dijalankan. Pytest integration yang membutuhkan service pada `localhost:8005` tidak dapat membuktikan runtime karena service belum berjalan di sandbox. Docker Compose validation tidak dapat dijalankan karena binary Docker tidak terpasang di sandbox. Ini dicatat sebagai keterbatasan verifikasi, bukan dianggap lulus.

Railway public networking, domain single-origin, database/Redis managed services, seeder staging, backup restore drill, dan Cloudflare deployment tetap membutuhkan verifikasi eksternal melalui environment pengguna. Repository hanya menyediakan implementasi dan runbook; tidak ada evidence eksternal yang dipalsukan.
