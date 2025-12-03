# Streon Binary Distribution Guide

This document explains how to create, distribute, and use pre-built binaries for Streon to significantly reduce installation time.

## Overview

Compiling FFmpeg, Liquidsoap, and Inferno from source can take 30-60 minutes on typical hardware. To speed up deployment, we provide pre-built binaries for common architectures.

**Supported Architectures:**
- `x86_64` (Intel/AMD 64-bit)
- `aarch64` (ARM 64-bit, e.g., Raspberry Pi 4/5, NVIDIA Jetson)

## For Users: Fast Installation with Pre-built Binaries

### Quick Start

The installer will automatically prompt to use pre-built binaries:

```bash
sudo ./install/debian-13-install.sh
```

When prompted:
```
Use pre-built binaries? (Faster installation) (Y/n):
```

Answer **Y** for fast installation (~5 minutes) or **n** to build from source (~45 minutes).

### Manual Binary Download

If you prefer to download binaries separately:

```bash
# Download and install pre-built binaries
sudo ./install/download-binaries.sh

# Then run the full installer
sudo ./install/debian-13-install.sh
```

The `download-binaries.sh` script will:
1. Detect your architecture (x86_64 or aarch64)
2. Download appropriate binaries from GitHub Releases
3. Verify checksums
4. Extract to correct locations

### What's Included

Each binary package includes:

**1. FFmpeg Package** (`ffmpeg-{arch}.tar.gz`)
- FFmpeg 6.1 compiled with:
  - libsrt (SRT protocol support)
  - libopus (Opus codec)
  - libfdk-aac (AAC codec)
  - libmp3lame, libvorbis, libx264, libx265, libvpx
- Binaries: `ffmpeg`, `ffprobe`
- Shared libraries

**2. Liquidsoap Package** (`liquidsoap-2.4.0-{arch}.tar.gz`)
- Liquidsoap 2.4.0 with all dependencies
- StereoTool operator support
- OCaml runtime

**3. Inferno AoIP Package** (`inferno-{arch}.tar.gz`)
- `statime` - PTP daemon for clock synchronization
- `inferno` - Dante/AES67 audio streaming daemon
- `inferno2pipe` - Audio pipeline utility
- `libasound_pcm_inferno.so` - ALSA plugin for Inferno device access
- Default configuration templates

### Installation Locations

Binaries are installed to:
```
/opt/streon/ffmpeg/          # FFmpeg
/opt/streon/liquidsoap/      # Liquidsoap
/opt/inferno/                # Inferno AoIP
```

Symlinks created in `/usr/local/bin/`:
- `ffmpeg` → `/opt/streon/ffmpeg/bin/ffmpeg`
- `ffprobe` → `/opt/streon/ffmpeg/bin/ffprobe`
- `liquidsoap` → `/opt/streon/liquidsoap/bin/liquidsoap`

---

## For Maintainers: Building Release Binaries

### Prerequisites

To build release binaries, you need:
- A Debian 13 system (or compatible distribution)
- The target architecture (build on x86_64 for x86_64, aarch64 for aarch64)
- Root/sudo access
- At least 20GB free disk space
- Build dependencies installed

### Build Process

1. **Prepare Build Environment**

```bash
# Clone repository
git clone https://github.com/bricedupuy/streon.git
cd streon

# Install build dependencies
sudo ./install/dependencies.sh
```

2. **Run Build Script**

```bash
# Build all binaries for your architecture
sudo ./install/build-release-binaries.sh
```

The script will prompt for what to build:
```
Build FFmpeg? (Y/n): y
Build Liquidsoap? (Y/n): y
Build Inferno? (Y/n): y
```

3. **Build Output**

After completion (30-60 minutes), you'll find release packages in `./release-binaries/`:

```
release-binaries/
├── ffmpeg-x86_64.tar.gz
├── ffmpeg-x86_64.tar.gz.sha256
├── liquidsoap-2.4.0-x86_64.tar.gz
├── liquidsoap-2.4.0-x86_64.tar.gz.sha256
├── inferno-x86_64.tar.gz
├── inferno-x86_64.tar.gz.sha256
└── MANIFEST-x86_64.txt
```

### Build on Both Architectures

To support both architectures, you must build on each:

