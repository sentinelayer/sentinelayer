from datetime import datetime


class IncidentLifecycle:
    def __init__(self):
        self.incidents = {}

    def create(self, incident_id: str, severity: str, description: str) -> dict:
        self.incidents[incident_id] = {
            "severity": severity,
            "description": description,
            "status": "open",
            "created_at": datetime.utcnow().isoformat()
        }
        return self.incidents[incident_id]

    def resolve(self, incident_id: str) -> dict:
        if incident_id in self.incidents:
            self.incidents[incident_id]["status"] = "resolved"
            self.incidents[incident_id]["resolved_at"] = datetime.utcnow().isoformat()
            return self.incidents[incident_id]
        return {"error": "Incident not found"}

    def escalate(self, incident_id: str) -> dict:
        if incident_id in self.incidents:
            self.incidents[incident_id]["severity"] = "critical"
            return self.incidents[incident_id]
        return {"error": "Incident not found"}
