# SentinelLayer Progress

## Current Status: Phase 0 complete (except retainer) + Data Plane pipeline wired

Honest status. No overclaims.

### Phase 0 (0% → 2%) — Done (Real)
- [x] GateEngine rewritten to full machine-enforced model (Section 0.8)
- [x] Evidence entity expanded to first-class object (Section 0.5)
- [x] Evidence lifecycle with version-binding + auto-expire (Section 0.6)
- [x] Definition of Done formal schema documented
- [x] Independent Verification (Solo Adaptation) procedure documented
- [x] External Retainer contract terms documented (PENDING signature)
- [x] P0 Requirement ID master list created (12 items)
- [x] GateEngine wired into control-plane API (/gates)
- [x] Evidence API updated to full model + lifecycle endpoints
- [x] DB models expanded (Evidence + Requirement)
- [x] Tables created in PostgreSQL
- [x] 12 P0 requirements seeded (all NOT_STARTED)
- [ ] External Retainer contract signed (BLOCKER for independent_reviewer_valid)

### Data Plane (Section 5.2 / 10) — In progress, real code
- [x] Coraza WAF real engine (not regex stub) with CRS include path
- [x] Fail-Open / Fail-Closed matrix implemented exactly as Section 10.23 (capability × endpoint class)
- [x] Full request pipeline in gateway: desync → SSRF → auth context → WAF → rate limit → risk×confidence → decision safety → upstream
- [x] Application Context contract fields propagated (Section 11.22)
- [x] Runtime provenance gate at startup when SL_ENFORCE_PROVENANCE=1 (Section 5.12)
- [x] Decision headers propagated to upstream; Prometheus blocked/allowed counters
- [ ] Behavior Engine full baseline + sequence (still lightweight in-process)
- [ ] Risk Engine HTTP call-out to Python engine (currently in-process scoring)
- [ ] Tenant isolation adversarial matrix tests passing against live API
- [ ] Real CI (Semgrep, Gitleaks, Trivy) green on every commit
- [ ] Any P0 requirement in ACCEPTED state

### Next concrete work
1. Wire gateway → Python Risk Engine over HTTP with circuit breaker + LKG
2. Implement real BOLA/IDOR + tenant isolation tests against control_plane
3. Sign External Retainer so independent_reviewer_valid can flip
4. Canary deploy path (Section 28) for policy changes
