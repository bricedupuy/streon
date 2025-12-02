#!/bin/bash
# System health check script

set -euo pipefail

API_BASE="http://localhost:8000/api/v1"

echo "========================================="
echo "Streon System Health Check"
echo "========================================="
echo ""

# Check controller service
echo "1. Controller Service:"
if systemctl is-active --quiet streon-controller; then
    echo "   ✓ streon-controller: RUNNING"
else
    echo "   ✗ streon-controller: STOPPED"
fi

# Check Inferno services (if configured)
echo ""
echo "2. Inferno AoIP Services:"
if systemctl is-active --quiet statime; then
    echo "   ✓ statime: RUNNING"
else
    echo "   ✗ statime: STOPPED or NOT CONFIGURED"
fi

if systemctl is-active --quiet inferno; then
    echo "   ✓ inferno: RUNNING"
else
    echo "   ✗ inferno: STOPPED or NOT CONFIGURED"
fi

# Check active Flows
echo ""
echo "3. Active Flows:"
FLOWS=$(systemctl list-units --type=service --state=running 'liquidsoap@*' --no-legend | awk '{print $1}')

if [ -z "$FLOWS" ]; then
    echo "   No active Flows"
else
    for flow in $FLOWS; do
        FLOW_ID=$(echo "$flow" | sed 's/liquidsoap@\(.*\)\.service/\1/')
        echo "   ✓ Flow: ${FLOW_ID}"

        # Check FFmpeg encoder
        if systemctl is-active --quiet "ffmpeg-srt-encoder@${FLOW_ID}"; then
            echo "     ✓ FFmpeg encoder: RUNNING"
        else
            echo "     ✗ FFmpeg encoder: STOPPED"
        fi
    done
fi

# Check API health
echo ""
echo "4. API Health:"
HEALTH_CHECK=$(curl -s "${API_BASE}/system/health" || echo "ERROR")

if [ "$HEALTH_CHECK" != "ERROR" ]; then
    echo "$HEALTH_CHECK" | jq '.'
else
    echo "   ✗ API unreachable"
fi

echo ""
echo "========================================="
echo "Health Check Complete"
echo "========================================="
