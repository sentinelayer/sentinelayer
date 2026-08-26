import os
import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import base64

class KeyHierarchy:
    def __init__(self):
        self.keys = {}
        self.rotation_days = 30
        self.load_keys()
    
    def load_keys(self):
        # Master key from env
        master_key = os.getenv("MASTER_KEY")
        if master_key:
            self.keys["master"] = master_key.encode()
        
        # Generate derived keys if not exist
        if "app" not in self.keys:
            self.generate_app_key()
    
    def generate_app_key(self):
        app_key = Fernet.generate_key()
        self.keys["app"] = app_key
    
    def rotate_keys(self) -> Dict:
        result = {}
        
        # Generate new keys
        for key_type in ["app", "session", "encryption"]:
            old_key = self.keys.get(key_type)
            new_key = Fernet.generate_key()
            
            if old_key:
                result[f"{key_type}_old"] = base64.b64encode(old_key).decode()
            
            self.keys[key_type] = new_key
            result[f"{key_type}_new"] = base64.b64encode(new_key).decode()
        
        result["rotated_at"] = datetime.utcnow().isoformat()
        return result
    
    def get_key(self, key_type: str) -> bytes:
        return self.keys.get(key_type)
    
    def encrypt(self, data: str, key_type: str = "app") -> str:
        key = self.get_key(key_type)
        if not key:
            raise ValueError(f"Key {key_type} not found")
        
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted: str, key_type: str = "app") -> str:
        key = self.get_key(key_type)
        if not key:
            raise ValueError(f"Key {key_type} not found")
        
        f = Fernet(key)
        return f.decrypt(encrypted.encode()).decode()

key_hierarchy = KeyHierarchy()
