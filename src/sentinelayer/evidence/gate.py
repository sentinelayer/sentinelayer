import os
import json
import subprocess
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class GateCheck:
    name: str
    passed: bool
    reason: str = ""
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)

class GateEngine:
    def __init__(self):
        self.checks: List[GateCheck] = []
        self.gate_results: Dict[str, bool] = {}
        self.test_dir = "tests"
    
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
        
        for check in checks:
            print(f"  {check.name}: {'PASS' if check.passed else 'FAIL'} - {check.reason}")
        
        return all_passed
    
    def check_implementation(self, requirement_id: str) -> GateCheck:
        impl_map = {
            "SL-SEC-AUTH-001": "src/sentinelayer/backend/internal/auth/jwt_handler.py",
            "SL-SEC-BOLA-001": "src/sentinelayer/backend/internal/auth/authorization.py",
            "SL-SEC-ISO-001": "src/sentinelayer/database/models/order.py",
            "SL-SEC-RATE-001": "src/sentinelayer/gateway/ratelimit/sliding_window.py",
            "SL-SEC-WAF-001": "src/sentinelayer/gateway/waf/coraza_wrapper.py",
            "SL-SEC-API-001": "src/sentinelayer/api/main_full.py",
        }
        
        filepath = impl_map.get(requirement_id)
        if not filepath:
            return GateCheck(name="Implementation", passed=False, reason=f"No mapping for {requirement_id}")
        
        if not os.path.exists(filepath):
            return GateCheck(name="Implementation", passed=False, reason=f"File not found: {filepath}")
        
        try:
            with open(filepath, "r") as f:
                content = f.read()
                if len(content) < 100:
                    return GateCheck(name="Implementation", passed=False, reason=f"File too small: {len(content)} bytes")
                
                if "def " not in content and "class " not in content:
                    return GateCheck(name="Implementation", passed=False, reason="No functions or classes found")
                
                return GateCheck(name="Implementation", passed=True, reason=f"Implementation found ({len(content)} bytes)")
        except Exception as e:
            return GateCheck(name="Implementation", passed=False, reason=f"Error reading file: {e}")
    
    def check_test(self, requirement_id: str) -> GateCheck:
        test_files = []
        for root, dirs, files in os.walk("tests"):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    test_files.append(os.path.join(root, file))
        
        if not test_files:
            return GateCheck(name="Automated Test", passed=False, reason="No test files found")
        
        try:
            result = __import__("subprocess").run(
                ["pytest", "-q", "--tb=no", "tests/"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if "FAILED" in result.stdout or "ERROR" in result.stdout:
                return GateCheck(name="Automated Test", passed=False, reason="Some tests failed")
            
            return GateCheck(name="Automated Test", passed=True, reason="All tests passed")
        except subprocess.TimeoutExpired:
            return GateCheck(name="Automated Test", passed=False, reason="Test timeout")
        except Exception as e:
            return GateCheck(name="Automated Test", passed=False, reason=f"Test error: {e}")
    
    def check_security(self, requirement_id: str) -> GateCheck:
        security_tests = ["tests/unit/waf/test_waf.py", "tests/unit/auth/test_bola.py"]
        found = [f for f in security_tests if os.path.exists(f)]
        
        if not found:
            return GateCheck(name="Security Test", passed=False, reason="No security tests found")
        
        try:
            result = __import__("subprocess").run(
                ["pytest", "-q", "--tb=no"] + found,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if "FAILED" in result.stdout:
                return GateCheck(name="Security Test", passed=False, reason="Security tests failed")
            
            return GateCheck(name="Security Test", passed=True, reason=f"{len(found)} security test files passed")
        except Exception as e:
            return GateCheck(name="Security Test", passed=False, reason=f"Security test error: {e}")
    
    def check_evidence(self, evidence_id: str) -> GateCheck:
        evidence_file = f"private/evidence/requirements/{evidence_id}.json"
        
        if not os.path.exists(evidence_file):
            return GateCheck(name="Evidence", passed=False, reason=f"Evidence not found: {evidence_file}")
        
        try:
            with open(evidence_file, "r") as f:
                data = json.load(f)
                status = data.get("status", "UNKNOWN")
                if status in ["VALID", "TESTED", "VERIFIED"]:
                    return GateCheck(name="Evidence", passed=True, reason=f"Status: {status}")
                else:
                    return GateCheck(name="Evidence", passed=False, reason=f"Invalid status: {status}")
        except Exception as e:
            return GateCheck(name="Evidence", passed=False, reason=f"Evidence error: {e}")
    
    def check_reviewer(self, evidence_id: str) -> GateCheck:
        evidence_file = f"private/evidence/requirements/{evidence_id}.json"
        
        if not os.path.exists(evidence_file):
            return GateCheck(name="Reviewer", passed=False, reason="Evidence not found")
        
        try:
            with open(evidence_file, "r") as f:
                data = json.load(f)
                reviewer = data.get("reviewer", "PENDING")
                if reviewer and reviewer != "PENDING":
                    return GateCheck(name="Reviewer", passed=True, reason=f"Reviewed by: {reviewer}")
                else:
                    return GateCheck(name="Reviewer", passed=False, reason="Reviewer pending")
        except Exception as e:
            return GateCheck(name="Reviewer", passed=False, reason=f"Reviewer error: {e}")
    
    def check_dependencies(self, requirement_id: str) -> GateCheck:
        required_packages = ["fastapi", "uvicorn", "sqlalchemy", "redis", "jwt", "pytest", "cryptography"]
        missing = []
        
        for pkg in required_packages:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        
        if missing:
            return GateCheck(name="Dependencies", passed=False, reason=f"Missing: {', '.join(missing)}")
        
        return GateCheck(name="Dependencies", passed=True, reason="All packages installed")
    
    def check_rollback(self, requirement_id: str) -> GateCheck:
        rollback_map = {
            "SL-SEC-AUTH-001": "Rollback to previous JWT version",
            "SL-SEC-BOLA-001": "Disable BOLA check",
            "SL-SEC-RATE-001": "Use in-memory rate limiter",
            "SL-SEC-WAF-001": "Disable WAF rules",
            "SL-SEC-API-001": "Rollback to previous API version",
        }
        
        strategy = rollback_map.get(requirement_id)
        if strategy:
            return GateCheck(name="Rollback", passed=True, reason=strategy)
        
        return GateCheck(name="Rollback", passed=False, reason=f"No strategy for {requirement_id}")
    
    def get_status(self, requirement_id: str) -> Dict[str, Any]:
        if requirement_id in self.gate_results:
            passed = self.gate_results[requirement_id]
            return {
                "requirement_id": requirement_id,
                "passed": passed,
                "status": "ACCEPTED" if passed else "REJECTED",
                "timestamp": time.time()
            }
        return {
            "requirement_id": requirement_id,
            "passed": False,
            "status": "NOT_RUN",
            "timestamp": time.time()
        }

def get_gate_engine() -> GateEngine:
    return GateEngine()
_gate_engine = None

def get_gate_engine():
    global _gate_engine
    if _gate_engine is None:
        _gate_engine = GateEngine()
    return _gate_engine
