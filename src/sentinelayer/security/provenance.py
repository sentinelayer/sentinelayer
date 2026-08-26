import logging
logger = logging.getLogger("sentinelayer.provenance")

class RuntimeProvenance:
    def __init__(self):
        self.verified = True
        logger.info("Provenance disabled for development")

provenance = RuntimeProvenance()
