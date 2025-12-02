# Streon - Project Status

**Last Updated:** December 2, 2025

## Overview

Streon is a professional, broadcast-grade, multi-Flow audio transport system for radio broadcasters. This document tracks the implementation status of all major components.

## Quick Links

- **Documentation:** [README.md](README.md)
- **Implementation Plan:** [.claude/plans/gentle-frolicking-firefly.md](.claude/plans/gentle-frolicking-firefly.md)
- **Getting Started:** [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)
- **API Docs (when running):** http://localhost:8000/docs

---

## Implementation Status

### ✅ Phase 1: Foundation (100% Complete)

- [x] Project structure created
- [x] README and documentation
- [x] Technology stack selected (Python + FastAPI + React + TypeScript)
- [x] User requirements confirmed

### ✅ Phase 2: Backend Core (70% Complete)

#### Completed
- [x] FastAPI application skeleton
- [x] Pydantic models (Flow, Device, StereoTool, Config)
- [x] Configuration Manager (YAML persistence)
- [x] StereoTool Manager (license & preset upload/management)
- [x] Device Manager (ALSA scanning, Inferno detection)
- [x] REST API: `/api/v1/stereotool/*` (fully functional)
- [x] REST API: `/api/v1/devices/*` (fully functional)
- [x] REST API: `/api/v1/system/health` (basic)

#### In Progress
- [ ] Flow Manager (models done, implementation pending)
- [ ] REST API: `/api/v1/flows/*` (placeholder)

#### Not Started
- [ ] Inferno Manager
- [ ] Network Manager
- [ ] GPIO Daemon
- [ ] Metadata Service
- [ ] Prometheus metrics exporter

### 🚧 Phase 3: Frontend (30% Complete)

#### Completed
- [x] React + TypeScript + Vite setup
- [x] Tailwind CSS configuration
- [x] React Router structure
- [x] API client (axios)
- [x] StereoTool API functions

#### Not Started
- [ ] Layout components (Header, Sidebar)
- [ ] StereoTool UI (upload, list, activate)
- [ ] Device UI (list, scan, edit)
- [ ] Flow UI (create, edit, monitor)
- [ ] Inferno UI
- [ ] Monitoring dashboards
- [ ] WebSocket integration

### ⏳ Phase 4: Liquidsoap Integration (0% Complete)

- [ ] Liquidsoap script templates (Jinja2)
- [ ] StereoTool operator integration
- [ ] Fallback/switch logic
- [ ] Silence detection
- [ ] Audio metering
- [ ] Metadata extraction

### ⏳ Phase 5: FFmpeg Transport (0% Complete)

- [ ] FFmpeg wrapper classes
- [ ] SRT encoder (Opus/AAC/PCM)
- [ ] SRT decoder
- [ ] Stats parser (RTT, loss, bitrate)
- [ ] Container handling (Matroska/TS)

### ⏳ Phase 6: Systemd Integration (0% Complete)

- [ ] Service unit files
  - [ ] liquidsoap@.service
  - [ ] ffmpeg-srt-encoder@.service
  - [ ] ffmpeg-srt-decoder@.service
  - [ ] streon-controller.service
  - [ ] inferno.service
  - [ ] statime.service
- [ ] Service management via controller

### ⏳ Phase 7: Installation (0% Complete)

- [ ] Debian 13 master installer
- [ ] Dependencies installer
- [ ] Liquidsoap 2.4.0 build script
- [ ] FFmpeg build script (with SRT)
- [ ] Inferno setup script

### ⏳ Phase 8: Advanced Features (0% Complete)

- [ ] Inferno AoIP integration
- [ ] GPIO engine (TCP/HTTP)
- [ ] Metadata service (WebSocket)
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules

---

## File Tree

