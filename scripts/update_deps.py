import subprocess
import json
import sys

def update_dependencies():
    try:
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Failed to check outdated packages")
            return
        
        outdated = json.loads(result.stdout)
        
        if not outdated:
            print("All packages are up to date")
            return
        
        print(f"Found {len(outdated)} outdated packages:")
        
        for pkg in outdated:
            print(f"  {pkg['name']}: {pkg['version']} -> {pkg['latest_version']}")
        
        response = input("Update all packages? (y/n): ")
        if response.lower() == 'y':
            for pkg in outdated:
                print(f"Updating {pkg['name']}...")
                subprocess.run(["pip", "install", "--upgrade", pkg['name']], capture_output=True)
            print("Done updating")
            subprocess.run(["pip", "freeze", ">", "requirements.txt"], shell=True)
            print("requirements.txt updated")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_dependencies()
