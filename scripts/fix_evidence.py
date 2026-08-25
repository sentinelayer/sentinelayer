import json
import os
from datetime import datetime

EVIDENCE_DIR = "private/evidence/requirements"

for filename in os.listdir(EVIDENCE_DIR):
    if not filename.endswith(".json"):
        continue
    filepath = os.path.join(EVIDENCE_DIR, filename)
    
    with open(filepath, "r") as f:
        data = json.load(f)
    
    if "evidence_id" not in data:
        data["evidence_id"] = filename.replace(".json", "")
    if "requirement_id" not in data:
        data["requirement_id"] = data.get("evidence_id", "SL-SEC-UNKNOWN")
    if "control_id" not in data:
        data["control_id"] = data.get("requirement_id", "CTRL-UNKNOWN")
    if "artifact" not in data:
        data["artifact"] = "unknown"
    if "timestamp" not in data:
        data["timestamp"] = datetime.now().timestamp()
    if "hash" not in data:
        data["hash"] = "pending"
    if "owner" not in data:
        data["owner"] = "founder"
    if "reviewer" not in data:
        data["reviewer"] = "PENDING"
    if "retention" not in data:
        data["retention"] = 365
    if "validity" not in data:
        data["validity"] = 90
    if "chain_of_custody" not in data:
        data["chain_of_custody"] = []
    if "implementation_version" not in data:
        data["implementation_version"] = "0.1.0"
    if "status" not in data:
        data["status"] = "CREATED"
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Fixed: {filename}")

print("All evidence files fixed")
