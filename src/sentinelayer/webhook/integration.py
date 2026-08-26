from src.sentinelayer.webhook.webhook import webhook_manager

async def dispatch_webhook(event: str, payload: dict):
    await webhook_manager.dispatch(event, payload)
