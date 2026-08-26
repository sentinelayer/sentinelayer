import os
import httpx
import json

class AIProvider:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openai")
        self.api_key = os.getenv("AI_API_KEY")
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")

    async def analyze(self, prompt: str, context: dict) -> str:
        if not self.api_key:
            return "AI_UNAVAILABLE: API key missing"

        if self.provider == "openai":
            return await self._openai_analyze(prompt, context)
        elif self.provider == "anthropic":
            return await self._anthropic_analyze(prompt, context)
        return "AI_UNAVAILABLE: Unknown provider"

    async def _openai_analyze(self, prompt: str, context: dict) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a security analyst."},
                        {"role": "user", "content": f"{prompt}\nContext: {json.dumps(context)}"}
                    ],
                    "max_tokens": 200
                },
                timeout=10.0
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            return f"AI_ERROR: {resp.status_code}"

    async def _anthropic_analyze(self, prompt: str, context: dict) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json={
                    "model": "claude-3-haiku-20240307",
                    "messages": [{"role": "user", "content": f"{prompt}\nContext: {json.dumps(context)}"}],
                    "max_tokens": 200
                },
                timeout=10.0
            )
            if resp.status_code == 200:
                return resp.json()["content"][0]["text"]
            return f"AI_ERROR: {resp.status_code}"
