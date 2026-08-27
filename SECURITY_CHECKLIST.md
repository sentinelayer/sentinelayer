# SentinelLayer Security Checklist — 2026-READY (Blueprint 8-15,24-25,32,36,39)

## Done (Blueprint align)
* JWT Authentication (PyJWT, HS256) — 8.2
* BOLA/IDOR Protection (P0 mandatory) — 8.19
* Rate Limiting (Redis sliding window) — 10.10
* Tenant Isolation (query-level + RLS + adversarial matrix) — 9.3, 5.11
* WAF (Coraza + CRS) — 10.8
* Risk Engine + Decision Safety Layer — 12,13
* Key Rotation (24h automatic + overlap) — 5.10, 8.13
* Runtime Provenance Verification (fail-closed) — 5.12
* Audit Logging + Immutable Evidence — 14.9, 14.10
* Backup Manager + DR (PITR) — 23
* Break-glass + JIT Privileged Access — 14.17, 14.16
* Telemetry Integrity (clock skew 5 detik) — 15.14
* Evidence Matrix (Probo/Evidentia) — 36
* Machine-enforced Gate Engine — 0.8
* HA multi-AZ + DNS failover — 22
* Enterprise SSO / SCIM — 32
* KMS full integration with key_rotation — 8.12, 21.9
* Grafana/Loki observability + SLO — 15

## Partial / In Progress (align blueprint 21,26.6)
* WAF Coraza+CRS full rules (tenant rules) — 10.9
* Real HA multi-AZ + DR drill evidence — 26.6
* Full DR Drill evidence + platform compromise drill

## Planned (align blueprint 31,33,39,40,41)
* Commercial GA (pricing, support SLA, compliance pack)
* Enterprise Readiness (SSO/SCIM/DPA) — 32
* Final Security Gate checklist — 39
* 3 Lapis Acceptance Model — 40
* Epistemological Gate + Evidence verification — 41
* Pilot success metrics & legal — 30

## Solo Adaptation Notes
- External Retainer (CSIRT + dual-control async) — 14.15, 14.18
- Founder on-call primary, Retainer only for high-severity
- Evidence: Post-action review 24 jam, log mandatory
- Budget Year 1: $35k-102k (pentest + retainer + SOC2 + DR)

You can’t perform that action at this time.
