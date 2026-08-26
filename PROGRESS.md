# SentinelLayer Progress

## Status: data-plane + risk HTTP + blast radius + isolation tests

Honest. No overclaims.

### Done
- GateEngine / Evidence / Phase 0 (retainer still unsigned)
- Gateway full pipeline + Coraza + fail matrix 10.23 + provenance gate
- Risk Engine HTTP (`engine/risk/server.py`) + Go client + circuit breaker + LKG
- Blast Radius Section 28
- BOLA + tenant matrix tests (need control plane up)

### Run
```bash
PYTHONPATH=. python -m engine.risk.server
# other terminal:
export RISK_ENGINE_URL=http://127.0.0.1:8090
cd gateway && go run ./cmd/gateway
cd /workspaces/sentinelayer/sentinelayer

cat > PROGRESS.md << 'EOF'
# SentinelLayer Progress

## Status: data-plane + risk HTTP + blast radius + isolation tests

Honest. No overclaims.

### Done
- GateEngine / Evidence / Phase 0 (retainer still unsigned)
- Gateway full pipeline + Coraza + fail matrix 10.23 + provenance gate
- Risk Engine HTTP (engine/risk/server.py) + Go client + circuit breaker + LKG
- Blast Radius Section 28
- BOLA + tenant matrix tests (need control plane up)

### Run
PYTHONPATH=. python -m engine.risk.server
export RISK_ENGINE_URL=http://127.0.0.1:8090
cd gateway && go run ./cmd/gateway

### Not done
- External Retainer signed
- Behavior Engine full baseline
- CI green every commit
- Any P0 ACCEPTED
