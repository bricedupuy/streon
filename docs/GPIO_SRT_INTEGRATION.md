### GPIO SRT Integration Guide

This document explains how to configure GPIO embedding and extraction in Streon Flows, enabling flexible automation control across SRT and Dante/ALSA transports.

## Overview

Streon supports **bidirectional GPIO integration** with audio streams:

- **GPIO Embedding**: Inject GPIO events into SRT output streams (as subtitle tracks)
- **GPIO Extraction**: Extract GPIO events from incoming SRT streams
- **GPIO Routing**: Send/receive GPIO via TCP independently of audio transport

This allows complex broadcast automation scenarios like:
- **SRT → SRT with GPIO passthrough**
- **SRT with GPIO → USB/Dante audio + TCP GPIO output**
- **Dante + TCP GPIO → SRT with embedded GPIO**

## GPIO Data Format

### In SRT Streams (Embedded)

GPIO events are embedded as **SubRip subtitle tracks** in Matroska/MPEG-TS containers:

```srt
1
00:00:10,500 --> 00:00:10,600
{"type":"START","timestamp_ms":10500,"payload":{"channel":1}}

2
00:00:15,200 --> 00:00:15,300
{"type":"STOP","timestamp_ms":15200,"payload":{}}
```

Each GPIO event occupies a 100ms subtitle entry with JSON payload.

### Over TCP (Standalone)

GPIO events use simple text protocol over TCP:

```
START:{"channel":1}\n
STOP\n
SKIP:{"duration_s":30}\n
FADE:{"duration_ms":2000,"level":0.5}\n
```

Format: `TYPE:payload\n` or just `TYPE\n`

## Configuration Model

### Per-Input GPIO Extraction

```python
class FlowInput(BaseModel):
    type: str  # "srt", "alsa", "usb", "inferno", etc.

    # GPIO extraction (per-input)
    gpio_extract: bool = False  # Extract GPIO from this input
    gpio_output_tcp_host: str  # Where to send extracted GPIO
    gpio_output_tcp_port: int
```

### Per-Output GPIO Embedding

```python
class SRTOutput(BaseModel):
    mode: str  # "caller" or "listener"
    host: str
    port: int

    # GPIO embedding (per-output)
    gpio_embed: bool = False  # Embed GPIO in this output
    gpio_input_tcp_port: int  # TCP port to receive GPIO for embedding
```

```python
class ALSAOutput(BaseModel):
    device: str  # "hw:InfernoTx0", "hw:1,0", etc.

    # GPIO routing (per-output)
    gpio_output_tcp_host: str  # Forward GPIO to automation system
    gpio_output_tcp_port: int
```

---

## Usage Scenarios

### Scenario 1: SRT Input (with GPIO) → USB Audio + TCP GPIO

**Use Case**: Receive SRT stream with embedded GPIO, play audio locally, send GPIO to automation.

**Configuration**:

```json
{
  "id": "srt_to_usb",
  "name": "SRT Receiver with GPIO Extraction",
  "inputs": [
    {
      "type": "srt",
      "srt_url": "srt://0.0.0.0:9000?mode=listener&latency=200000",
      "priority": 1,

      "gpio_extract": true,
      "gpio_output_tcp_host": "192.168.1.100",
      "gpio_output_tcp_port": 7001
    }
  ],
  "processing": {
    "stereotool": {
      "enabled": false
    }
  },
  "outputs": {
    "alsa": [
      {
        "device": "hw:1,0",
        "channels": 2,
        "sample_rate": 48000
      }
    ],
    "srt": []
  }
}
```

**Signal Flow**:
```
SRT Input (audio + GPIO subtitle track)
    │
    ├─> Audio → Liquidsoap → ALSA (hw:1,0) → USB Soundcard
    │
    └─> GPIO → Extracted from subtitles → TCP 192.168.1.100:7001
```

---

### Scenario 2: Dante Input + TCP GPIO → SRT Output (with embedded GPIO)

**Use Case**: Capture Dante audio + receive GPIO via TCP, send as SRT stream with embedded GPIO.

**Configuration**:

```json
{
  "id": "dante_to_srt",
  "name": "Dante to SRT with GPIO Embedding",
  "inputs": [
    {
      "type": "inferno",
      "device": "hw:InfernoStream0",
      "channels": 2,
      "sample_rate": 48000,
      "priority": 1
    }
  ],
  "processing": {
    "stereotool": {
      "enabled": false
    }
  },
  "outputs": {
    "srt": [
      {
        "mode": "caller",
        "host": "remote-server.example.com",
        "port": 9000,
        "latency_ms": 200,
        "codec": "opus",
        "bitrate_kbps": 128,
        "container": "matroska",

        "gpio_embed": true,
        "gpio_input_tcp_port": 7002
      }
    ],
    "alsa": []
  }
}
```