**On x86_64 machine:**
```bash
sudo ./install/build-release-binaries.sh
# Produces: ffmpeg-x86_64.tar.gz, liquidsoap-2.4.0-x86_64.tar.gz, inferno-x86_64.tar.gz
```

**On aarch64 machine (e.g., Raspberry Pi 5):**
```bash
sudo ./install/build-release-binaries.sh
# Produces: ffmpeg-aarch64.tar.gz, liquidsoap-2.4.0-aarch64.tar.gz, inferno-aarch64.tar.gz
```

### Creating a GitHub Release

1. **Create Release Tag**

```bash
git tag -a v1.0.0-alpha -m "Streon v1.0.0-alpha release"
git push origin v1.0.0-alpha
```

2. **Create GitHub Release**

- Go to: https://github.com/bricedupuy/streon/releases/new
- Select tag: `v1.0.0-alpha`
- Title: `Streon v1.0.0-alpha`
- Description: Copy from CHANGELOG or describe features

3. **Upload Binary Packages**

Upload all files from both architectures:
```
ffmpeg-x86_64.tar.gz
ffmpeg-x86_64.tar.gz.sha256
liquidsoap-2.4.0-x86_64.tar.gz
liquidsoap-2.4.0-x86_64.tar.gz.sha256
inferno-x86_64.tar.gz
inferno-x86_64.tar.gz.sha256
MANIFEST-x86_64.txt

ffmpeg-aarch64.tar.gz
ffmpeg-aarch64.tar.gz.sha256
liquidsoap-2.4.0-aarch64.tar.gz
liquidsoap-2.4.0-aarch64.tar.gz.sha256
inferno-aarch64.tar.gz
inferno-aarch64.tar.gz.sha256
MANIFEST-aarch64.txt
```

4. **Publish Release**

Make sure to mark as "pre-release" for alpha/beta versions.

---

## Binary Package Structure

### FFmpeg Package

```
ffmpeg/
├── bin/
│   ├── ffmpeg          # Main binary
│   └── ffprobe         # Media info tool
└── lib/
    ├── libavcodec.so.*
    ├── libavformat.so.*
    ├── libavutil.so.*
    └── ... (other libraries)
```

### Liquidsoap Package

```
liquidsoap/
├── bin/
│   └── liquidsoap      # Main binary
├── lib/
│   └── liquidsoap/     # OCaml libraries
└── share/
    └── liquidsoap/     # Documentation
```

### Inferno Package

```
inferno/
├── bin/
│   ├── statime         # PTP daemon
│   ├── inferno         # AoIP daemon
│   └── inferno2pipe    # Audio pipeline utility
├── lib/
│   └── libasound_pcm_inferno.so  # ALSA plugin
└── config/
    ├── inferno.toml.example
    └── inferno-ptpv1.toml.example
```

---

## Verification

### Verify Checksums

Always verify checksums before installation:

```bash
# In the download directory
sha256sum -c ffmpeg-x86_64.tar.gz.sha256
sha256sum -c liquidsoap-2.4.0-x86_64.tar.gz.sha256
sha256sum -c inferno-x86_64.tar.gz.sha256
```

Expected output:
```
ffmpeg-x86_64.tar.gz: OK
liquidsoap-2.4.0-x86_64.tar.gz: OK
inferno-x86_64.tar.gz: OK
```

### Test Binaries

After installation, verify each component works:

```bash
# FFmpeg
ffmpeg -version
ffmpeg -protocols | grep srt

# Liquidsoap
liquidsoap --version

# Inferno
/opt/inferno/bin/statime --version
/opt/inferno/bin/inferno --version
```

---

## Troubleshooting

### Binary Download Fails

**Problem:** Download script fails with 404 error

**Solution:**
1. Check GitHub release exists: https://github.com/bricedupuy/streon/releases
2. Verify version in `download-binaries.sh` matches release tag
3. Ensure architecture is supported (x86_64 or aarch64)

**Workaround:** Build from source instead:
```bash
# Disable binary download when prompted
# Or set environment variable
export USE_BINARIES=n
sudo ./install/debian-13-install.sh
```

### Checksum Verification Fails

**Problem:** `sha256sum` reports checksum mismatch

