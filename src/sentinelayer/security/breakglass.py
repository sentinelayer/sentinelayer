import time
import uuid
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class BreakGlassSession:
    session_id: str
    user_id: str
    reason: str
    created_at: float
    expires_at: float
    is_active: bool = True
    actions: list = field(default_factory=list)

class BreakGlassManager:
    def __init__(self):
        self.sessions: Dict[str, BreakGlassSession] = {}
        self.max_duration = 3600
    
    def create_session(self, user_id: str, reason: str) -> BreakGlassSession:
        session_id = str(uuid.uuid4())
        now = time.time()
        
        session = BreakGlassSession(
            session_id=session_id,
            user_id=user_id,
            reason=reason,
            created_at=now,
            expires_at=now + self.max_duration
        )
        
        self.sessions[session_id] = session
        logger.warning(f"Break-glass session created: user={user_id}, reason={reason}")
        return session
    
    def get_session(self, session_id: str) -> Optional[BreakGlassSession]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        if not session.is_active:
            return None
        
        if time.time() > session.expires_at:
            session.is_active = False
            logger.warning(f"Break-glass session expired: {session_id}")
            return None
        
        return session
    
    def revoke_session(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.is_active = False
        logger.warning(f"Break-glass session revoked: {session_id}")
        return True
    
    def log_action(self, session_id: str, action: str) -> bool:
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return False
        
        session.actions.append({
            "action": action,
            "timestamp": time.time()
        })
        return True
    
    def get_active_sessions(self) -> list:
        return [s for s in self.sessions.values() if s.is_active]

_breakglass = None

def get_breakglass_manager():
    global _breakglass
    if _breakglass is None:
        _breakglass = BreakGlassManager()
    return _breakglass
