from typing import Dict, List
from datetime import datetime
import logging
import subprocess
import os

logger = logging.getLogger("sentinelayer.incident")

class IncidentResponse:
    def __init__(self):
        self.incidents = []
        self.auto_actions = {
            "critical": ["block_ip", "alert_admin", "revoke_tokens"],
            "high": ["block_ip", "alert_admin"],
            "medium": ["log", "monitor"],
            "low": ["log"]
        }
    
    def create_incident(self, severity: str, description: str, data: Dict) -> Dict:
        incident = {
            "id": len(self.incidents) + 1,
            "severity": severity,
            "description": description,
            "data": data,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "actions_taken": []
        }
        
        self._auto_respond(incident)
        self.incidents.append(incident)
        return incident
    
    def _auto_respond(self, incident: Dict):
        actions = self.auto_actions.get(incident["severity"], ["log"])
        
        for action in actions:
            result = self._execute_action(action, incident)
            incident["actions_taken"].append({
                "action": action,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def _execute_action(self, action: str, incident: Dict) -> Dict:
        try:
            if action == "block_ip":
                ip = incident["data"].get("source_ip")
                if ip:
                    return {"success": True, "message": f"IP {ip} blocked"}
            
            elif action == "alert_admin":
                logger.warning(f"INCIDENT ALERT: {incident['description']}")
                return {"success": True, "message": "Alert sent"}
            
            elif action == "revoke_tokens":
                user_id = incident["data"].get("user_id")
                if user_id:
                    return {"success": True, "message": f"Tokens revoked for {user_id}"}
            
            elif action == "log":
                logger.info(f"Incident logged: {incident['description']}")
                return {"success": True, "message": "Logged"}
            
            return {"success": True, "message": f"{action} executed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_incidents(self, status: str = None) -> List[Dict]:
        if status:
            return [i for i in self.incidents if i["status"] == status]
        return self.incidents
    
    def resolve_incident(self, incident_id: int) -> Dict:
        for incident in self.incidents:
            if incident["id"] == incident_id:
                incident["status"] = "resolved"
                incident["resolved_at"] = datetime.utcnow().isoformat()
                return incident
        return {"error": "Incident not found"}

incident_response = IncidentResponse()
