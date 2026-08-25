# ============ URUTAN MIDDLEWARE YANG BENER ============
# 1. WAF (semua request)
# 2. Auth (biar user_id & tenant_id kebaca)
# 3. Rate Limit (pake user_id & tenant_id)
# 4. Tenant (validasi tenant)

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    public_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json", "/metrics", "/api/v1/auth/login"]
    
    if TESTING:
        if request.url.path not in public_paths:
            await waf_middleware(request)
        response = await call_next(request)
        return response
    
    if request.url.path not in public_paths:
        await waf_middleware(request)       # 1. WAF
        await auth_middleware(request)       # 2. AUTH (user_id & tenant_id tersedia)
        await rate_limit_middleware(request) # 3. RATE LIMIT (bisa baca user_id)
        await tenant_middleware(request)     # 4. TENANT
    
    response = await call_next(request)
    return response

# ============ ENGINE INTEGRATION ============
from sentinelayer.risk.engine import get_risk_engine
from sentinelayer.behavior.baseline import get_baseline_manager
from sentinelayer.decision.safety import get_decision_safety
from sentinelayer.threatintel.engine import get_threat_intel
from sentinelayer.ai.llm import get_llm_layer
from sentinelayer.evidence.gate import get_gate_engine
from sentinelayer.evidence.matrix import get_evidence_matrix
from sentinelayer.security.key_rotation import get_key_rotation

# Init engines (sekali, global)
risk_engine = get_risk_engine()
behavior_engine = get_baseline_manager()
decision_safety = get_decision_safety()
threat_intel = get_threat_intel()
llm_layer = get_llm_layer()
gate_engine = get_gate_engine()
evidence_matrix = get_evidence_matrix()
key_rotation = get_key_rotation()

# ============ ENGINE ENDPOINTS ============
@app.get("/api/v1/risk/calculate")
async def risk_calculate(current_user: dict = Depends(get_current_user)):
    result = risk_engine.calculate_risk()
    return result

@app.post("/api/v1/risk/signal")
async def risk_signal(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    risk_engine.add_signal(data.get("name", "unknown"), data.get("score", 0.5))
    return {"status": "added"}

@app.get("/api/v1/behavior/stats")
async def behavior_stats(current_user: dict = Depends(get_current_user)):
    return behavior_engine.get_stats()

@app.get("/api/v1/decision/stats")
async def decision_stats(current_user: dict = Depends(get_current_user)):
    return decision_safety.get_stats()

@app.post("/api/v1/decision/killswitch")
async def toggle_killswitch(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    if data.get("action") == "activate":
        decision_safety.activate_kill_switch(data.get("reason", "Manual"))
        return {"status": "activated"}
    decision_safety.deactivate_kill_switch()
    return {"status": "deactivated"}

@app.get("/api/v1/threatintel/ip/{ip}")
async def threat_ip(ip: str, current_user: dict = Depends(get_current_user)):
    result = threat_intel.check_ip(ip)
    return {"ip": ip, "score": result.score, "is_malicious": result.is_malicious}

@app.post("/api/v1/ai/analyze")
async def ai_analyze(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    analysis = llm_layer.analyze_request(data.get("request", {}), data.get("risk", {}))
    return {"summary": analysis.summary, "recommendations": analysis.recommendations}

@app.get("/api/v1/gate/check/{requirement_id}")
async def gate_check(requirement_id: str, current_user: dict = Depends(get_current_user)):
    result = gate_engine.check_requirement(requirement_id, "EV-001")
    return gate_engine.get_status(requirement_id)

@app.get("/api/v1/evidence/list")
async def evidence_list(current_user: dict = Depends(get_current_user)):
    return {"evidence": [e.__dict__ for e in evidence_matrix.list_evidence()]}

@app.get("/api/v1/keys/status")
async def keys_status(current_user: dict = Depends(get_current_user)):
    return key_rotation.get_stats()

@app.post("/api/v1/keys/rotate")
async def keys_rotate(current_user: dict = Depends(get_current_user)):
    key_rotation.rotate_key(key_rotation.current_key_id, current_user.get("sub", "system"))
    return {"status": "rotated", "new_key": key_rotation.current_key_id}
