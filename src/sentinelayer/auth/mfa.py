import pyotp
import qrcode
import io
import base64
import os
from datetime import datetime
from src.sentinelayer.database import SessionLocal
from src.sentinelayer.database.models import User, MFA

class MFAManager:
    def __init__(self):
        self.db = SessionLocal()
        self.issuer = os.getenv("MFA_ISSUER", "SentinelLayer")

    def setup_mfa(self, user_id: str):
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            return {"error": "User not found"}
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name=self.issuer)
        qr = qrcode.make(provisioning_uri)
        buffered = io.BytesIO()
        qr.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        mfa = MFA(user_id=user_id, secret=secret, enabled=False, created_at=datetime.utcnow())
        self.db.add(mfa)
        self.db.commit()
        return {"secret": secret, "qr_code": qr_base64, "provisioning_uri": provisioning_uri}

    def verify_mfa(self, user_id: str, code: str) -> bool:
        mfa = self.db.query(MFA).filter_by(user_id=user_id).first()
        if not mfa or not mfa.enabled:
            return False
        return pyotp.TOTP(mfa.secret).verify(code)

    def enable_mfa(self, user_id: str, code: str) -> bool:
        if not self.verify_mfa(user_id, code):
            return False
        mfa = self.db.query(MFA).filter_by(user_id=user_id).first()
        if mfa:
            mfa.enabled = True
            self.db.commit()
            return True
        return False

    def disable_mfa(self, user_id: str) -> bool:
        mfa = self.db.query(MFA).filter_by(user_id=user_id).first()
        if mfa:
            mfa.enabled = False
            self.db.commit()
            return True
        return False

mfa_manager = MFAManager()
