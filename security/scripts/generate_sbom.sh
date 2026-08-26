#!/bin/bash
echo "Generating SBOM..."
pip install cyclonedx-bom
cyclonedx-bom -o security/sbom/sbom.json -f json
echo "SBOM generated at security/sbom/sbom.json"
