import json
import httpx
import os
from typing import Dict, List

class GRCTooling:
    def __init__(self):
        self.probo_url = os.getenv("PROBO_URL", "http://localhost:8080")
        self.unicis_url = os.getenv("UNICIS_URL", "http://localhost:8081")
        self.evidentia_url = os.getenv("EVIDENTIA_URL", "http://localhost:8082")

    async def check_probo(self, framework: str) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.probo_url}/api/v1/frameworks/{framework}")
                if resp.status_code == 200:
                    return {"status": "connected", "framework": framework, "data": resp.json()}
                return {"status": "error", "message": "Probo API error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def check_unicis(self, framework: str) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.unicis_url}/api/v1/frameworks/{framework}")
                if resp.status_code == 200:
                    return {"status": "connected", "framework": framework, "data": resp.json()}
                return {"status": "error", "message": "Unicis API error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def check_evidentia(self, artifact: str) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.evidentia_url}/api/v1/evidence",
                    json={"artifact": artifact}
                )
                if resp.status_code == 200:
                    return {"status": "connected", "artifact": artifact, "data": resp.json()}
                return {"status": "error", "message": "Evidentia API error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def generate_compliance_matrix(self, requirements: List[Dict]) -> Dict:
        matrix = {"soc2": [], "iso27001": [], "gdpr": [], "pci_dss": [], "hipaa": []}
        for req in requirements:
            for framework, controls in req.get("frameworks", {}).items():
                if framework in matrix:
                    matrix[framework].append({
                        "requirement": req.get("id"),
                        "control": controls,
                        "status": req.get("status", "unknown")
                    })
        return matrix

grc = GRCTooling()
