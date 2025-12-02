#!/bin/bash
# FFmpeg SRT Decoder Wrapper Script
# Reads Flow configuration and launches FFmpeg decoder

set -euo pipefail

FLOW_ID="$1"
CONFIG_FILE="/etc/streon/flows/${FLOW_ID}.yaml"
FFMPEG_BIN="/opt/streon/ffmpeg/bin/ffmpeg"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Flow config not found: $CONFIG_FILE"
    exit 1
fi

# Parse Flow config using Python
DECODER_CONFIG=$(python3 -c "
import yaml
import sys

with open('${CONFIG_FILE}', 'r') as f:
    config = yaml.safe_load(f)

# Check if this Flow has an SRT input (decoder mode)
inputs = config.get('inputs', [])
srt_input = next((i for i in inputs if i.get('type') == 'srt'), None)

if not srt_input:
    print('NO_SRT_INPUT')
    sys.exit(0)

mode = srt_input.get('mode', 'listener')
port = srt_input.get('port', 9000)
latency_ms = srt_input.get('latency_ms', 200)
passphrase = srt_input.get('passphrase', '')

# Output device (if specified)
outputs = config.get('outputs', {})
alsa_outputs = outputs.get('alsa', [])
alsa_device = alsa_outputs[0].get('device', 'default') if alsa_outputs else 'default'

print(f'{mode}|{port}|{latency_ms}|{passphrase}|{alsa_device}')
")

if [ "$DECODER_CONFIG" == "NO_SRT_INPUT" ]; then
    echo "INFO: No SRT input configured for Flow ${FLOW_ID}, exiting"
    sleep infinity  # Keep service running but idle
    exit 0
fi

# Parse the config output
IFS='|' read -r MODE PORT LATENCY PASSPHRASE ALSA_DEVICE <<< "$DECODER_CONFIG"

# Build SRT URL
if [ -n "$PASSPHRASE" ]; then
    SRT_URL="srt://0.0.0.0:${PORT}?mode=${MODE}&latency=${LATENCY}000&passphrase=${PASSPHRASE}"
else
    SRT_URL="srt://0.0.0.0:${PORT}?mode=${MODE}&latency=${LATENCY}000"
fi

echo "Starting FFmpeg SRT decoder for Flow ${FLOW_ID}"
echo "  SRT URL: ${SRT_URL}"
echo "  ALSA Output: ${ALSA_DEVICE}"

# Decode SRT stream and output to ALSA
exec $FFMPEG_BIN \
    -i "$SRT_URL" \
    -f alsa "$ALSA_DEVICE"
