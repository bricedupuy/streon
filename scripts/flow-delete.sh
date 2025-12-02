#!/bin/bash
# Helper script to delete a Flow via API

set -euo pipefail

API_BASE="http://localhost:8000/api/v1"
FLOW_ID="${1:-}"

if [ -z "$FLOW_ID" ]; then
    echo "Usage: $0 <flow_id>"
    echo "Example: $0 main_flow"
    exit 1
fi

echo "Stopping Flow services..."
sudo systemctl stop "liquidsoap@${FLOW_ID}" || true
sudo systemctl stop "ffmpeg-srt-encoder@${FLOW_ID}" || true
sudo systemctl stop "ffmpeg-srt-decoder@${FLOW_ID}" || true

echo "Deleting Flow: ${FLOW_ID}"
curl -X DELETE "${API_BASE}/flows/${FLOW_ID}" | jq '.'

echo ""
echo "Flow deleted successfully!"
