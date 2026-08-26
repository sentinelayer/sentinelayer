from typing import Dict, List

class MITREATLAS:
    def __init__(self):
        self.tactics = {
            "TA0001": {"name": "Reconnaissance", "techniques": ["T1595", "T1592", "T1598"]},
            "TA0002": {"name": "Resource Development", "techniques": ["T1587", "T1588", "T1586"]},
            "TA0003": {"name": "Initial Access", "techniques": ["T1190", "T1133", "T1566"]},
            "TA0004": {"name": "Execution", "techniques": ["T1059", "T1204", "T1505"]},
            "TA0005": {"name": "Persistence", "techniques": ["T1136", "T1078", "T1098"]},
            "TA0006": {"name": "Privilege Escalation", "techniques": ["T1068", "T1055", "T1484"]},
            "TA0007": {"name": "Defense Evasion", "techniques": ["T1070", "T1027", "T1036"]},
            "TA0008": {"name": "Credential Access", "techniques": ["T1110", "T1555", "T1003"]},
            "TA0009": {"name": "Discovery", "techniques": ["T1087", "T1046", "T1069"]},
            "TA0010": {"name": "Collection", "techniques": ["T1119", "T1005", "T1530"]},
            "TA0011": {"name": "Command and Control", "techniques": ["T1071", "T1090", "T1572"]},
            "TA0012": {"name": "Exfiltration", "techniques": ["T1048", "T1567", "T1020"]},
            "TA0013": {"name": "Impact", "techniques": ["T1486", "T1490", "T1485"]},
            "TA0014": {"name": "AI Model Access", "techniques": ["T1600", "T1601", "T1602"]},
            "TA0015": {"name": "AI Data Poisoning", "techniques": ["T1603", "T1604"]},
            "TA0016": {"name": "AI Output Manipulation", "techniques": ["T1605", "T1606"]}
        }

    def get_threats(self, asset_type: str) -> List[Dict]:
        threats = []
        for tactic_id, tactic in self.tactics.items():
            if "AI" in tactic["name"]:
                threats.append({
                    "tactic": tactic["name"],
                    "tactic_id": tactic_id,
                    "techniques": tactic["techniques"],
                    "asset_type": "AI"
                })
            elif asset_type in ["api", "gateway"]:
                threats.append({
                    "tactic": tactic["name"],
                    "tactic_id": tactic_id,
                    "techniques": tactic["techniques"],
                    "asset_type": "API"
                })
        return threats

atlas = MITREATLAS()
