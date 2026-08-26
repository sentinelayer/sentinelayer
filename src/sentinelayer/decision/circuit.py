from datetime import datetime, timedelta
from typing import Dict
import logging

logger = logging.getLogger("sentinelayer.circuit")

class CircuitBreaker:
    def __init__(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.failure_threshold = 5
        self.timeout_seconds = 60
        self.last_failure_time = None
        self.half_open_successes = 0
        self.half_open_threshold = 2
    
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout_seconds):
                self._transition_to("HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._handle_success()
            return result
        except Exception as e:
            self._handle_failure()
            raise e
    
    def _handle_success(self):
        if self.state == "HALF_OPEN":
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_threshold:
                self._transition_to("CLOSED")
        self.failure_count = 0
    
    def _handle_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == "HALF_OPEN":
            self._transition_to("OPEN")
        elif self.failure_count >= self.failure_threshold:
            self._transition_to("OPEN")
    
    def _transition_to(self, new_state: str):
        logger.info(f"Circuit breaker transition: {self.state} -> {new_state}")
        self.state = new_state
        if new_state == "CLOSED":
            self.failure_count = 0
            self.half_open_successes = 0

circuit_breaker = CircuitBreaker()