**Signal Flow**:
```
Dante/Inferno (hw:InfernoStream0)
    │
    └─> Audio → Liquidsoap → FIFO → FFmpeg Encoder
                                         │
                                         ├─> Audio (Opus)
                                         │
TCP GPIO Input (port 7002) ──────────────┴─> GPIO Subtitle Track
                                         │
                                         └─> SRT Output (Matroska container)
```

**Send GPIO Events**:
```bash
# Send START event
echo "START:{\"channel\":1}" | nc localhost 7002

# Send STOP event
echo "STOP" | nc localhost 7002
```

---

### Scenario 3: SRT (with GPIO) → SRT (with GPIO) Relay

**Use Case**: Relay SRT stream while preserving GPIO, optionally modifying audio processing.

**Configuration**:

```json
{
  "id": "srt_relay",
  "name": "SRT Relay with GPIO Passthrough",
  "inputs": [
    {
      "type": "srt",
      "srt_url": "srt://source-server:9000?mode=caller&latency=200000",
      "priority": 1,

      "gpio_extract": true,
      "gpio_output_tcp_host": "127.0.0.1",
      "gpio_output_tcp_port": 7003
    }
  ],
  "processing": {
    "stereotool": {
      "enabled": true,
      "preset": "broadcast_preset_001"
    }
  },
  "outputs": {
    "srt": [
      {
        "mode": "listener",
        "port": 9001,
        "latency_ms": 200,
        "codec": "opus",
        "bitrate_kbps": 128,
        "container": "matroska",

        "gpio_embed": true,
        "gpio_input_tcp_port": 7003
      }
    ],
    "alsa": []
  }
}
```

**Signal Flow**:
```
SRT Input (source-server:9000)
    │
    ├─> Audio → Liquidsoap → StereoTool → FIFO → FFmpeg Encoder → SRT Output (:9001)
    │                                                                    │
    └─> GPIO Extracted ──> TCP 127.0.0.1:7003 (loopback) ───────────────┘ GPIO Embedded
```

GPIO flows through local TCP loopback, allowing inspection/modification if needed.

---

### Scenario 4: Multiple Inputs with GPIO Routing

**Use Case**: Automatic failover between SRT sources, forward GPIO from active source.

**Configuration**:

```json
{
  "id": "multi_input_gpio",
  "name": "Multi-Input with GPIO Failover",
  "inputs": [
    {
      "type": "srt",
      "srt_url": "srt://primary-server:9000?mode=caller&latency=200000",
      "priority": 1,
      "fallback": false,

      "gpio_extract": true,
      "gpio_output_tcp_host": "192.168.1.50",
      "gpio_output_tcp_port": 7010
    },
    {
      "type": "srt",
      "srt_url": "srt://backup-server:9000?mode=caller&latency=200000",
      "priority": 2,
      "fallback": true,

      "gpio_extract": true,
      "gpio_output_tcp_host": "192.168.1.50",
      "gpio_output_tcp_port": 7010
    }
  ],
  "processing": {
    "stereotool": {
      "enabled": false
    }
  },
  "outputs": {
    "alsa": [
      {
        "device": "hw:InfernoTx0",
        "channels": 2,
        "sample_rate": 48000,

        "gpio_output_tcp_host": "192.168.1.60",
        "gpio_output_tcp_port": 7020
      }
    ],
    "srt": []
  }
}
```

**Signal Flow**:
```
Primary SRT ────┐
                ├─> Liquidsoap Fallback ─> Dante Output (hw:InfernoTx0)
Backup SRT ─────┘                                │
                                                 └─> GPIO to automation (192.168.1.60:7020)

Both inputs send GPIO to same endpoint (192.168.1.50:7010)
```

Liquidsoap automatically switches between inputs based on availability/priority.

---

## GPIO Event Types

### Standard Events

| Event Type | Description | Typical Payload |
|------------|-------------|-----------------|
| `START` | Start playback/transmission | `{"channel": 1}` |
| `STOP` | Stop playback | `{}` |
| `SKIP` | Skip current item | `{"duration_s": 30}` |
| `FADE` | Fade in/out | `{"duration_ms": 2000, "level": 0.5}` |
| `VOLUME` | Change volume | `{"level": 0.75}` |
| `MARKER` | Timing marker | `{"marker_id": "intro_end"}` |
| `METADATA` | Metadata update | `{"artist": "...", "title": "..."}` |

