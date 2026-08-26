import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, List
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import Incident

logger = logging.getLogger("sentinelayer.incident")

class IncidentResponse:
    def __init__(self):
        self.db = SessionLocal()
        self.auto_actions = {
            "critical": ["block_ip", "alert_admin"],
            "high": ["block_ip", "alert_admin"],
            "medium": ["log"],
            "low": ["log"]
        }

    def create_incident(self, severity: str, description: str, data: Dict) -> Dict:
        incident = Incident(
            severity=severity,
            description=description,
            status="open",
            created_at=datetime.utcnow()
        )
        self.db.add(incident)
        self.db.commit()

        actions_taken = []
        for action in self.auto_actions.get(severity, ["log"]):
            result = self._execute_action(action, data)
            actions_taken.append({"action": action, "result": result})

        return {
            "id": str(incident.id),
            "severity": severity,
            "description": description,
            "status": "open",
            "actions_taken": actions_taken
        }

    def _execute_action(self, action: str, data: Dict) -> Dict:
        try:
            if action == "block_ip":
                ip = data.get("source_ip")
                if ip:
                    subprocess.run(["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"], check=True)
                    return {"success": True, "message": f"IP {ip} blocked"}
                return {"success": False, "message": "No IP provided"}

            elif action == "alert_admin":
                logger.warning(f"INCIDENT ALERT: {data.get('description', 'No description')}")
                return {"success": True, "message": "Alert sent"}

            elif action == "log":
                logger.info(f"Incident logged: {data.get('description', 'No description')}")
                return {"success": True, "message": "Logged"}

            return {"success": False, "message": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_incidents(self, status: str = None) -> List[Dict]:
        query = self.db.query(Incident)
        if status:
            query = query.filter_by(status=status)
        return [{
            "id": str(i.id),
            "severity": i.severity,
            "description": i.description,
            "status": i.status,
            "created_at": i.created_at.isoformat()
        } for i in query.all()]

    def resolve_incident(self, incident_id: str) -> Dict:
        incident = self.db.query(Incident).filter_by(id=incident_id).first()
        if not incident:
            return {"error": "Incident not found"}
        incident.status = "resolved"
        incident.resolved_at = datetime.utcnow()
        self.db.commit()
        return {"id": str(incident.id), "status": "resolved"}

incident_response = IncidentResponse()
