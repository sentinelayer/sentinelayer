# SentinelLayer Progress

## Current Status: MVP Scaffolding

### Completed (Scaffolded)
- [x] Repository structure (gateway/, control_plane/, engine/, dashboard/)
- [x] Auth JWT + bcrypt (basic)
- [x] Database models + migration
- [x] Dashboard pages (18 pages, placeholder data)
- [x] API endpoints (auth, tenants, policies, incidents, evidence, metrics, health)
- [x] Gateway (Go) with regex WAF, rate limit, SSRF
- [x] Risk/Behavior/Decision engines (basic in-memory)
- [x] Documentation (architecture, security, compliance, runbooks)

### In Progress
- [ ] WAF Coraza integration (currently regex)
- [ ] Pipeline: Gateway → Engine → Decision
- [ ] Evidence lifecycle (CREATED → VERIFIED → VALID → EXPIRED)
- [ ] Tenant isolation adversarial matrix
- [ ] Runtime provenance
- [ ] CI/CD real (Semgrep, Gitleaks, Trivy)

### Next
- [ ] Integrate Coraza WAF
- [ ] Wire pipeline to engine
- [ ] Real test coverage
- [ ] Production hardening
