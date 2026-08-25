import json
from sentinelayer.api.main_full import app

def generate_openapi():
    openapi_schema = app.openapi()
    with open("docs/openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("OpenAPI spec generated at docs/openapi.json")

if __name__ == "__main__":
    generate_openapi()
