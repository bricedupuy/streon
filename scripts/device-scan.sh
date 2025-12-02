#!/bin/bash
# Helper script to scan audio devices via API

set -euo pipefail

API_BASE="http://localhost:8000/api/v1"

echo "Scanning audio devices..."
curl -X GET "${API_BASE}/devices/scan" | jq '.'

echo ""
echo "Listing all devices:"
curl -X GET "${API_BASE}/devices" | jq '.'