### Custom Events

You can define custom event types for your automation:

```json
{"type": "TRIGGER_LIGHTING", "payload": {"scene": "commercial", "transition_ms": 500}}
{"type": "SWITCH_CAMERA", "payload": {"camera_id": 2, "preset": "wide"}}
{"type": "ALERT", "payload": {"severity": "warning", "message": "Low headroom"}}
```

---

## Implementation Details

### FFmpeg Subtitle Embedding

When `gpio_embed: true`, Streon uses FFmpeg's subtitle track feature:

```bash
ffmpeg \
  -f wav -i audio_input.fifo \
  -i gpio_subtitles.srt \
  -map 0:a \
  -map 1:s:0 \
  -c:a libopus -b:a 128k \
  -c:s mov_text \
  -f matroska \
  "srt://destination:9000?mode=caller&latency=200000"
```

- Audio track: Opus-encoded audio
- Subtitle track: mov_text codec with JSON GPIO events

### FFmpeg Subtitle Extraction

When `gpio_extract: true`, Streon extracts subtitles:

```bash
ffmpeg \
  -i "srt://0.0.0.0:9000?mode=listener&latency=200000" \
  -map 0:a \
  -c:a pcm_s16le \
  -f alsa hw:1,0 \
  -map 0:s:0? \
  -c:s srt \
  /tmp/extracted_gpio.srt
```

Extracted `.srt` file is monitored in real-time, GPIO events are parsed and forwarded to TCP.

---

## Testing GPIO Integration

### 1. Test GPIO Embedding

**Start Flow with GPIO embedding**:
```bash
# Create Flow with SRT output + GPIO embedding
curl -X POST http://localhost:8000/api/v1/flows \
  -H "Content-Type: application/json" \
  -d @flow_config.json

# Start Flow
curl -X POST http://localhost:8000/api/v1/flows/test_flow/start
```

**Send GPIO events**:
```bash
# Send START event
echo "START:{\"channel\":1}" | nc localhost 7002

# Send STOP event after 10 seconds
sleep 10
echo "STOP" | nc localhost 7002
```

**Verify on receiving end**:
```bash
# Receive SRT stream and extract subtitles
ffmpeg -i "srt://0.0.0.0:9001?mode=listener" \
  -map 0:s:0 -c:s srt gpio_received.srt

# Check extracted GPIO
cat gpio_received.srt
```

### 2. Test GPIO Extraction

**Receive SRT with GPIO and forward to TCP**:

```bash
# Start automation listener
nc -l 7001

# Create Flow with SRT input + GPIO extraction
# (use config from Scenario 1)

# GPIO events will appear in the nc listener
```

**Expected output**:
```
START:{"channel":1}
STOP
```

### 3. End-to-End Test

**Setup**:
```
[Sender Flow]
Dante hw:InfernoStream0 + TCP GPIO (port 7002)
    ↓
SRT with embedded GPIO → port 9000

[Receiver Flow]
SRT input (port 9000) with GPIO extraction
    ↓
USB Audio hw:1,0 + TCP GPIO output (port 7001)
```

**Test**:
```bash
# On sender: Send GPIO event
echo "START:{\"test\":true}" | nc localhost 7002

# On receiver: Monitor GPIO output
nc -l 7001
# Should receive: START:{"test":true}
```

---

## Performance Considerations

### Subtitle Track Overhead

- Each GPIO event adds ~100 bytes to the stream
- 10 events/second = ~1KB/s = negligible overhead
- Subtitle tracks do NOT increase audio encoding load

### TCP GPIO Latency

- Local loopback: <1ms
- LAN: 1-5ms
- GPIO forwarding adds minimal latency compared to SRT audio latency (typically 200ms)

### Resource Usage

- GPIO extraction: Minimal CPU (subtitle parsing)
- GPIO embedding: Minimal CPU (JSON serialization)
- Memory: ~1KB per GPIO event (buffered)

---

## Troubleshooting

### GPIO Events Not Embedded

**Symptoms**: SRT output has no subtitle track

**Check**:
1. Verify `gpio_embed: true` in output configuration
2. Check `gpio_input_tcp_port` is specified
3. Ensure TCP GPIO sender is connected: `netstat -an | grep 7002`
4. Check FFmpeg encoder logs: `journalctl -u ffmpeg-srt-encoder@flow_id`

