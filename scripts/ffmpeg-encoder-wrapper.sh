#!/bin/bash
# FFmpeg SRT Encoder Wrapper Script
# Reads Flow configuration and launches FFmpeg encoder(s)

set -euo pipefail

FLOW_ID="$1"
CONFIG_FILE="/etc/streon/flows/${FLOW_ID}.yaml"
FFMPEG_BIN="/opt/streon/ffmpeg/bin/ffmpeg"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Flow config not found: $CONFIG_FILE"
    exit 1
fi

# Parse Flow config using Python
FLOW_CONFIG=$(python3 -c "
import yaml
import sys

with open('${CONFIG_FILE}', 'r') as f:
    config = yaml.safe_load(f)

# Extract SRT outputs
srt_outputs = config.get('outputs', {}).get('srt', [])

if not srt_outputs:
    print('NO_SRT_OUTPUTS')
    sys.exit(0)

# For now, handle the first SRT output
# In future versions, we'll launch multiple FFmpeg instances for multiple outputs
srt = srt_outputs[0]

mode = srt.get('mode', 'caller')
host = srt.get('host', 'localhost')
port = srt.get('port', 9000)
latency_ms = srt.get('latency_ms', 200)
passphrase = srt.get('passphrase', '')
codec = srt.get('codec', 'opus')
bitrate_kbps = srt.get('bitrate_kbps', 128)
container = srt.get('container', 'matroska')

print(f'{mode}|{host}|{port}|{latency_ms}|{passphrase}|{codec}|{bitrate_kbps}|{container}')
")

if [ "$FLOW_CONFIG" == "NO_SRT_OUTPUTS" ]; then
    echo "INFO: No SRT outputs configured for Flow ${FLOW_ID}, exiting"
    sleep infinity  # Keep service running but idle
    exit 0
fi

# Parse the config output
IFS='|' read -r MODE HOST PORT LATENCY PASSPHRASE CODEC BITRATE CONTAINER <<< "$FLOW_CONFIG"

# Build SRT URL
if [ -n "$PASSPHRASE" ]; then
    SRT_URL="srt://${HOST}:${PORT}?mode=${MODE}&latency=${LATENCY}000&passphrase=${PASSPHRASE}"
else
    SRT_URL="srt://${HOST}:${PORT}?mode=${MODE}&latency=${LATENCY}000"
fi

# Build FFmpeg command based on codec and container
FIFO_INPUT="/tmp/streon_${FLOW_ID}_srt0.fifo"

# Wait for FIFO to be created by Liquidsoap
echo "Waiting for FIFO: ${FIFO_INPUT}"
while [ ! -p "$FIFO_INPUT" ]; do
    sleep 1
done

echo "Starting FFmpeg SRT encoder for Flow ${FLOW_ID}"
echo "  Codec: ${CODEC}"
echo "  Bitrate: ${BITRATE} kbps"
echo "  Container: ${CONTAINER}"
echo "  SRT URL: ${SRT_URL}"

case "$CODEC" in
    opus)
        exec $FFMPEG_BIN \
            -f wav -i "$FIFO_INPUT" \
            -c:a libopus -b:a "${BITRATE}k" -application audio -vbr on \
            -f "$CONTAINER" \
            -map 0:a \
            -metadata flow_id="${FLOW_ID}" \
            "$SRT_URL"
        ;;
    aac)
        exec $FFMPEG_BIN \
            -f wav -i "$FIFO_INPUT" \
            -c:a aac -b:a "${BITRATE}k" -profile:a aac_low \
            -f "$CONTAINER" \
            -map 0:a \
            -metadata flow_id="${FLOW_ID}" \
            "$SRT_URL"
        ;;
    pcm)
        exec $FFMPEG_BIN \
            -f wav -i "$FIFO_INPUT" \
            -c:a pcm_s16le \
            -f "$CONTAINER" \
            -map 0:a \
            -metadata flow_id="${FLOW_ID}" \
            "$SRT_URL"
        ;;
    *)
        echo "ERROR: Unknown codec: ${CODEC}"
        exit 1
        ;;
esac
