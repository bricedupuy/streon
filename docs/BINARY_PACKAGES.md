# Streon Binary Packages Reference

This document provides detailed information about the pre-built binary packages for Streon.

## Package Overview

| Package | Size (approx) | Architectures | Components |
|---------|---------------|---------------|------------|
| FFmpeg | ~50MB | x86_64, aarch64 | ffmpeg, ffprobe, libraries |
| Liquidsoap | ~100MB | x86_64, aarch64 | liquidsoap binary, OCaml runtime |
| Inferno AoIP | ~20MB | x86_64, aarch64 | statime, inferno, inferno2pipe, ALSA plugin |

**Total download:** ~170MB (vs ~200MB source code + compile time)

## FFmpeg Package

### File: `ffmpeg-{arch}.tar.gz`

**Build Configuration:**
```bash
FFmpeg 6.1 with:
  --enable-gpl
  --enable-nonfree
  --enable-libsrt          # SRT protocol support
  --enable-libopus         # Opus codec
  --enable-libfdk-aac      # AAC codec (high quality)
  --enable-libmp3lame      # MP3 codec
  --enable-libvorbis       # Vorbis codec
  --enable-libx264         # H.264 video codec
  --enable-libx265         # H.265 video codec
  --enable-libvpx          # VP8/VP9 codec
  --enable-protocol=srt    # SRT protocol
  --enable-openssl         # HTTPS support
```

### Package Contents

```
ffmpeg/
├── bin/
│   ├── ffmpeg          # Main FFmpeg binary (streaming, transcoding)
│   └── ffprobe         # Media file analyzer
└── lib/
    ├── libavcodec.so.60       # Codec library
    ├── libavformat.so.60      # Container format library
    ├── libavutil.so.58        # Utility functions
    ├── libavfilter.so.9       # Audio/video filtering
    ├── libavdevice.so.60      # Device input/output
    ├── libswscale.so.7        # Video scaling
    ├── libswresample.so.4     # Audio resampling
    └── pkgconfig/             # pkg-config files
```

### Key Features

- **SRT Transport:** Full SRT protocol support with encryption
- **Opus Codec:** Low-latency, high-quality audio codec
- **AAC Codec:** Industry-standard audio codec (fdk-aac)
- **Hardware Acceleration:** Supports hardware encoders when available
- **Network Protocols:** SRT, RTMP, HLS, HTTP, HTTPS

### Usage Examples

```bash
# Verify SRT support
/opt/streon/ffmpeg/bin/ffmpeg -protocols | grep srt

# Encode to SRT with Opus
ffmpeg -i input.wav -c:a libopus -b:a 128k -f matroska \
  srt://destination:9000?latency=200000

# Decode from SRT
ffmpeg -i srt://0.0.0.0:9000?mode=listener -f wav pipe:1 | aplay

# Check SRT stats
ffmpeg -i srt://source:9000 -c copy output.mkv -v info
```

### Verification

```bash
# Check version
ffmpeg -version

# List available codecs
ffmpeg -codecs | grep -E "opus|aac|srt"

# List protocols
ffmpeg -protocols | grep srt

# Check library dependencies
ldd /opt/streon/ffmpeg/bin/ffmpeg
```

## Liquidsoap Package

### File: `liquidsoap-2.4.0-{arch}.tar.gz`

**Build Configuration:**
- Liquidsoap 2.4.0 (latest stable)
- OCaml 4.14+ runtime
- All standard operators enabled
- StereoTool operator support

### Package Contents

```
liquidsoap/
├── bin/
│   └── liquidsoap      # Liquidsoap binary
├── lib/
│   └── ocaml/
│       └── liquidsoap/
│           ├── *.cma        # OCaml bytecode libraries
│           ├── *.cmxa       # OCaml native libraries
│           └── plugins/     # Liquidsoap plugins
└── share/
    └── liquidsoap/
        ├── libs/           # Standard library scripts
        └── doc/            # Documentation
```

### Key Features

- **Audio Processing:** Crossfade, fade, gain, normalize, compress
- **Fallback:** Automatic failover between sources
- **Silence Detection:** Detect and react to silence
- **Metadata:** Extract and manipulate metadata
- **StereoTool Integration:** Support for StereoTool processing
- **Telnet Server:** Remote control interface
- **Request Queue:** Dynamic playlist management

### Supported Operators

**Audio Processing:**
- `amplify` - Volume control
- `compress` - Dynamic range compression
- `normalize` - Loudness normalization
- `fade.in`, `fade.out` - Fading
- `crossfade` - Smooth transitions
- `stereotool` - StereoTool processing

