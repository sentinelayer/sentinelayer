import time
from fastapi import Request
from fastapi.responses import JSONResponse
from src.sentinelayer.gateway.waf.regex_waf import get_waf_engine
from src.sentinelayer.behavior.baseline import get_baseline_manager
from src.sentinelayer.risk.engine import get_risk_engine, RiskSignal
from src.sentinelayer.decision.safety import get_decision_safety

waf = get_waf_engine()
behavior = get_baseline_manager()
decision = get_decision_safety()

async def security_pipeline(request: Request, call_next):
    path = request.url.path
    if path in ["/health", "/docs", "/redoc", "/openapi.json", "/", "/metrics", "/api/v1/auth/login"]:
        return await call_next(request)

    query = str(request.query_params)
    body = ""
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body_bytes = await request.body()
            body = body_bytes.decode('utf-8', errors='ignore')[:10000]
        except:
            pass

    waf_result = waf.inspect_request(path, query, body, dict(request.headers))
    if waf_result["blocked"]:
        return JSONResponse(status_code=403, content={"error": "Blocked by WAF", "violations": waf_result["violations"]})

    user_id = getattr(request.state, "user_id", "unknown")
    tenant_id = getattr(request.state, "tenant_id", "default")

    behavior.record_request({
        "endpoint": path,
        "method": request.method,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "response_time": 0,
        "status_code": 200,
        "request_size": len(body),
        "response_size": 0
    })

    anomaly = behavior.detect_anomaly({
        "endpoint": path,
        "method": request.method,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "response_time": 0,
        "status_code": 200
    })
    
    risk_signals = []
    if anomaly.get("is_anomaly", False):
        risk_signals.append(RiskSignal("anomaly_detection", anomaly.get("score", 0.5) * 100, 1.0, 0.8, "behavior"))

    if waf_result["violations"]:
        risk_signals.append(RiskSignal("waf_block", 80.0, 1.5, 0.9, "waf"))

    risk_engine = get_risk_engine()
    risk_result = risk_engine.calculate_risk(risk_signals)
    
    decision_result = decision.make_decision(
        request_id=request.headers.get("X-Request-ID", "unknown"),
        risk_result=risk_result,
        context={"user": user_id, "tenant": tenant_id, "path": path}
    )

    if decision_result.action == "block":
        return JSONResponse(status_code=403, content={"error": "Request blocked by security policy", "risk_score": risk_result["score"]})

    response = await call_next(request)

    behavior.record_request({
        "endpoint": path,
        "method": request.method,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "response_time": 0,
        "status_code": response.status_code,
        "request_size": len(body),
        "response_size": len(response.body) if hasattr(response, "body") else 0
    })

    return response
