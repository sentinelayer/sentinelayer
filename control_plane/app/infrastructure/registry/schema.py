import json
import hashlib
from datetime import datetime
from typing import Dict, Optional

class SchemaRegistry:
    def __init__(self):
        self.schemas = {}

    def register(self, schema_id: str, version: str, schema: Dict) -> Dict:
        key = f"{schema_id}:{version}"
        schema_hash = hashlib.sha256(json.dumps(schema, sort_keys=True).encode()).hexdigest()
        self.schemas[key] = {
            "schema_id": schema_id,
            "version": version,
            "schema": schema,
            "hash": schema_hash,
            "registered_at": datetime.utcnow().isoformat()
        }
        return self.schemas[key]

    def get(self, schema_id: str, version: str) -> Optional[Dict]:
        key = f"{schema_id}:{version}"
        return self.schemas.get(key)

    def list_versions(self, schema_id: str) -> list:
        return [k.split(":")[1] for k in self.schemas.keys() if k.startswith(f"{schema_id}:")]
