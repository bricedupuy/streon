# Streon

**Professional Multi-Flow Audio Transport System for Radio Broadcasters**

Streon is a Linux-based, modular audio engine designed for professional radio operations. It unifies audio ingest, routing, processing, AoIP, SRT transport, GPIO automation, and real-time monitoring with a complete Web UI.

## Features

- **Multi-Flow Architecture** - Unlimited concurrent, independent audio pipelines
- **Liquidsoap 2.4.0** - Professional audio processing with StereoTool integration
- **SRT Transport** - Opus/AAC/PCM over SRT with configurable bitrate and FEC
- **Dante/AES67** - Professional AoIP integration via Inferno
- **Web UI** - Complete configuration and monitoring interface
- **GPIO Engine** - Per-Flow TCP/HTTP automation control
- **Real-time Metadata** - Song metadata delivery via WebSocket
- **Observability** - Prometheus/Grafana monitoring stack

## Technology Stack

- **Backend:** Python 3.11+ (FastAPI, asyncio, Pydantic)
- **Frontend:** React 18, TypeScript, Vite, shadcn/ui, Tailwind CSS
- **Audio:** Liquidsoap 2.4.0, StereoTool operator
- **Transport:** FFmpeg with libsrt, libopus, libfdk-aac
- **AoIP:** Inferno + statime
- **Platform:** Debian 13 (bare-metal, x64/aarch64)

## Quick Start

### Production Installation (Debian 13)

```bash
# Clone repository
git clone https://github.com/bricedupuy/streon.git
cd streon

# Make installation script executable
chmod +x install/debian-13-install.sh

# Run master installer (interactive)
sudo ./install/debian-13-install.sh
```

The installer will:
1. Install system dependencies
2. Build Liquidsoap 2.4.0 from source
3. Build FFmpeg with SRT support
4. Optionally install Inferno AoIP (Dante/AES67)
5. Set up Python controller with FastAPI
6. Install systemd services
7. Optionally install Prometheus + Grafana
8. Create initial configuration

After installation:

```bash
# Start the controller
sudo systemctl start streon-controller

# Access the Web UI
# Open http://your-server-ip:8000 in your browser

# Create your first Flow
/opt/streon/scripts/flow-create.sh my_first_flow

# Start the Flow
sudo systemctl start liquidsoap@my_first_flow
sudo systemctl start ffmpeg-srt-encoder@my_first_flow

# Check system health
/opt/streon/scripts/health-check.sh
```

### Development Setup

For development without full installation:

```bash
# Backend (Python FastAPI)
cd controller
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (React + TypeScript) - in another terminal
cd web-ui
npm install
npm run dev
```

Access:
- Web UI: [http://localhost:5173](http://localhost:5173)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- API: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)

## Architecture

### Flow Concept

A **Flow** is the primary unit in Streon:

```
Input(s) → Processing → Output(s) → GPIO → Metadata → Transport → Monitoring
```

Each Flow includes:
- **Inputs:** ALSA/USB, Dante/AES67, SRT, NDI, files
- **Processing:** Liquidsoap (fallback, crossfade, silence detection) + StereoTool
- **Outputs:** SRT encode, ALSA/USB/HDMI playback
- **GPIO:** TCP/HTTP automation I/O
- **Metadata:** Real-time song information
- **Monitoring:** Audio levels, SRT stats, silence detection

### Components

- **streon-controller** - Python FastAPI backend (REST API + WebSocket)
- **liquidsoap** - Audio processing engine (per-Flow instance)
- **ffmpeg** - SRT transport encoding/decoding
- **inferno** - Dante/AES67 integration
- **Web UI** - React-based configuration interface
- **Prometheus/Grafana** - Metrics and visualization

## Configuration

### StereoTool Integration

Streon supports StereoTool for broadcast audio processing:

1. Add your StereoTool license key via Web UI (Settings → StereoTool → paste license text)
2. Upload preset files (.sts) via Web UI
3. Assign presets to Flows in Flow configuration

### Flow Management

Create Flows via Web UI or REST API:

```bash
# Via Web UI
# Navigate to Flows → Create Flow

# Via CLI helper script
/opt/streon/scripts/flow-create.sh my_flow

# Via API
curl -X POST http://localhost:8000/api/v1/flows \
  -H "Content-Type: application/json" \
  -d @my_flow_config.json
```

### Service Management

```bash
# Controller service
sudo systemctl start streon-controller
sudo systemctl status streon-controller
sudo journalctl -u streon-controller -f

# Flow services (per-Flow)
sudo systemctl start liquidsoap@flow_id
sudo systemctl start ffmpeg-srt-encoder@flow_id

# Inferno AoIP (if installed)
sudo systemctl start statime
sudo systemctl start inferno
sudo journalctl -u inferno -f

# Check all services
/opt/streon/scripts/health-check.sh
```

## Monitoring

Access monitoring dashboards:

- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Grafana**: [http://localhost:3000](http://localhost:3000) (default: admin/admin)
- **Metrics API**: [http://localhost:8000/api/v1/system/metrics](http://localhost:8000/api/v1/system/metrics)

## System Requirements

### Minimum
- Debian 13 (x64 or aarch64)
- 4GB RAM
- 20GB disk space
- 1Gbps network interface

### Recommended (Multi-Flow Production)
- 8GB+ RAM
- 50GB+ SSD storage
- Dedicated Dante NIC (Intel i210/i350 recommended)
- PTP-capable switch for AoIP networks
- UPS for critical operations

## Project Status

**Current Version**: 1.0.0-alpha

**Implemented**:
- ✅ Python FastAPI backend with REST API
- ✅ React + TypeScript Web UI with all core pages
- ✅ Flow lifecycle management (create, start, stop, restart, delete)
- ✅ Flow creation/editing UI (comprehensive form)
- ✅ Device discovery (ALSA/USB/Dante)
- ✅ StereoTool license input (text-based) and preset management (upload, list, assign)
- ✅ Liquidsoap script generation (Jinja2 templates)
- ✅ FFmpeg SRT transport wrappers (Opus/AAC/PCM)
- ✅ GPIO daemon (TCP/HTTP automation control)
- ✅ Metadata service (WebSocket streaming)
- ✅ Prometheus metrics exporter (25+ metrics)
- ✅ Systemd service templates (7 services)
- ✅ Installation scripts for Debian 13
- ✅ Real-time monitoring dashboard UI with VU meters and SRT stats

**In Development**:
- 🚧 Grafana dashboards (JSON definitions)
- 🚧 Dante/Inferno AoIP integration (hardware testing required)
- 🚧 Dante control panel UI
- 🚧 Network configuration UI

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## Support

For issues and questions: https://github.com/yourusername/streon/issues
