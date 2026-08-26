import uuid
from datetime import datetime, timedelta


class CSIRTSolo:
    def __init__(self):
        self.incidents = {}
        self.external_retainer_email = "retainer@sentinelayer.com"

    def create_incident(self, severity: str, description: str) -> dict:
        incident_id = str(uuid.uuid4())
        self.incidents[incident_id] = {
            "id": incident_id,
            "severity": severity,
            "description": description,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "post_action_review_deadline": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        return self.incidents[incident_id]

    def emergency_action_log(self, incident_id: str, action: str) -> dict:
        incident = self.incidents.get(incident_id)
        if not incident:
            return {"error": "Incident not found"}
        incident["emergency_action"] = action
        incident["emergency_action_at"] = datetime.utcnow().isoformat()
        return incident

    def post_action_review(self, incident_id: str, notes: str) -> dict:
        incident = self.incidents.get(incident_id)
        if not incident:
            return {"error": "Incident not found"}
        incident["post_action_review"] = notes
        incident["post_action_review_at"] = datetime.utcnow().isoformat()
        incident["status"] = "reviewed"
        return incident

    def get_incident(self, incident_id: str) -> dict:
        return self.incidents.get(incident_id, {"error": "Not found"})
