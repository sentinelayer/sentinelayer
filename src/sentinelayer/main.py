import signal
import sys
import logging

logger = logging.getLogger(__name__)

def graceful_shutdown(signum, frame):
    logger.info("Received shutdown signal. Cleaning up...")
    # Close database connections
    # Flush logs
    # Finish pending requests
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)
