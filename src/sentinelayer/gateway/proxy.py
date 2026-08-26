import httpx
from fastapi import Request, Response
import os

class DataPlane:
    def __init__(self):
        self.upstream_url = os.getenv("UPSTREAM_URL", "http://localhost:8001")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def proxy_request(self, request: Request, path: str):
        url = f"{self.upstream_url}{path}"
        headers = dict(request.headers)
        body = await request.body()
        resp = await self.client.request(method=request.method, url=url, headers=headers, content=body, params=request.query_params)
        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

data_plane = DataPlane()
