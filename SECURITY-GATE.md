# SentinelLayer Security Gate

Dokumen ini mendefinisikan kondisi penerimaan SentinelLayer. **CI green bukan bukti bahwa production sudah diterima.** Setiap criterion harus memiliki implementation evidence, test evidence, runtime evidence, dan reviewer acceptance yang dapat ditelusuri.

## Acceptance criteria

| Criterion | Repository/CI status | Production acceptance |
|---|---|---|
| Coverage P0/P1 minimal 95% | Sebagian besar control path memiliki test, namun blueprint 0–41 masih memiliki gap terbuka | Pending evidence matrix lengkap |
| Residual-risk acceptance | API/model dan audit path tersedia | Pending approval record dari owner dan reviewer independen |
| Independent verifier | Belum ada review eksternal yang terlampir | Blocking |
| Configuration drift = 0 | Manifest/provenance checks tersedia | Pending signed runtime artifact evidence |
| Runtime provenance | Generator dan verifier ada; Docker build lulus | Pending signed image/attestation admission pada environment target |
| Failure matrix | WAF/risk/Redis/behavior policy diuji sebagian | Pending live outage/chaos evidence |
| Backup/DR/HA | Runbook dan local test tersedia | Pending real restore drill, RTO/RPO, failover |

## Evidence lifecycle

Evidence mengikuti lifecycle `CREATED → VERIFIED → VALID → SUPERSEDED/EXPIRED/REVOKED`. Record harus menyimpan implementation version, hash, actor/reviewer, timestamp, chain of custody, dan retention policy. Nilai pada repository atau CI tidak boleh dipresentasikan sebagai bukti deployment runtime bila belum diambil dari environment target.

## Decision safety layers

L1 adalah mitigasi cepat melalui WAF/rate limit dan harus memiliki rollback. L2 adalah perubahan policy melalui signed version, approval, blast-radius control, dan observability. L3 adalah emergency bypass yang memerlukan alasan, expiry, dual control, dan audit trail. Capability yang belum memiliki handler nyata tetap berstatus unavailable, bukan sekadar approved workflow.

## Current verdict

**Repository status: hardened and CI-validated for the tested scope.**

**Technical GA: pending.** Production deployment, signed runtime attestation, external secret/KMS lifecycle, HA/failover, restore drill, load/chaos, alert routing, labelled calibration data, and independent review have not all been proven.

**Commercial GA and pilot: not accepted.** Customer pilot, legal/compliance completion, measured false-positive/false-negative results, SLA evidence, support process, and customer outcome records are still required.

Jangan gunakan label “tanpa celah”, “10/10”, “100% uptime”, “zero incidents”, “zero false positive”, “certified”, atau “Commercial GA” berdasarkan dokumen ini saja.
