#!/bin/bash
# Helper script to create a new Flow via API

set -euo pipefail

API_BASE="http://localhost:8000/api/v1"
FLOW_NAME="${1:-}"

if [ -z "$FLOW_NAME" ]; then
    echo "Usage: $0 <flow_name>"
    echo "Example: $0 main_flow"
    exit 1
fi

# Create a basic Flow configuration
FLOW_CONFIG=$(cat <<EOF
{
  "config": {
    "id": "${FLOW_NAME}",
    "name": "${FLOW_NAME}",
    "enabled": true,
    "inputs": [
      {
        "type": "alsa",
        "device": "hw:0",
        "channels": 2,
        "sample_rate": 48000,
        "priority": 1
      }
    ],
    "processing": {
      "stereotool": {
        "enabled": false,
        "preset": ""
      },
      "silence_detection": {
        "threshold_dbfs": -50,
        "duration_s": 5
      },
      "crossfade": {
        "enabled": false,
        "duration_s": 2
      }
    },
    "outputs": {
      "srt": [
        {
          "mode": "caller",
          "host": "localhost",
          "port": 9000,
          "latency_ms": 200,
          "passphrase": "",
          "codec": "opus",
          "bitrate_kbps": 128,
          "container": "matroska"
        }
      ],
      "alsa": []
    },
    "gpio": {
      "tcp_input": {
        "enabled": false,
        "port": 7000
      },
      "http_input": {
        "enabled": false,
        "port": 8080
      },
      "tcp_output": {
        "enabled": false,
        "host": "localhost",
        "port": 7001
      },
      "embed_in_srt": false
    },
    "metadata": {
      "enabled": true,
      "websocket": true,
      "embed_in_srt": false,
      "rest_endpoint": true
    },
    "monitoring": {
      "metering": true,
      "silence_detection": true,
      "srt_stats": true,
      "prometheus": true
    }
  }
}
EOF
)

echo "Creating Flow: ${FLOW_NAME}"
curl -X POST "${API_BASE}/flows" \
    -H "Content-Type: application/json" \
    -d "$FLOW_CONFIG" | jq '.'

echo ""
echo "Flow created successfully!"
echo "Start the Flow with: sudo systemctl start liquidsoap@${FLOW_NAME} ffmpeg-srt-encoder@${FLOW_NAME}"
