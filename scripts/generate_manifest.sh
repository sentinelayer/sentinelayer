#!/bin/bash
echo '{"artifacts": {}}' > private/manifest.json
for file in $(find src -name "*.py"); do
    hash=$(sha256sum $file | cut -d' ' -f1)
    echo "{\"artifacts\": {\"$file\": {\"hash\": \"$hash\", \"verified\": true}}}" > private/manifest.json.tmp
    jq -s '.[0] * .[1]' private/manifest.json private/manifest.json.tmp > private/manifest.json.tmp2
    mv private/manifest.json.tmp2 private/manifest.json
done
rm -f private/manifest.json.tmp
echo "Manifest generated with $(jq '.artifacts | length' private/manifest.json) artifacts"
