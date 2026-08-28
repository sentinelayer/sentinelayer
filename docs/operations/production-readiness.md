# SentinelLayer Production Readiness Plan

Dokumen ini membedakan **kapabilitas yang dapat diverifikasi dari repository** dengan **evidence yang hanya dapat diperoleh dari environment nyata, customer pilot, atau reviewer independen**. Status tidak boleh dinaikkan hanya karena build atau test lokal berhasil.

## Acceptance matrix

| Domain | Implementasi repository | Evidence yang masih wajib | Owner / frekuensi |
|---|---|---|---|
| Deployment | Dockerfile, Railway config, single-service launcher | Staging deployment, smoke test, rollback record | Founder / setiap release |
| Database | Alembic, tenant scoping, RLS tests | Managed PostgreSQL backup/PITR restore drill | Founder / bulanan |
| Cache/state | Redis-backed rate limit and maintenance lease | Failover, eviction, persistence, and degraded-mode drill | Founder / kuartalan |
| Security | SAST, secret scan, Trivy, SBOM, adversarial tests | Independent penetration test and remediation report | External reviewer / sebelum GA |
| Availability | Health/readiness endpoints and runbooks | Measured RTO/RPO, failover, and availability window | Founder / kuartalan |
| Calibration | Deterministic risk engine and explainability | Labelled corpus, FP/FN budget, threshold approval | Security owner / setiap policy release |
| Pilot | Onboarding and pilot templates | Customer consent, traffic measurement, rollback evidence, outcome | Founder + customer / setiap pilot |
| Compliance | Applicability and UU PDP documents | DPA/ToS approval, data inventory, retention proof | Legal reviewer / setiap perubahan |
| Enterprise | RBAC/MFA/audit/API/webhook primitives | SSO/SCIM/SIEM integration and customer questionnaire | Product/security / sebelum enterprise sale |

## Backup and restore drill

1. Set `DATABASE_URL`, `BACKUP_DIR`, and—when required—`GPG_RECIPIENT` from the deployment secret manager. Never put those values in Git.
2. Run `bash scripts/backup_postgres.sh` and retain the generated dump, checksum, and manifest according to the approved retention policy.
3. Copy the backup to an isolated restore environment. Run `RESTORE_DRY_RUN=1 bash scripts/restore_postgres.sh` and record checksum, `pg_restore --list`, timestamp, and database version.
4. For a destructive drill only, set `RESTORE_CONFIRM=I_UNDERSTAND` and restore into a disposable database. Verify migrations, tenant isolation, login, policy reads, audit reads, and dashboard health.
5. Record measured RTO/RPO, row counts, failed checks, remediation, and sign-off in the evidence repository. A successful backup command alone is not a DR drill.

## Release gate

A release may be called **repository-ready** only when CI, security scans, SBOM generation, test results, and runtime provenance artifacts are green. It may be called **production-ready** only after staging smoke tests, secret-manager validation, backup/restore evidence, alert routing, rollback evidence, and owner approval. It may be called **Technical GA** or **Commercial GA** only after the external evidence in the matrix is complete.

## Explicit non-claims

The system must not claim zero incidents, zero false positives, 100% uptime, certification, HA, independent verification, or enterprise readiness without the corresponding evidence. AI agent execution remains deferred until a separate design review enables it.