**Sources:**
- `input.alsa` - ALSA audio input
- `input.http` - HTTP streaming
- `input.srt` - SRT input (with FFmpeg)
- `playlist` - File playlists
- `request.queue` - Dynamic requests

**Outputs:**
- `output.alsa` - ALSA audio output
- `output.file` - File output
- `output.dummy` - Discard output (for processing)

**Control:**
- `fallback` - Source fallover
- `switch` - Source switching
- `on_metadata` - Metadata events
- `server.telnet` - Remote control

### Usage Examples

```bash
# Check version
liquidsoap --version

# List available operators
liquidsoap --list-plugins

# Test configuration
liquidsoap --check script.liq

# Run script
liquidsoap script.liq

# Interactive mode
liquidsoap -i
```

### Verification

```bash
# Check version and build info
liquidsoap --version

# List audio input/output methods
liquidsoap --list-plugins | grep -E "input|output"

# Check for StereoTool support
liquidsoap --list-plugins | grep stereotool

# Test ALSA support
liquidsoap -c "output.alsa(sine())"
```

## Inferno AoIP Package

### File: `inferno-{arch}.tar.gz`

**Build Configuration:**
- Built with Rust (latest stable)
- Optimized for Dante/AES67 compatibility
- Hardware timestamping support
- PTPv1 and PTPv2 support

### Package Contents

```
inferno/
├── bin/
│   ├── statime         # PTP daemon (IEEE 1588 clock sync)
│   ├── inferno         # Main AoIP daemon
│   └── inferno2pipe    # Audio pipeline utility
├── lib/
│   └── libasound_pcm_inferno.so  # ALSA plugin for Inferno devices
└── config/
    ├── inferno.toml.example          # AoIP configuration template
    └── inferno-ptpv1.toml.example    # PTP configuration template
```

### Component Details

#### 1. statime - PTP Daemon

**Purpose:** Precise clock synchronization via IEEE 1588 (PTP)

**Features:**
- PTPv1 support (Dante compatibility)
- PTPv2 support (AES67 standard)
- Hardware timestamping (if NIC supports it)
- Sub-microsecond accuracy
- Grandmaster or slave mode

**Configuration:** `/opt/inferno/config/inferno-ptpv1.toml`

```toml
[interface]
name = "eth1"

[ptp]
domain = 0
priority1 = 128
priority2 = 128
version = 1              # PTPv1 for Dante
delay_mechanism = "E2E"  # End-to-End delay
timestamping = "hardware"
```

#### 2. inferno - AoIP Daemon

**Purpose:** Dante/AES67 audio streaming daemon

**Features:**
- AES67 RTP audio streaming
- Dante network compatibility
- Multiple simultaneous streams
- ALSA device integration
- QoS/DSCP tagging
- Low-latency buffering

**Configuration:** `/opt/inferno/config/inferno.toml`

```toml
[network]
interface = "eth1"
multicast_base = "239.69.0.0"
sample_rate = 48000
bit_depth = 24
packet_time_us = 1000

[streams]
max_rx_streams = 8    # Creates hw:InfernoStream0-7
max_tx_streams = 8    # Creates hw:InfernoTx0-7

[buffer]
rx_buffer_us = 5000   # 5ms receive buffer
tx_buffer_us = 2000   # 2ms transmit buffer
```

#### 3. inferno2pipe - Audio Pipeline

**Purpose:** Route audio between Inferno and other applications

**Usage:**
```bash
# Receive Dante stream to stdout
inferno2pipe --input hw:InfernoStream0 --output - | aplay

# Send audio to Dante
arecord -f S24_LE -r 48000 | inferno2pipe --input - --output hw:InfernoTx0
```

#### 4. libasound_pcm_inferno.so - ALSA Plugin

**Purpose:** Allows ALSA applications to access Inferno audio devices

**Installation:**
```bash
# Copy to ALSA plugin directory
sudo cp /opt/inferno/lib/libasound_pcm_inferno.so \
  /usr/lib/x86_64-linux-gnu/alsa-lib/

# Verify
aplay -L | grep Inferno
```

**ALSA Devices Created:**
- `hw:InfernoStream0` to `hw:InfernoStream7` (RX - receive from Dante)
- `hw:InfernoTx0` to `hw:InfernoTx7` (TX - transmit to Dante)

### Usage Examples

```bash
# Start PTP daemon
/opt/inferno/bin/statime -c /opt/inferno/config/inferno-ptpv1.toml

# Start Inferno daemon
/opt/inferno/bin/inferno -c /opt/inferno/config/inferno.toml

# List available Dante devices
arecord -L | grep Inferno
aplay -L | grep Inferno

# Test receive from Dante
arecord -D hw:InfernoStream0 -f S24_LE -r 48000 test.wav

# Test transmit to Dante
aplay -D hw:InfernoTx0 -f S24_LE -r 48000 audio.wav
```

