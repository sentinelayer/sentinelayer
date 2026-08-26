import httpx
from fastapi import Request, Response
import os

class DataPlane:
    def __init__(self):
        self.upstream_url = os.getenv("UPSTREAM_URL", "http://localhost:8001")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def proxy_request(self, request: Request, path: str):
        filtered_headers = {k: v for k, v in request.headers.items() if k not in [
            "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
            "te", "trailer", "transfer-encoding", "upgrade"
        ]}
        body = await request.body()
        resp = await self.client.request(
            method=request.method,
            url=f"{self.upstream_url}{path}",
            headers=filtered_headers,
            content=body,
            params=request.query_params
        )
        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

data_plane = DataPlane()
