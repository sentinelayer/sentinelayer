import json
import time
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
    """LLM layer for advanced security analysis"""
    
    def __init__(self):
        self.model_type = "mock"  # Mock LLM (can replace with OpenAI/Anthropic)
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.analysis_history: List[LLMAnalysis] = []
    
    def analyze_request(self, request_data: Dict[str, Any], risk_result: Dict[str, Any]) -> LLMAnalysis:
        """Analyze request and provide recommendations"""
        
        # Mock analysis (replace with actual LLM call)
        risk_score = risk_result.get("score", 0)
        risk_level = risk_result.get("level", "low")
        signals = risk_result.get("signals", [])
        
        if risk_level == "critical" or risk_score > 0.8:
            summary = "High-risk request detected. Multiple security signals triggered."
            recommendations = [
                "Block this request immediately",
                "Review WAF rules for similar patterns",
                "Check if this IP is in threat intelligence database",
                "Consider rate limiting this source"
            ]
        elif risk_level == "high":
            summary = "Suspicious request with elevated risk indicators."
            recommendations = [
                "Monitor this request pattern",
                "Review user behavior baseline",
                "Check for potential attack patterns",
                "Consider CAPTCHA challenge"
            ]
        elif risk_level == "medium":
            summary = "Moderate risk request with some anomalies."
            recommendations = [
                "Log for further analysis",
                "Review if this is expected behavior",
                "Update baseline if this is normal"
            ]
        else:
            summary = "Normal request with no significant risk indicators."
            recommendations = [
                "Allow request",
                "Continue monitoring",
                "Update baseline with this request"
            ]
        
        # Add signal-specific recommendations
        for signal in signals:
            if signal.get("name") == "waf_block" and signal.get("score", 0) > 0.5:
                recommendations.append(f"WAF rule triggered: {signal.get('source', 'unknown')}")
            if signal.get("name") == "anomaly_detection" and signal.get("score", 0) > 0.5:
                recommendations.append("Behavior anomaly detected - review user patterns")
        
        analysis = LLMAnalysis(
            request_id=request_data.get("request_id", "unknown"),
            summary=summary,
            risk_level=risk_level,
            recommendations=recommendations[:5],  # Limit to 5
            confidence=min(0.9, max(0.5, 1 - risk_score * 0.5)),
            details={
                "risk_score": risk_score,
                "signal_count": len(signals),
                "request": {
                    "method": request_data.get("method", ""),
                    "endpoint": request_data.get("endpoint", ""),
                    "user_id": request_data.get("user_id", ""),
                    "tenant_id": request_data.get("tenant_id", "")
                }
            }
        )
        
        self.analysis_history.append(analysis)
        if len(self.analysis_history) > 100:
            self.analysis_history.pop(0)
        
        return analysis
    
    def get_analysis(self, request_id: str) -> Optional[LLMAnalysis]:
        """Get analysis by request ID"""
        for analysis in self.analysis_history:
            if analysis.request_id == request_id:
                return analysis
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_analyses": len(self.analysis_history),
            "recent_analyses": [
                {
                    "request_id": a.request_id,
                    "risk_level": a.risk_level,
                    "confidence": a.confidence,
                    "timestamp": a.timestamp
                }
                for a in self.analysis_history[-5:]
            ]
        }

def get_llm_layer() -> LLMLayer:
    return LLMLayer()
