# Streon

**Professional Multi-Flow Audio Transport System for Radio Broadcasters**

Streon is a Linux-based, modular audio engine designed for professional radio operations. It unifies audio ingest, routing, processing, AoIP, SRT transport, GPIO automation, and real-time monitoring with a complete Web UI.

## Features

- **Multi-Flow Architecture** - Unlimited concurrent, independent audio pipelines
- **Liquidsoap 2.4.0** - Professional audio processing with StereoTool integration
- **SRT Transport** - Opus/AAC/PCM over SRT with adaptive bitrate
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

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/streon.git
cd streon

# Run installer (Debian 13 only)
sudo ./install/debian-13-install.sh
```

### Development

```bash
# Start backend
cd controller
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Start frontend (in another terminal)
cd web-ui
npm install
npm run dev
```

Access the Web UI at `http://localhost:5173`

API documentation at `http://localhost:8000/docs`

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

## Documentation

- [Installation Guide](docs/installation.md)
- [Quick Start](docs/quickstart.md)
- [Flow Configuration](docs/flow-configuration.md)
- [Inferno AoIP Setup](docs/inferno-setup.md)
- [API Reference](docs/api-reference.md)
- [Troubleshooting](docs/troubleshooting.md)

## System Requirements

- Debian 13 (x64 or aarch64)
- Minimum 4GB RAM (8GB recommended for multiple Flows)
- Dedicated network interface for Dante/AES67 (optional)
- PTP-capable switch for Dante networks (optional)

## License

[Your License Here]

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## Support

For issues and questions: https://github.com/yourusername/streon/issues