### Verification

```bash
# Check statime version
/opt/inferno/bin/statime --version

# Check inferno version
/opt/inferno/bin/inferno --version

# Check PTP sync status
journalctl -u statime | grep -i sync

# Check ALSA plugin
ls -la /usr/lib/*/alsa-lib/libasound_pcm_inferno.so

# List Inferno ALSA devices
aplay -L | grep -A2 Inferno
```

### Network Requirements

**For Dante/AES67:**
- Dedicated network interface
- Gigabit Ethernet (1000 Mbps minimum)
- PTP-capable switch (for clock sync)
- Multicast support enabled
- IGMP snooping configured
- QoS/DSCP support recommended
- MTU 1500 (or 9000 for jumbo frames)

**Network Configuration:**
```bash
# Enable multicast
ip link set eth1 multicast on

# Add multicast route
ip route add 239.69.0.0/16 dev eth1

# Set MTU (optional, for jumbo frames)
ip link set eth1 mtu 9000

# Enable hardware timestamping (if supported)
ethtool -K eth1 rx-timestamping on tx-timestamping on
```

## Installation Locations

After installation, binaries are located at:

```
/opt/streon/
├── ffmpeg/
│   ├── bin/ffmpeg → /usr/local/bin/ffmpeg (symlink)
│   ├── bin/ffprobe → /usr/local/bin/ffprobe (symlink)
│   └── lib/
└── liquidsoap/
    ├── bin/liquidsoap → /usr/local/bin/liquidsoap (symlink)
    └── lib/

/opt/inferno/
├── bin/
│   ├── statime
│   ├── inferno
│   └── inferno2pipe
└── lib/
    └── libasound_pcm_inferno.so
```

## Compatibility

### Debian 13 (Trixie)

All binaries are built on Debian 13 and tested for compatibility.

**Tested Configurations:**
- Debian 13 (stable) - x86_64
- Debian 13 (stable) - aarch64
- Raspberry Pi 4/5 (Debian 13) - aarch64

**Should work on:**
- Ubuntu 24.04+ (similar library versions)
- Raspberry Pi OS (Debian-based)

**May not work on:**
- Debian 11/12 (older library versions)
- Ubuntu 22.04 or older
- CentOS/RHEL (different package ecosystem)

### Architecture Detection

The installer automatically detects your architecture:

```bash
uname -m
# x86_64  → Downloads x86_64 binaries
# aarch64 → Downloads aarch64 binaries
```

## Checksums and Security

Each binary package includes a SHA256 checksum file:

```bash
# Verify before installation
sha256sum -c ffmpeg-x86_64.tar.gz.sha256
sha256sum -c liquidsoap-2.4.0-x86_64.tar.gz.sha256
sha256sum -c inferno-x86_64.tar.gz.sha256
```

**Expected output:**
```
ffmpeg-x86_64.tar.gz: OK
liquidsoap-2.4.0-x86_64.tar.gz: OK
inferno-x86_64.tar.gz: OK
```

## Troubleshooting

### Library Errors

**Error:** `error while loading shared libraries: libsrt.so.1`

**Solution:**
```bash
# Update library cache
sudo ldconfig

# Check library paths
echo $LD_LIBRARY_PATH

# Add FFmpeg libs to path
echo "/opt/streon/ffmpeg/lib" | sudo tee /etc/ld.so.conf.d/streon-ffmpeg.conf
sudo ldconfig
```

### ALSA Plugin Not Found

**Error:** Inferno devices not appearing in `aplay -L`

**Solution:**
```bash
# Find correct ALSA plugin directory
dpkg-architecture -q DEB_HOST_MULTIARCH
# Output: x86_64-linux-gnu or aarch64-linux-gnu

# Copy plugin
sudo cp /opt/inferno/lib/libasound_pcm_inferno.so \
  /usr/lib/$(dpkg-architecture -q DEB_HOST_MULTIARCH)/alsa-lib/

# Restart ALSA
sudo systemctl restart alsa-restore
```

### Binary Won't Execute

**Error:** `cannot execute binary file: Exec format error`

**Solution:**
- Verify architecture: `uname -m`
- Ensure you downloaded correct architecture package
- Check if file is corrupted: verify checksum

## Support

For issues with binary packages:

- Check: [BINARY_DISTRIBUTION.md](BINARY_DISTRIBUTION.md)
- Report: https://github.com/bricedupuy/streon/issues
- Build from source if binaries don't work for your system
