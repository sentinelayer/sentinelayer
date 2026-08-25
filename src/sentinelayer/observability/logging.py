"""
Structured logging untuk SentinelLayer
JSON format untuk log aggregation
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import Request

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter untuk structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'tenant_id'):
            log_entry["tenant_id"] = record.tenant_id
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'duration'):
            log_entry["duration_ms"] = record.duration
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def setup_logging():
    """Setup structured logging"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

def get_logger(name: str, request: Optional[Request] = None):
    """Get logger with context"""
    logger = logging.getLogger(name)
    
    # Add request context if available
    if request:
        logger.tenant_id = getattr(request.state, 'tenant_id', None)
        logger.user_id = getattr(request.state, 'user_id', None)
        logger.request_id = getattr(request.headers.get('X-Request-ID'), None)
    
    return logger

# FastAPI middleware for request logging
async def logging_middleware(request: Request, call_next):
    """Log all requests with structured JSON"""
    logger = get_logger('sentinelayer.api', request)
    
    # Log request
    logger.info({
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "query": str(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get('user-agent')
    })
    
    start_time = datetime.utcnow()
    try:
        response = await call_next(request)
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Log response
        logger.info({
            "event": "response",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration
        })
        
        return response
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error({
            "event": "error",
            "method": request.method,
            "path": request.url.path,
            "error": str(e),
            "duration_ms": duration
        })
        raise
