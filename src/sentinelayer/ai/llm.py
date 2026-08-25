import time
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class LLMAnalysis:
    request_id: str
    summary: str
    risk_level: str
    recommendations: List[str]
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class LLMLayer:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "mock")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.analysis_history: List[LLMAnalysis] = []
    
    def analyze_request(self, request_data: Dict[str, Any], risk_result: Dict[str, Any]) -> LLMAnalysis:
        risk_score = risk_result.get("score", 0)
        risk_level = risk_result.get("level", "low")
        signals = risk_result.get("signals", [])
        
        if risk_level == "critical" or risk_score > 85:
            summary = "High-risk request detected. Multiple security signals triggered."
            recommendations = ["Block this request", "Review WAF rules", "Check IP reputation"]
        elif risk_level == "high":
            summary = "Suspicious request with elevated risk indicators."
            recommendations = ["Monitor this pattern", "Review behavior baseline"]
        else:
            summary = "Normal request with no significant risk."
            recommendations = ["Allow request", "Continue monitoring"]
        
        analysis = LLMAnalysis(
            request_id=request_data.get("request_id", "unknown"),
            summary=summary,
            risk_level=risk_level,
            recommendations=recommendations,
            confidence=min(0.9, max(0.5, 1 - risk_score * 0.01)),
            details={"risk_score": risk_score, "signal_count": len(signals)}
        )
        self.analysis_history.append(analysis)
        return analysis

_llm_layer = None

def get_llm_layer():
    global _llm_layer
    if _llm_layer is None:
        _llm_layer = LLMLayer()
    return _llm_layer
