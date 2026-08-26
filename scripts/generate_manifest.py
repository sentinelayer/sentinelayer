import json
import os
import hashlib

manifest = {"artifacts": {}}
src_dir = "src"

for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "rb") as f:
                hash_value = hashlib.sha256(f.read()).hexdigest()
            manifest["artifacts"][path] = {"hash": hash_value, "verified": True}

os.makedirs("private", exist_ok=True)
with open("private/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Manifest generated with {len(manifest['artifacts'])} artifacts")
