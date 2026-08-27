from control_plane.app.domain.policy.signing import PolicySigning


def test_policy_signature_verifies_and_rejects_tampering(monkeypatch):
    monkeypatch.setenv("SL_ENV", "test")
    monkeypatch.setenv("KMS_KEY", "test-kms-key-for-policy-signing")
    monkeypatch.setenv("POLICY_SIGNING_KEY_ID", "test-key-v1")
    signer = PolicySigning()
    policy = {"policy_id": "p1", "tenant_id": "t1", "version": 1, "rules": {"mode": "block"}}
    signature = signer.sign(policy)
    assert signer.verify(policy, signature) is True
    tampered = {**policy, "rules": {"mode": "allow"}}
    assert signer.verify(tampered, signature) is False
    assert signer.key_id == "test-key-v1"


def test_policy_signature_is_stable_for_same_config(monkeypatch):
    monkeypatch.setenv("SL_ENV", "test")
    monkeypatch.setenv("KMS_KEY", "stable-test-kms-key")
    first = PolicySigning()
    second = PolicySigning()
    policy = {"policy_id": "p1", "tenant_id": "t1", "version": 1, "rules": {"mode": "monitor"}}
    assert first.sign(policy) == second.sign(policy)
    assert first.get_public_key() == second.get_public_key()
