import os

class LLMLayer:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "mock")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        # WARNING: Default is "mock" - NOT production LLM
    
    def analyze(self, risk_score: float, context: dict) -> str:
        if self.provider == "mock":
            return "⚠️ MOCK ANALYSIS - Not actual LLM. Set LLM_PROVIDER=openai for production."
        # TODO: Implement actual LLM calls
        return "LLM analysis placeholder"
