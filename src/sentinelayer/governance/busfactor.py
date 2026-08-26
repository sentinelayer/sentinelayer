import json
import os
from datetime import datetime
from typing import Dict, List
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import BusFactorEntry

class BusFactorManager:
    def __init__(self):
        self.db = SessionLocal()
        self.emergency_contacts = os.getenv("EMERGENCY_CONTACTS", "").split(",")
        self.recovery_credentials = os.getenv("RECOVERY_CREDENTIALS", "")

    def get_bus_factor(self) -> Dict:
        return {
            "founder_skills": self._get_founder_skills(),
            "critical_knowledge": self._get_critical_knowledge(),
            "documentation": self._get_documentation_status(),
            "emergency_contacts": self.emergency_contacts
        }

    def _get_founder_skills(self) -> List[Dict]:
        return [
            {"skill": "Backend Engineering", "level": "HIGH"},
            {"skill": "Security Engineering", "level": "HIGH"},
            {"skill": "DevOps", "level": "HIGH"},
            {"skill": "AI/ML", "level": "MEDIUM"},
            {"skill": "Product Management", "level": "HIGH"},
            {"skill": "Sales/Business", "level": "MEDIUM"}
        ]

    def _get_critical_knowledge(self) -> List[Dict]:
        return [
            {"area": "Architecture", "documented": True},
            {"area": "Security Controls", "documented": True},
            {"area": "Deployment", "documented": True},
            {"area": "Customer Configuration", "documented": False},
            {"area": "Key Management", "documented": False}
        ]

    def _get_documentation_status(self) -> Dict:
        return {
            "architecture": True,
            "api": True,
            "deployment": True,
            "security": True,
            "customer_onboarding": False,
            "emergency_procedures": True
        }

    def record_action(self, action: str, context: Dict) -> Dict:
        entry = BusFactorEntry(
            action=action,
            context=json.dumps(context),
            timestamp=datetime.utcnow().isoformat()
        )
        self.db.add(entry)
        self.db.commit()
        return {"id": entry.id, "action": action}

    def get_recovery_instructions(self) -> Dict:
        return {
            "infrastructure_credentials": self.recovery_credentials,
            "emergency_contacts": self.emergency_contacts,
            "recovery_steps": [
                "1. Access recovery credentials from secure storage",
                "2. Contact emergency contacts",
                "3. Follow disaster recovery procedure",
                "4. Verify system integrity after recovery"
            ]
        }

bus_factor = BusFactorManager()