```
streon-claude/
├── README.md                              ✅ Created
├── PROJECT_STATUS.md                      ✅ Created
├── docs/
│   └── GETTING_STARTED.md                 ✅ Created
├── controller/                             ✅ Python Backend
│   ├── main.py                            ✅ FastAPI app
│   ├── requirements.txt                   ✅ Dependencies
│   ├── api/                               ✅ Endpoints
│   │   ├── __init__.py                    ✅
│   │   ├── stereotool.py                  ✅ Complete
│   │   ├── devices.py                     ✅ Complete
│   │   ├── flows.py                       🚧 Placeholder
│   │   └── system.py                      🚧 Partial
│   ├── core/                              ✅ Business logic
│   │   ├── __init__.py                    ✅
│   │   ├── config_manager.py              ✅ Complete
│   │   ├── stereotool_manager.py          ✅ Complete
│   │   ├── device_manager.py              ✅ Complete
│   │   ├── flow_manager.py                ⏳ TODO
│   │   ├── inferno_manager.py             ⏳ TODO
│   │   ├── network_manager.py             ⏳ TODO
│   │   ├── gpio_daemon.py                 ⏳ TODO
│   │   └── metadata_service.py            ⏳ TODO
│   ├── models/                            ✅ Pydantic models
│   │   ├── __init__.py                    ✅
│   │   ├── flow.py                        ✅ Complete
│   │   ├── device.py                      ✅ Complete
│   │   ├── stereotool.py                  ✅ Complete
│   │   └── config.py                      ✅ Complete
│   ├── monitoring/                        ⏳ TODO
│   └── utils/                             ⏳ TODO
├── web-ui/                                 ✅ React Frontend
│   ├── package.json                       ✅ Created
│   ├── vite.config.ts                     ✅ Created
│   ├── tsconfig.json                      ✅ Created
│   ├── tailwind.config.js                 ✅ Created
│   ├── index.html                         ✅ Created
│   └── src/
│       ├── main.tsx                       ✅ Created
│       ├── App.tsx                        ✅ Created
│       ├── index.css                      ✅ Created
│       ├── api/
│       │   ├── client.ts                  ✅ Complete
│       │   ├── stereotool.ts              ✅ Complete
│       │   ├── devices.ts                 ⏳ TODO
│       │   └── flows.ts                   ⏳ TODO
│       ├── components/                    ⏳ TODO (all)
│       │   ├── common/                    ⏳ Layout, Header, Sidebar
│       │   ├── stereotool/                ⏳ Upload, List
│       │   ├── devices/                   ⏳ List, Scanner
│       │   ├── flows/                     ⏳ Editor, Monitor
│       │   ├── inferno/                   ⏳ Status, Config
│       │   └── monitoring/                ⏳ Dashboards
│       ├── pages/                         ⏳ TODO (all)
│       └── store/                         ⏳ TODO
├── liquidsoap/                            ⏳ TODO
│   ├── templates/                         ⏳ Jinja2 templates
│   ├── lib/                               ⏳ Shared functions
│   └── stereotool/                        ✅ Directories created
│       ├── presets/                       ✅ (will contain .sts files)
│       └── licenses/                      ✅ (will contain licenses)
├── services/                              ⏳ TODO
│   ├── liquidsoap@.service                ⏳
│   ├── ffmpeg-srt-encoder@.service        ⏳
│   ├── streon-controller.service          ⏳
│   ├── inferno.service                    ⏳
│   └── statime.service                    ⏳
├── install/                               ⏳ TODO
│   ├── debian-13-install.sh               ⏳
│   ├── dependencies.sh                    ⏳
│   ├── liquidsoap-build.sh                ⏳
│   ├── ffmpeg-build.sh                    ⏳
│   └── inferno-setup.sh                   ⏳
├── monitoring/                            ⏳ TODO
│   ├── prometheus/                        ⏳
│   └── grafana/dashboards/                ⏳
├── config/                                ✅ Directories created
│   ├── flows/                             ✅
│   ├── inferno/                           ✅
│   └── network/                           ✅
└── scripts/                               ⏳ TODO
```

---

## What Works Right Now

### Backend API

You can currently:

1. **Upload StereoTool licenses**
   ```bash
   curl -X POST http://localhost:8000/api/v1/stereotool/licenses \
     -F "file=@license.key"
   ```

2. **Upload StereoTool presets**
   ```bash
   curl -X POST http://localhost:8000/api/v1/stereotool/presets \
     -F "file=@preset.sts" \
     -F "name=FM Broadcast" \
     -F "description=Heavy compression"
   ```

3. **List presets**
   ```bash
   curl http://localhost:8000/api/v1/stereotool/presets
   ```

4. **Activate a preset**
   ```bash
   curl -X PUT http://localhost:8000/api/v1/stereotool/presets/{preset_id}/activate
   ```

5. **Scan for audio devices**
   ```bash
   curl http://localhost:8000/api/v1/devices/scan
   ```

6. **List devices**
   ```bash
   curl http://localhost:8000/api/v1/devices
   ```

7. **Update device friendly name**
   ```bash
   curl -X PUT http://localhost:8000/api/v1/devices/{device_id} \
     -H "Content-Type: application/json" \
     -d '{"friendly_name": "Studio Interface"}'
   ```

8. **Check system health**
   ```bash
   curl http://localhost:8000/api/v1/system/health
   ```

---

## Next Priority Tasks

### Immediate (Week 1-2)

1. **Create missing stub files for Flow Manager**
   - Implement `core/flow_manager.py`
   - Implement Flow API endpoints in `api/flows.py`

2. **Create Liquidsoap template**
   - Design Jinja2 template for Flow scripts
   - Include StereoTool integration
   - Add fallback/silence detection

3. **Create basic UI components**
   - Layout (Header + Sidebar)
   - StereoTool page (upload presets)
   - Device page (list devices)

### Short-term (Week 3-4)

4. **Implement FFmpeg wrapper**
   - SRT encoder command generation
   - Process management
   - Stats parsing

5. **Create systemd service files**
   - Templated units for Flows
   - Controller service

6. **Build Flow UI**
   - Flow editor
   - Flow list
   - Start/stop controls

### Medium-term (Month 2)

7. **Inferno integration**
8. **GPIO engine**
9. **Metadata service**
10. **Installation scripts**

---

## Development Workflow

### Running the Stack

**Terminal 1 - Backend:**
```bash
cd controller
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd web-ui
npm install  # First time only
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Questions or Issues?

1. Check [GETTING_STARTED.md](docs/GETTING_STARTED.md)
2. Review [Implementation Plan](.claude/plans/gentle-frolicking-firefly.md)
3. Check API docs at http://localhost:8000/docs

---

## Progress Tracking

**Overall Completion: ~25%**

- Foundation: 100%
- Backend Core: 70%
- Frontend: 30%
- Liquidsoap: 0%
- FFmpeg: 0%
- Systemd: 0%
- Installation: 0%
- Advanced Features: 0%
