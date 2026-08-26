from typing import Dict, List
from datetime import datetime, timedelta

class DataClassifier:
    CLASSIFICATIONS = {
        "public": {"level": 1, "retention_days": 30},
        "internal": {"level": 2, "retention_days": 90},
        "confidential": {"level": 3, "retention_days": 365},
        "restricted": {"level": 4, "retention_days": 730}
    }
    
    def classify(self, data: Dict) -> str:
        score = 0
        
        if data.get("email"):
            score += 1
        if data.get("phone"):
            score += 1
        if data.get("address"):
            score += 1
        if data.get("payment") or data.get("credit_card"):
            score += 2
        if data.get("ssn") or data.get("id_number"):
            score += 2
        
        if score >= 4:
            return "restricted"
        elif score >= 3:
            return "confidential"
        elif score >= 1:
            return "internal"
        else:
            return "public"
    
    def get_retention_days(self, classification: str) -> int:
        return self.CLASSIFICATIONS.get(classification, {}).get("retention_days", 30)
    
    def should_retain(self, created_at: datetime, classification: str) -> bool:
        days = self.get_retention_days(classification)
        return (datetime.utcnow() - created_at).days < days

classifier = DataClassifier()
