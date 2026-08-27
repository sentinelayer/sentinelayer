from __future__ import annotations

import base64
import binascii
import hashlib
import json
import logging
import os
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

log = logging.getLogger(__name__)


class PolicySigning:
    """Ed25519 policy signing with stable, externally configured key material."""

    def __init__(self) -> None:
        configured = os.getenv("POLICY_SIGNING_PRIVATE_KEY", "").strip()
        kms_key = os.getenv("KMS_KEY", "").strip()
        environment = os.getenv("SL_ENV", "development").lower()

        if configured:
            try:
                seed = base64.b64decode(configured, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise RuntimeError("POLICY_SIGNING_PRIVATE_KEY must be base64") from exc
            if len(seed) != 32:
                raise RuntimeError("POLICY_SIGNING_PRIVATE_KEY must encode exactly 32 bytes")
            self.key_id = os.getenv("POLICY_SIGNING_KEY_ID", "policy-configured-v1")
            self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
        elif kms_key:
            seed = hashlib.sha256(("sentinelayer-policy-signing-v1:" + kms_key).encode()).digest()
            self.key_id = os.getenv("POLICY_SIGNING_KEY_ID", "policy-kms-derived-v1")
            self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
        elif environment in {"production", "prod"}:
            raise RuntimeError("POLICY_SIGNING_PRIVATE_KEY or KMS_KEY is required in production")
        else:
            self.key_id = "ephemeral-dev"
            self.private_key = ed25519.Ed25519PrivateKey.generate()
            log.warning("Policy signing key is ephemeral because no configured key exists")

        self.public_key = self.private_key.public_key()
        self.public_keys: dict[str, ed25519.Ed25519PublicKey] = {self.key_id: self.public_key}
        raw_previous = os.getenv("POLICY_SIGNING_PUBLIC_KEYS_JSON", "").strip()
        if raw_previous:
            try:
                previous_keys: dict[str, Any] = json.loads(raw_previous)
            except json.JSONDecodeError as exc:
                raise RuntimeError("POLICY_SIGNING_PUBLIC_KEYS_JSON must be valid JSON") from exc
            if not isinstance(previous_keys, dict):
                raise RuntimeError("POLICY_SIGNING_PUBLIC_KEYS_JSON must be an object")
            for key_id, encoded in previous_keys.items():
                if not isinstance(key_id, str) or not isinstance(encoded, str):
                    raise RuntimeError("policy public key entries must be string-to-string")
                try:
                    public_bytes = base64.b64decode(encoded, validate=True)
                    self.public_keys[key_id] = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
                except (binascii.Error, ValueError) as exc:
                    raise RuntimeError(f"invalid public key for policy key id {key_id}") from exc

    @staticmethod
    def canonical(policy: dict) -> bytes:
        return json.dumps(policy, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

    def sign(self, policy: dict) -> str:
        signature = self.private_key.sign(self.canonical(policy))
        return base64.b64encode(signature).decode("ascii")

    def verify(self, policy: dict, signature: str, key_id: str | None = None) -> bool:
        try:
            sig = base64.b64decode(signature, validate=True)
            verifier = self.public_keys.get(key_id or self.key_id)
            if verifier is None:
                return False
            verifier.verify(sig, self.canonical(policy))
            return True
        except (InvalidSignature, ValueError, binascii.Error, TypeError):
            return False

    def get_public_key(self) -> str:
        return base64.b64encode(self.public_key.public_bytes_raw()).decode("ascii")
