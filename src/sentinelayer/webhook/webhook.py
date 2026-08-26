import httpx
import json
from datetime import datetime
from typing import Dict, List
import os

class WebhookManager:
    def __init__(self):
        self.webhooks = {}
        self.client = httpx.AsyncClient(timeout=10.0)
    
    def register(self, webhook_id: str, url: str, events: List[str]):
        self.webhooks[webhook_id] = {
            "url": url,
            "events": events,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def dispatch(self, event: str, payload: Dict):
        for webhook_id, config in self.webhooks.items():
            if event in config["events"]:
                await self._send_webhook(config["url"], {
                    "event": event,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": payload,
                    "webhook_id": webhook_id
                })
    
    async def _send_webhook(self, url: str, payload: Dict):
        try:
            resp = await self.client.post(url, json=payload)
            if resp.status_code >= 400:
                pass  # Log failure
        except Exception:
            pass  # Log error

webhook_manager = WebhookManager()
