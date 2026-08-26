VERSION = "0.1.0"

def get_version():
    return VERSION

def get_component_version(component: str) -> str:
    versions = {
        "gateway": "0.1.0",
        "control-plane": "0.1.0",
        "engine": "0.1.0",
        "dashboard": "0.1.0"
    }
    return versions.get(component, "unknown")