**Solution**:
```bash
# Test TCP connection
echo "TEST" | nc -v localhost 7002
```

### GPIO Events Not Extracted

**Symptoms**: No GPIO events sent to TCP endpoint

**Check**:
1. Verify `gpio_extract: true` in input configuration
2. Check incoming SRT has subtitle track:
   ```bash
   ffprobe "srt://0.0.0.0:9000?mode=listener"
   # Look for Stream #0:1: Subtitle: mov_text
   ```
3. Check extraction script logs
4. Verify TCP endpoint is reachable: `nc -zv 192.168.1.100 7001`

**Solution**:
```bash
# Manually extract subtitles to verify
ffmpeg -i "srt://source:9000" -map 0:s:0 -c:s srt test.srt
cat test.srt
```

### GPIO Events Delayed

**Symptoms**: GPIO arrives seconds after audio

**Cause**: SRT latency buffer (typically 200ms) + processing delay

**Solution**:
- Reduce SRT latency (minimum ~50ms for LAN):
  ```json
  {"latency_ms": 50}
  ```
- GPIO timing is preserved relative to audio timeline
- For real-time GPIO (independent of audio), use separate TCP channel (don't embed)

---

## Best Practices

### 1. Use Embedded GPIO When...

- GPIO must stay synchronized with audio (frame-accurate control)
- Single transport connection is preferred (firewall/NAT friendly)
- Remote sites need GPIO + audio in one stream

### 2. Use Separate TCP GPIO When...

- GPIO must arrive before audio (pre-roll automation)
- GPIO is independent of audio content (manual triggers)
- Multiple systems need same GPIO (multicast scenario)
- Low latency is critical (<10ms)

### 3. Combine Both When...

- Primary control via embedded GPIO (synchronized)
- Override/emergency control via TCP (immediate)
- Monitoring automation events separately from audio

### 4. GPIO Event Design

- Keep payloads small (<256 bytes)
- Use standard event types when possible
- Include timestamps for logging/debugging
- Add sequence numbers for critical events:
  ```json
  {"type":"START","seq":12345,"payload":{...}}
  ```

---

## Future Enhancements

Planned improvements:

- **GPIO Filtering**: Selective forwarding of event types
- **GPIO Transformation**: Map/transform events between systems
- **GPIO Logging**: Persistent GPIO event database
- **GPIO Scheduling**: Time-based GPIO injection
- **Binary GPIO Protocol**: More efficient encoding (Protocol Buffers)

---

## API Examples

### Create Flow with GPIO

```python
import requests

flow_config = {
    "config": {
        "id": "gpio_test",
        "name": "GPIO Test Flow",
        "inputs": [{
            "type": "srt",
            "srt_url": "srt://source:9000?mode=caller",
            "priority": 1,
            "gpio_extract": True,
            "gpio_output_tcp_host": "192.168.1.100",
            "gpio_output_tcp_port": 7001
        }],
        "outputs": {
            "srt": [{
                "mode": "listener",
                "port": 9001,
                "codec": "opus",
                "bitrate_kbps": 128,
                "container": "matroska",
                "gpio_embed": True,
                "gpio_input_tcp_port": 7002
            }],
            "alsa": []
        }
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/flows",
    json=flow_config
)
print(response.json())
```

### Send GPIO Event

```python
import socket

def send_gpio(host, port, event_type, payload=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))

        if payload:
            import json
            message = f"{event_type}:{json.dumps(payload)}\n"
        else:
            message = f"{event_type}\n"

        sock.sendall(message.encode('utf-8'))
        response = sock.recv(1024)  # Wait for "OK\n"
        return response.decode().strip()

# Send START event
send_gpio("localhost", 7002, "START", {"channel": 1})

# Send STOP event
send_gpio("localhost", 7002, "STOP")
```

---

## Summary

Streon's GPIO SRT integration provides flexible broadcast automation:

✅ **Per-input GPIO extraction** - Extract from any SRT input
✅ **Per-output GPIO embedding** - Embed in any SRT output
✅ **Mixed scenarios** - Combine embedded + standalone TCP GPIO
✅ **Standard format** - SubRip subtitles for wide compatibility
✅ **Low overhead** - Minimal CPU/bandwidth impact
✅ **Professional workflows** - Frame-accurate automation control

For additional help, see:
- [Flow Configuration Guide](GETTING_STARTED.md)
- [SRT Configuration](SRT_GUIDE.md)
- [Dante/Inferno Integration](INFERNO_INTEGRATION.md)
