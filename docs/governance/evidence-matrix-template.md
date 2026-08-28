# Evidence Matrix Template

Gunakan satu baris untuk setiap requirement. Status **designed**, **implemented**, **tested**, **verified**, dan **production** harus didukung oleh artefak yang berbeda bila diperlukan.

| Requirement ID | Requirement | Status | Environment | Artifact / URL | Test method | Result | Owner | Reviewer | Timestamp | Retention | Follow-up |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GOV-001 | Definition of done and acceptance criteria | designed | repository | `docs/governance/definition-of-done.md` | Document review | pending |  |  |  |  |  |
| SEC-001 | Security scanning and SBOM | tested | CI | GitHub Actions run URL | CI workflow | pending |  |  |  |  |  |
| OPS-001 | PostgreSQL backup integrity | implemented | staging | backup checksum + manifest | `scripts/backup_postgres.sh` | pending |  |  |  |  |  |
| OPS-002 | PostgreSQL restore and measured RTO/RPO | verified | staging | restore log + database checks | `scripts/restore_postgres.sh` | pending |  |  |  |  |  |
| RISK-001 | Risk threshold calibration | verified | pilot | labelled corpus + calibration report | replay corpus | pending |  |  |  |  |  |
| PILOT-001 | Controlled blocking and rollback | verified | pilot | rollout and rollback record | pilot runbook | pending |  |  |  |  |  |
| COMP-001 | Regulatory applicability and retention | verified | production | ROPA/DPIA/DPA review | compliance checklist | pending |  |  |  |  |  |
| EXT-001 | Independent security review | production | external | signed report and remediation closure | pentest | pending |  |  |  |  |  |

## Evidence rules

Evidence must be immutable or access-controlled, must identify the exact commit and environment, and must contain enough context to reproduce the result. A screenshot without timestamp, scope, commit, and test method is not sufficient by itself. Redact secrets and personal data before storing evidence.

## Pilot measurement fields

Record request volume, attack corpus version, policy version, rule version, detection rate, block rate, false-positive samples, false-negative samples, p50/p95/p99 latency overhead, availability, error rate, dashboard usability score, audit evidence completeness, and rollback success. Do not publish a target as an achieved result until the measurement is complete and reviewed.
