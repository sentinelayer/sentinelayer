import subprocess
import json
import sys

def generate_sbom():
    try:
        result = subprocess.run(
            ["pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Failed to get pip list")
            sys.exit(1)
        
        packages = json.loads(result.stdout)
        
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "components": []
        }
        
        for pkg in packages:
            sbom["components"].append({
                "type": "library",
                "name": pkg.get("name", ""),
                "version": pkg.get("version", ""),
                "purl": f"pypi/{pkg.get('name', '')}@{pkg.get('version', '')}"
            })
        
        with open("sbom.json", "w") as f:
            json.dump(sbom, f, indent=2)
        
        print("SBOM generated at sbom.json")
        
    except Exception as e:
        print(f"Error generating SBOM: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_sbom()
