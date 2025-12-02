# Getting Started with Streon Development

## What's Been Built

We've created the foundation of the Streon project with the following components:

### Backend (Python FastAPI)

✅ **Complete:**
- FastAPI application skeleton ([controller/main.py](controller/main.py))
- Pydantic models for all entities (Flow, Device, StereoTool, Config)
- StereoTool manager (license & preset upload/management)
- Device manager (ALSA device scanning)
- Configuration manager (YAML config persistence)
- REST API endpoints:
  - `/api/v1/stereotool/*` - Fully functional
  - `/api/v1/devices/*` - Fully functional
  - `/api/v1/flows/*` - Placeholder (TODO)
  - `/api/v1/system/*` - Basic health check

### Frontend (React + TypeScript)

✅ **Complete:**
- Vite + React 18 + TypeScript setup
- Tailwind CSS configuration
- React Router setup
- API client with axios
- StereoTool API client functions

### Project Structure

```
streon-claude/
├── controller/          # Python FastAPI backend
│   ├── api/            # API endpoints
│   ├── core/           # Business logic managers
│   ├── models/         # Pydantic models
│   └── requirements.txt
├── web-ui/             # React frontend
│   ├── src/
│   │   ├── api/        # API client
│   │   ├── components/ # React components (TODO)
│   │   └── pages/      # Page components (TODO)
│   └── package.json
├── services/           # Systemd unit files (TODO)
├── liquidsoap/         # Liquidsoap templates (TODO)
├── install/            # Installation scripts (TODO)
└── docs/               # Documentation
```

## Running the Development Environment

### Backend

```bash
cd controller

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Frontend

```bash
cd web-ui

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Testing the Backend

### Test StereoTool Upload

```bash
# Upload a preset file
curl -X POST http://localhost:8000/api/v1/stereotool/presets \
  -F "file=@/path/to/preset.sts" \
  -F "name=My Broadcast Preset" \
  -F "description=Heavy compression for FM"

# List presets
curl http://localhost:8000/api/v1/stereotool/presets

# Activate a preset
curl -X PUT http://localhost:8000/api/v1/stereotool/presets/preset_abc123/activate
```

### Test Device Scanning

```bash
# Scan for devices
curl http://localhost:8000/api/v1/devices/scan

# List devices
curl http://localhost:8000/api/v1/devices

# Update device friendly name
curl -X PUT http://localhost:8000/api/v1/devices/dev_usb0 \
  -H "Content-Type: application/json" \
  -d '{"friendly_name": "Studio Interface"}'
```

### Check System Health

```bash
curl http://localhost:8000/api/v1/system/health
```

## Next Steps

### Priority 1: Core Functionality

1. **Implement Flow Manager** ([controller/core/flow_manager.py](controller/core/flow_manager.py))
   - Liquidsoap script generation
   - FFmpeg wrapper
   - Systemd service management
   - Process monitoring

2. **Create Liquidsoap Templates** ([liquidsoap/templates/](liquidsoap/templates/))
   - Flow script template (Jinja2)
   - StereoTool integration
   - Fallback logic

3. **Implement Flow API** ([controller/api/flows.py](controller/api/flows.py))
   - Create/update/delete Flows
   - Start/stop/restart Flows
   - Get Flow status and metrics

### Priority 2: Web UI

4. **Create Layout Components**
   - Header with navigation
   - Sidebar menu
   - Status badges

5. **Implement StereoTool UI**
   - License upload component
   - Preset upload component
   - Preset list with activate/delete

6. **Implement Device UI**
   - Device list
   - Scan button
   - Friendly name editing

7. **Implement Flow UI**
   - Flow list
   - Flow editor (create/edit)
   - Flow monitor (real-time status)

### Priority 3: Installation & Deployment

8. **Create Systemd Service Files**
   - liquidsoap@.service
   - ffmpeg-srt-encoder@.service
   - streon-controller.service

9. **Write Installation Scripts**
   - Debian 13 installer
   - Liquidsoap 2.4.0 build script
   - FFmpeg build script
   - Inferno setup script

### Priority 4: Advanced Features

10. **Inferno Integration**
    - Inferno manager implementation
    - PTP status monitoring
    - Stream health detection

11. **GPIO Engine**
    - TCP/HTTP servers
    - Event routing
    - WebSocket support

12. **Metadata Service**
    - Liquidsoap metadata parsing
    - WebSocket streaming
    - REST endpoint

13. **Monitoring**
    - Prometheus metrics exporter
    - FFmpeg stats parser
    - Grafana dashboards

## Current Status

### ✅ Working
- Backend API server
- StereoTool file upload/management
- Device scanning (ALSA)
- Configuration management
- API documentation (FastAPI automatic docs)

### 🚧 In Progress
- Flow management (models complete, implementation needed)
- Frontend UI components (structure complete, components needed)

### ⏳ Not Started
- Liquidsoap integration
- FFmpeg wrappers
- Systemd service management
- Inferno AoIP integration
- GPIO engine
- Metadata service
- Monitoring/metrics

## Development Tips

1. **Use FastAPI docs:** Visit `http://localhost:8000/docs` to interactively test the API

2. **Check logs:** Backend logs appear in the terminal where you run `uvicorn`

3. **Data location (development):**
   - Configs: `c:\Users\BriceDupuy\Code\streon-claude\config\`
   - StereoTool files: `c:\Users\BriceDupuy\Code\streon-claude\liquidsoap\stereotool\`

4. **Frontend proxy:** Vite proxies `/api` requests to `http://localhost:8000`

5. **Hot reload:** Both backend (with `--reload`) and frontend (Vite) support hot reload

## Questions?

See the [Architecture Documentation](../README.md) or the [Implementation Plan](../.claude/plans/gentle-frolicking-firefly.md)
