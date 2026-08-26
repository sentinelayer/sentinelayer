import os
import httpx
import json
import logging

logger = logging.getLogger("sentinelayer.ai")

class LLMLayer:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai")
        self.api_key = os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    async def analyze(self, risk_score: float, context: dict) -> str:
        if not self.api_key:
            raise ValueError("LLM_API_KEY is required")
        if self.provider == "openai":
            return await self._openai_analyze(risk_score, context)
        elif self.provider == "anthropic":
            return await self._anthropic_analyze(risk_score, context)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _openai_analyze(self, risk_score: float, context: dict) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a security analyst."},
                        {"role": "user", "content": f"Risk score: {risk_score}, Context: {json.dumps(context)}"}
                    ],
                    "max_tokens": 200
                },
                timeout=10.0
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            raise ValueError(f"OpenAI API error: {resp.status_code}")

    async def _anthropic_analyze(self, risk_score: float, context: dict) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json={
                    "model": "claude-3-haiku-20240307",
                    "messages": [{"role": "user", "content": f"Risk score: {risk_score}, Context: {json.dumps(context)}"}],
                    "max_tokens": 200
                },
                timeout=10.0
            )
            if resp.status_code == 200:
                return resp.json()["content"][0]["text"]
            raise ValueError(f"Anthropic API error: {resp.status_code}")

llm_layer = LLMLayer()
