from src.sentinelayer.decision.replay import replay_engine

def integrate_decision_replay(decision: dict):
    replay_engine.record_decision(decision)
    return replay_engine.replay({"tenant_id": decision.get("tenant_id")})
