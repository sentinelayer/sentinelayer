import os
import json
import time
import subprocess
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class GateCheck:
    name: str
    passed: bool
    reason: str = ""
    timestamp: float = field(default_factory=time.time)

class GateEngine:
    def __init__(self):
        self.gate_results: Dict[str, bool] = {}
    
    def check_requirement(self, requirement_id: str, evidence_id: str) -> bool:
        checks = [
            self.check_implementation(requirement_id),
            self.check_test(requirement_id),
            self.check_security(requirement_id),
            self.check_evidence(evidence_id),
            self.check_reviewer(evidence_id),
            self.check_dependencies(requirement_id),
            self.check_rollback(requirement_id)
        ]
        all_passed = all(c.passed for c in checks)
        self.gate_results[requirement_id] = all_passed
        return all_passed
    
    def check_implementation(self, requirement_id: str) -> GateCheck:
        impl_map = {
            "SL-SEC-AUTH-001": "src/sentinelayer/backend/internal/auth/jwt_handler.py",
            "SL-SEC-BOLA-001": "src/sentinelayer/backend/internal/auth/authorization.py",
            "SL-SEC-ISO-001": "src/sentinelayer/database/models/order.py",
            "SL-SEC-RATE-001": "src/sentinelayer/gateway/ratelimit/sliding_window.py",
            "SL-SEC-API-001": "src/sentinelayer/api/main_full.py",
        }
        filepath = impl_map.get(requirement_id)
        if not filepath or not os.path.exists(filepath):
            return GateCheck("Implementation", False, f"File not found: {filepath}")
        with open(filepath, "r") as f:
            content = f.read()
            if len(content) < 100:
                return GateCheck("Implementation", False, "File too small")
        return GateCheck("Implementation", True, "File exists")
    
    def check_test(self, requirement_id: str) -> GateCheck:
        test_files = []
        for root, dirs, files in os.walk("tests"):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    test_files.append(os.path.join(root, file))
        if not test_files:
            return GateCheck("Test", False, "No test files")
        return GateCheck("Test", True, f"{len(test_files)} test files")
    
    def check_security(self, requirement_id: str) -> GateCheck:
        found = ["tests/unit/waf/test_waf.py", "tests/unit/auth/test_bola.py"]
        existing = [f for f in found if os.path.exists(f)]
        if not existing:
            return GateCheck("Security", False, "No security tests")
        return GateCheck("Security", True, "Security tests found")
    
    def check_evidence(self, evidence_id: str) -> GateCheck:
        evidence_file = f"private/evidence/requirements/{evidence_id}.json"
        if not os.path.exists(evidence_file):
            return GateCheck("Evidence", False, "Evidence not found")
        with open(evidence_file, "r") as f:
            data = json.load(f)
            status = data.get("status", "UNKNOWN")
            if status in ["VALID", "TESTED", "VERIFIED"]:
                return GateCheck("Evidence", True, f"Status: {status}")
        return GateCheck("Evidence", False, "Invalid evidence")
    
    def check_reviewer(self, evidence_id: str) -> GateCheck:
        evidence_file = f"private/evidence/requirements/{evidence_id}.json"
        if not os.path.exists(evidence_file):
            return GateCheck("Reviewer", False, "Evidence not found")
        with open(evidence_file, "r") as f:
            data = json.load(f)
            reviewer = data.get("reviewer", "PENDING")
            if reviewer and reviewer != "PENDING":
                return GateCheck("Reviewer", True, f"Reviewed by: {reviewer}")
        return GateCheck("Reviewer", False, "Reviewer pending")
    
    def check_dependencies(self, requirement_id: str) -> GateCheck:
        packages = ["fastapi", "uvicorn", "sqlalchemy", "redis", "jwt", "pytest"]
        missing = []
        for pkg in packages:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        if missing:
            return GateCheck("Dependencies", False, f"Missing: {missing}")
        return GateCheck("Dependencies", True, "All packages installed")
    
    def check_rollback(self, requirement_id: str) -> GateCheck:
        rollback_script = f"scripts/rollback/{requirement_id}.sh"
        if os.path.exists(rollback_script):
            return GateCheck("Rollback", True, "Rollback script exists")
        return GateCheck("Rollback", False, "No rollback script")
    
    def get_status(self, requirement_id: str) -> Dict[str, Any]:
        passed = self.gate_results.get(requirement_id, False)
        return {
            "requirement_id": requirement_id,
            "passed": passed,
            "status": "ACCEPTED" if passed else "REJECTED",
            "timestamp": time.time()
        }

def get_gate_engine() -> GateEngine:
    return GateEngine()
