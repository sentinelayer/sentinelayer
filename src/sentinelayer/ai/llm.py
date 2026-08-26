import os
import httpx
from typing import Dict, Optional
import json
import logging

logger = logging.getLogger("sentinelayer.ai")

class LLMLayer:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "mock")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    
    async def analyze(self, risk_score: float, context: Dict) -> str:
        if self.provider == "mock":
            return self._mock_analysis(risk_score, context)
        
        if self.provider == "openai":
            return await self._openai_analyze(risk_score, context)
        
        if self.provider == "anthropic":
            return await self._anthropic_analyze(risk_score, context)
        
        return self._mock_analysis(risk_score, context)
    
    def _mock_analysis(self, risk_score: float, context: Dict) -> str:
        if risk_score >= 80:
            return "CRITICAL: High risk detected. Action: BLOCK. Reason: Risk score exceeds threshold."
        elif risk_score >= 60:
            return "HIGH: Elevated risk detected. Action: CHALLENGE. Reason: Suspicious pattern identified."
        elif risk_score >= 30:
            return "MEDIUM: Moderate risk detected. Action: MONITOR. Reason: Unusual behavior observed."
        else:
            return "LOW: Normal activity. Action: ALLOW. No action needed."
    
    async def _openai_analyze(self, risk_score: float, context: Dict) -> str:
        if not self.api_key:
            return self._mock_analysis(risk_score, context)
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a security analyst. Analyze this risk context and provide action recommendation."},
                            {"role": "user", "content": f"Risk score: {risk_score}, Context: {json.dumps(context)}"}
                        ],
                        "max_tokens": 200,
                        "temperature": 0.3
                    },
                    timeout=10.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                return self._mock_analysis(risk_score, context)
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return self._mock_analysis(risk_score, context)
    
    async def _anthropic_analyze(self, risk_score: float, context: Dict) -> str:
        if not self.api_key:
            return self._mock_analysis(risk_score, context)
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "messages": [{"role": "user", "content": f"Risk score: {risk_score}, Context: {json.dumps(context)}"}],
                        "max_tokens": 200,
                        "temperature": 0.3
                    },
                    timeout=10.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["content"][0]["text"]
                return self._mock_analysis(risk_score, context)
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            return self._mock_analysis(risk_score, context)

llm_layer = LLMLayer()