**Solution:**
1. Download may be corrupted - try re-downloading
2. Check if binary package was updated but checksum file wasn't
3. Contact maintainers if problem persists

**Workaround:** Skip verification (NOT recommended for production):
```bash
# Edit download-binaries.sh and comment out verify_checksum calls
```

### Binary Incompatibility

**Problem:** Binary fails to run with "cannot execute binary file" or library errors

**Solution:**
1. Verify you're on Debian 13 (or compatible): `cat /etc/debian_version`
2. Check architecture matches: `uname -m`
3. Install missing dependencies: `sudo ./install/dependencies.sh`
4. Check library paths: `ldd /opt/streon/ffmpeg/bin/ffmpeg`

**Workaround:** Build from source for your specific system.

### Inferno ALSA Plugin Not Found

**Problem:** Liquidsoap can't find Inferno ALSA devices

**Solution:**
1. Copy ALSA plugin to system directory:
```bash
sudo cp /opt/inferno/lib/libasound_pcm_inferno.so /usr/lib/x86_64-linux-gnu/alsa-lib/
# or for aarch64:
sudo cp /opt/inferno/lib/libasound_pcm_inferno.so /usr/lib/aarch64-linux-gnu/alsa-lib/
```

2. Restart ALSA:
```bash
sudo systemctl restart alsa-restore
```

---

## Build Customization

### Custom FFmpeg Build

If you need different FFmpeg features:

1. Edit `install/build-release-binaries.sh`
2. Modify `./configure` flags in `build_ffmpeg()` function:

```bash
./configure \
    --prefix="$ffmpeg_prefix" \
    --enable-gpl \
    --enable-nonfree \
    --enable-libsrt \
    --enable-libopus \
    --enable-libfdk-aac \
    # Add your custom flags here
    --enable-libvmaf \
    --enable-libaom \
    # ...
```

3. Rebuild: `sudo ./install/build-release-binaries.sh`

### Custom Inferno Configuration

To include custom Inferno configurations in binary package:

1. Edit `install/build-release-binaries.sh`
2. Modify config templates in `build_inferno()` function
3. Add your custom `.toml` files to `$inferno_prefix/config/`

---

## Performance Comparison

| Method | Time | Disk Space | Network | When to Use |
|--------|------|------------|---------|-------------|
| Pre-built binaries | ~5 min | 500MB | ~150MB download | Production, quick setup |
| Build from source | ~45 min | 5GB (build) + 500MB (installed) | ~200MB (source) | Custom builds, unsupported platforms |

**Recommendation:** Use pre-built binaries unless you have specific customization needs.

---

## Security Considerations

### Checksum Verification

Always verify checksums to ensure binaries haven't been tampered with:

```bash
sha256sum -c *.sha256
```

### Binary Signing (Future)

Future releases may include GPG signatures:

```bash
# Import maintainer's public key
gpg --import streon-release-key.asc

# Verify signature
gpg --verify ffmpeg-x86_64.tar.gz.sig ffmpeg-x86_64.tar.gz
```

### Building Your Own

For maximum security, build from source on a trusted system:

```bash
export USE_BINARIES=n
sudo ./install/debian-13-install.sh
```

---

## Distribution Checklist

Before creating a new release:

- [ ] Build binaries on x86_64 system
- [ ] Build binaries on aarch64 system
- [ ] Verify all checksums match
- [ ] Test installation on fresh Debian 13 systems (both architectures)
- [ ] Verify FFmpeg SRT support: `ffmpeg -protocols | grep srt`
- [ ] Verify Liquidsoap version: `liquidsoap --version`
- [ ] Verify Inferno binaries present and executable
- [ ] Update version number in `download-binaries.sh`
- [ ] Create GitHub release with tag
- [ ] Upload all binaries and checksums
- [ ] Update CHANGELOG.md
- [ ] Announce release in documentation

---

## Support

For issues with binary packages:

1. Check this documentation first
2. Verify system requirements (Debian 13, supported architecture)
3. Try building from source as a workaround
4. Report issue: https://github.com/bricedupuy/streon/issues

Include:
- Architecture: `uname -m`
- Debian version: `cat /etc/debian_version`
- Error messages from installation
- Output of `ldd` on failing binary
