import time
import threading
import logging
from src.sentinelayer.evidence.matrix import get_evidence_matrix

logger = logging.getLogger(__name__)

def enforce_retention():
    matrix = get_evidence_matrix()
    expired = []
    for evidence in matrix.list_evidence():
        age = time.time() - evidence.timestamp
        if age > evidence.retention * 86400:
            expired.append(evidence.evidence_id)
            evidence.status = "EXPIRED"
            matrix.save_evidence(evidence)
    if expired:
        logger.info(f"Evidence expired: {expired}")
    return expired

def start_retention_enforcer(interval_hours=24):
    def loop():
        while True:
            time.sleep(interval_hours * 3600)
            enforce_retention()
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    logger.info(f"Retention enforcer started (interval: {interval_hours}h)")
