# GPIO SRT Quick Reference

Quick configuration examples for common GPIO scenarios.

## Scenario Matrix

| Input | GPIO Source | Output | GPIO Destination | Configuration |
|-------|-------------|--------|------------------|---------------|
| SRT | Embedded | USB/ALSA | TCP | [Config 1](#config-1-srt-gpio--usb--tcp-gpio) |
| SRT | Embedded | Dante | TCP | [Config 2](#config-2-srt-gpio--dante--tcp-gpio) |
| Dante | TCP | SRT | Embedded | [Config 3](#config-3-dante--tcp-gpio--srt-gpio) |
| SRT | Embedded | SRT | Embedded | [Config 4](#config-4-srt-relay-with-gpio-passthrough) |
| ALSA | TCP | SRT | Embedded | [Config 5](#config-5-alsa--tcp-gpio--srt-gpio) |

---

## Config 1: SRT (GPIO) → USB + TCP GPIO

**Use Case**: Receive SRT stream with GPIO, play audio, forward GPIO to automation

```json
{
  "id": "srt_to_usb",
  "inputs": [{
    "type": "srt",
    "srt_url": "srt://0.0.0.0:9000?mode=listener",
    "priority": 1,
    "gpio_extract": true,
    "gpio_output_tcp_host": "192.168.1.100",
    "gpio_output_tcp_port": 7001
  }],
  "processing": {"stereotool": {"enabled": false}},
  "outputs": {
    "alsa": [{"device": "hw:1,0"}],
    "srt": []
  }
}
```

---

## Config 2: SRT (GPIO) → Dante + TCP GPIO

**Use Case**: Receive SRT, output to Dante network, forward GPIO

```json
{
  "id": "srt_to_dante",
  "inputs": [{
    "type": "srt",
    "srt_url": "srt://source:9000?mode=caller",
    "priority": 1,
    "gpio_extract": true,
    "gpio_output_tcp_host": "automation.local",
    "gpio_output_tcp_port": 7001
  }],
  "processing": {"stereotool": {"enabled": false}},
  "outputs": {
    "alsa": [{
      "device": "hw:InfernoTx0",
      "gpio_output_tcp_host": "automation.local",
      "gpio_output_tcp_port": 7001
    }],
    "srt": []
  }
}
```

---

## Config 3: Dante + TCP GPIO → SRT (GPIO)

**Use Case**: Capture Dante, receive GPIO, send as SRT with embedded GPIO

```json
{
  "id": "dante_to_srt",
  "inputs": [{
    "type": "inferno",
    "device": "hw:InfernoStream0",
    "priority": 1
  }],
  "processing": {"stereotool": {"enabled": false}},
  "outputs": {
    "srt": [{
      "mode": "caller",
      "host": "receiver.example.com",
      "port": 9000,
      "codec": "opus",
      "bitrate_kbps": 128,
      "container": "matroska",
      "gpio_embed": true,
      "gpio_input_tcp_port": 7002
    }],
    "alsa": []
  }
}
```

**Send GPIO**:
```bash
echo "START:{\"channel\":1}" | nc localhost 7002
```

---

## Config 4: SRT Relay with GPIO Passthrough

**Use Case**: Relay SRT stream, preserve GPIO, add processing

```json
{
  "id": "srt_relay",
  "inputs": [{
    "type": "srt",
    "srt_url": "srt://source:9000?mode=caller",
    "priority": 1,
    "gpio_extract": true,
    "gpio_output_tcp_host": "127.0.0.1",
    "gpio_output_tcp_port": 7003
  }],
  "processing": {
    "stereotool": {
      "enabled": true,
      "preset": "broadcast_preset"
    }
  },
  "outputs": {
    "srt": [{
      "mode": "listener",
      "port": 9001,
      "codec": "opus",
      "container": "matroska",
      "gpio_embed": true,
      "gpio_input_tcp_port": 7003
    }],
    "alsa": []
  }
}
```

GPIO flows through loopback (127.0.0.1:7003) for inspection/modification.

---

## Config 5: ALSA + TCP GPIO → SRT (GPIO)

**Use Case**: Capture local audio, receive GPIO commands, send as SRT

```json
{
  "id": "alsa_to_srt",
  "inputs": [{
    "type": "alsa",
    "device": "hw:1,0",
    "priority": 1
  }],
  "processing": {"stereotool": {"enabled": false}},
  "outputs": {
    "srt": [{
      "mode": "caller",
      "host": "remote-server.com",
      "port": 9000,
      "codec": "opus",
      "bitrate_kbps": 128,
      "container": "matroska",
      "gpio_embed": true,
      "gpio_input_tcp_port": 7004
    }],
    "alsa": []
  }
}
```

---

## GPIO Event Examples

### Send Events (TCP)

```bash
# Simple event
echo "START" | nc localhost 7002

# Event with payload
echo "START:{\"channel\":1,\"source\":\"studio_a\"}" | nc localhost 7002

# Multiple events
(
  echo "START:{\"channel\":1}"
  sleep 10
  echo "FADE:{\"duration_ms\":2000,\"level\":0.5}"
  sleep 5
  echo "STOP"
) | nc localhost 7002
```

### Python Client

```python
import socket
import json

def send_gpio(host, port, event_type, payload=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        if payload:
            msg = f"{event_type}:{json.dumps(payload)}\n"
        else:
            msg = f"{event_type}\n"
        s.sendall(msg.encode())
        return s.recv(1024).decode().strip()  # "OK"

# Usage
send_gpio("localhost", 7002, "START", {"channel": 1})
send_gpio("localhost", 7002, "STOP")
```

---

## Standard Event Types

| Type | Description | Example Payload |
|------|-------------|-----------------|
| `START` | Start playback | `{"channel": 1}` |
| `STOP` | Stop playback | `{}` |
| `SKIP` | Skip current | `{"duration_s": 30}` |
| `FADE` | Fade audio | `{"duration_ms": 2000, "level": 0.5}` |
| `VOLUME` | Set volume | `{"level": 0.75}` |
| `MARKER` | Timing marker | `{"marker_id": "intro_end", "timestamp_ms": 15000}` |
| `METADATA` | Update metadata | `{"artist": "Artist", "title": "Song"}` |

---

## Troubleshooting

### No GPIO in Output

```bash
# Check if GPIO is being embedded
ffprobe "srt://0.0.0.0:9001?mode=listener" 2>&1 | grep Subtitle

# Expected output:
# Stream #0:1: Subtitle: mov_text (default)
```

### GPIO Not Extracted

```bash
# Manually extract GPIO to verify
ffmpeg -i "srt://source:9000?mode=caller" -map 0:s:0 -c:s srt test.srt
cat test.srt

# Expected format:
# 1
# 00:00:10,500 --> 00:00:10,600
# {"type":"START","timestamp_ms":10500,"payload":{}}
```

### Test TCP Connection

```bash
# Listen for GPIO output
nc -l 7001

# Send test GPIO
echo "TEST" | nc localhost 7002
```

---

## API Quick Reference

### Create Flow

```bash
curl -X POST http://localhost:8000/api/v1/flows \
  -H "Content-Type: application/json" \
  -d @flow_config.json
```

### Start/Stop Flow

```bash
curl -X POST http://localhost:8000/api/v1/flows/{flow_id}/start
curl -X POST http://localhost:8000/api/v1/flows/{flow_id}/stop
```

### Check Flow Status

```bash
curl http://localhost:8000/api/v1/flows/{flow_id}/status
```

---

## Performance Notes

- **Overhead**: GPIO adds <1% CPU, <1KB/s bandwidth
- **Latency**: GPIO synchronized with audio (SRT latency applies)
- **Event Rate**: Supports 100+ events/second without issues
- **Storage**: Each GPIO event ~100 bytes in stream

---

## See Also

- [Full GPIO Integration Guide](GPIO_SRT_INTEGRATION.md)
- [Flow Configuration Guide](GETTING_STARTED.md)
- [SRT Configuration](SRT_GUIDE.md)
