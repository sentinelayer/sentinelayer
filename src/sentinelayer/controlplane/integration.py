from src.sentinelayer.controlplane.policy import policy_manager

def get_policy_with_version(policy_id: str, version: int = None):
    return policy_manager.get_policy(policy_id, version)
