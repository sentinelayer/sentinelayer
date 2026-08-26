#!/bin/bash
pip install cyclonedx-bom
cyclonedx-bom -o sbom.json -f json
echo "SBOM generated: sbom.json"
