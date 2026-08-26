import os
import subprocess
import json
from datetime import datetime
from typing import Dict, List
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import DRPlan, DRTest

class BCPManager:
    def __init__(self):
        self.db = SessionLocal()
        self.rto = int(os.getenv("RTO_SECONDS", "300"))
        self.rpo = int(os.getenv("RPO_SECONDS", "900"))
        self.backup_freq = int(os.getenv("BACKUP_FREQUENCY_HOURS", "24"))

    def create_dr_plan(self, name: str, description: str) -> Dict:
        plan = DRPlan(
            name=name,
            description=description,
            status="ACTIVE",
            rto=self.rto,
            rpo=self.rpo,
            backup_frequency_hours=self.backup_freq,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        self.db.add(plan)
        self.db.commit()
        return {"id": str(plan.id), "name": plan.name}

    def execute_dr_test(self, plan_id: str) -> Dict:
        test = DRTest(
            plan_id=plan_id,
            started_at=datetime.utcnow().isoformat(),
            status="IN_PROGRESS"
        )
        self.db.add(test)
        self.db.commit()

        try:
            result = self._run_dr_test()
            test.status = "COMPLETED"
            test.completed_at = datetime.utcnow().isoformat()
            test.result = json.dumps(result)
            self.db.commit()
            return {"id": str(test.id), "status": test.status, "result": result}
        except Exception as e:
            test.status = "FAILED"
            test.result = json.dumps({"error": str(e)})
            self.db.commit()
            return {"id": str(test.id), "status": "FAILED", "error": str(e)}

    def _run_dr_test(self) -> Dict:
        steps = []
        try:
            subprocess.run(["pg_dump", "--version"], capture_output=True, check=True)
            steps.append({"step": "pg_dump_available", "status": "PASS"})
        except:
            steps.append({"step": "pg_dump_available", "status": "FAIL"})
            return {"success": False, "steps": steps}

        try:
            backup_path = f"backups/dr_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql"
            os.makedirs("backups", exist_ok=True)
            result = subprocess.run([
                "pg_dump",
                "-h", os.getenv("DB_HOST", "localhost"),
                "-U", os.getenv("DB_USER", "postgres"),
                "-d", os.getenv("DB_NAME", "sentinelayer"),
                "-F", "c",
                "-f", backup_path
            ], capture_output=True, check=True)
            steps.append({"step": "backup_creation", "status": "PASS"})
        except:
            steps.append({"step": "backup_creation", "status": "FAIL"})
            return {"success": False, "steps": steps}

        return {"success": True, "steps": steps}

    def get_active_plans(self) -> List[Dict]:
        plans = self.db.query(DRPlan).filter_by(status="ACTIVE").all()
        return [{"id": str(p.id), "name": p.name, "rto": p.rto, "rpo": p.rpo} for p in plans]

bcp = BCPManager()
