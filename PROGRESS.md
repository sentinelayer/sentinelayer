# SentinelLayer Progress

## Current Status: Phase 0 — Constitution & Governance (wiring complete)

Honest status. No overclaims.

### Phase 0 (0% → 2%) — Real Progress
- [x] GateEngine rewritten to full machine-enforced model (Section 0.8)
- [x] Evidence entity expanded to first-class object (Section 0.5)
- [x] Evidence lifecycle with version-binding + auto-expire (Section 0.6)
- [x] Definition of Done formal schema documented
- [x] Independent Verification (Solo Adaptation) procedure documented
- [x] External Retainer contract terms documented (PENDING signature)
- [x] P0 Requirement ID master list created (12 items)
- [x] GateEngine wired into control-plane API (`/gates`)
- [x] Evidence API updated to full model + lifecycle endpoints
- [x] DB models expanded (Evidence + Requirement)
- [x] Migration 0002 created
- [x] P0 seed script created (`seed_p0.py`)
- [ ] Migration 0002 applied to database
- [ ] P0 requirements seeded into DB
- [ ] First real Evidence objects created for existing P0 items
- [ ] External Retainer contract signed

### Previously Scaffolded (still incomplete)
- Repository structure (gateway/, control_plane/, engine/, dashboard/)
- Auth JWT + bcrypt (basic)
- Database models + migration (partial → now expanded)
- Dashboard pages (many still placeholder data)
- Gateway (Go) — WAF still regex, not full Coraza+CRS production path
- Risk / Behavior / Decision engines (basic in-memory)
- Documentation (architecture, security, compliance, runbooks) — high-level

### Explicitly Not Done Yet
- Coraza + CRS production integration
- Full pipeline Gateway → Behavior → Risk → Decision Safety
- Tenant isolation adversarial matrix tests (real)
- Runtime provenance enforcement at startup
- Real CI (Semgrep, Gitleaks, Trivy) passing on every commit
- Any P0 requirement in ACCEPTED state

### Next (finish Phase 0)
1. Apply migration 0002
2. Run `python -m app.domain.gate.seed_p0`
3. Verify via `GET /gates/requirements?criticality=P0`
4. Contract External Retainer (blocks Independent Reviewer VALID)
