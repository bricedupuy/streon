#!/bin/bash
# Build release binaries for distribution
# Run this script on target architecture (aarch64 or x86_64) to create release packages

set -euo pipefail

ARCH=$(uname -m)
VERSION="v1.0.0-alpha"
BUILD_DIR="/tmp/streon-release-build"
OUTPUT_DIR="$(pwd)/release-binaries"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

detect_architecture() {
    case "$ARCH" in
        x86_64|amd64)
            ARCH_NAME="x86_64"
            ;;
        aarch64|arm64)
            ARCH_NAME="aarch64"
            ;;
        *)
            log_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac

    log_info "Building for architecture: $ARCH_NAME"
}

build_ffmpeg() {
    log_info "Building FFmpeg with SRT support..."

    local ffmpeg_version="6.1"
    local ffmpeg_prefix="$BUILD_DIR/ffmpeg-install"

    cd "$BUILD_DIR"
    wget "https://ffmpeg.org/releases/ffmpeg-${ffmpeg_version}.tar.xz"
    tar -xf "ffmpeg-${ffmpeg_version}.tar.xz"
    cd "ffmpeg-${ffmpeg_version}"

    ./configure \
        --prefix="$ffmpeg_prefix" \
        --enable-gpl \
        --enable-nonfree \
        --enable-libsrt \
        --enable-libopus \
        --enable-libfdk-aac \
        --enable-libmp3lame \
        --enable-libvorbis \
        --enable-libx264 \
        --enable-libx265 \
        --enable-libvpx \
        --enable-protocol=srt \
        --enable-openssl \
        --enable-shared \
        --disable-static \
        --disable-doc \
        --disable-ffplay

    make -j$(nproc)
    make install

    # Package FFmpeg
    log_info "Packaging FFmpeg..."
    cd "$ffmpeg_prefix"
    tar -czf "$OUTPUT_DIR/ffmpeg-${ARCH_NAME}.tar.gz" .

    # Generate checksum
    sha256sum "$OUTPUT_DIR/ffmpeg-${ARCH_NAME}.tar.gz" > "$OUTPUT_DIR/ffmpeg-${ARCH_NAME}.tar.gz.sha256"

    log_info "FFmpeg package created: $OUTPUT_DIR/ffmpeg-${ARCH_NAME}.tar.gz"
}

build_liquidsoap() {
    log_info "Building Liquidsoap 2.4.0..."

    local liquidsoap_version="2.4.0"
    local liquidsoap_prefix="$BUILD_DIR/liquidsoap-install"

    # Install opam dependencies
    opam init -y --disable-sandboxing
    eval $(opam env)
    opam install -y liquidsoap.${liquidsoap_version}

    # Copy liquidsoap installation
    mkdir -p "$liquidsoap_prefix"
    cp -r $(opam var prefix)/* "$liquidsoap_prefix/"

    # Package Liquidsoap
    log_info "Packaging Liquidsoap..."
    cd "$liquidsoap_prefix"
    tar -czf "$OUTPUT_DIR/liquidsoap-2.4.0-${ARCH_NAME}.tar.gz" .

    # Generate checksum
    sha256sum "$OUTPUT_DIR/liquidsoap-2.4.0-${ARCH_NAME}.tar.gz" > "$OUTPUT_DIR/liquidsoap-2.4.0-${ARCH_NAME}.tar.gz.sha256"

    log_info "Liquidsoap package created: $OUTPUT_DIR/liquidsoap-2.4.0-${ARCH_NAME}.tar.gz"
}

build_inferno() {
    log_info "Building Inferno AoIP binaries..."

    local inferno_prefix="$BUILD_DIR/inferno-install"
    mkdir -p "$inferno_prefix"/{bin,lib,config}

    # Install Rust
    if ! command -v rustc &> /dev/null; then
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
        source "$HOME/.cargo/env"
    fi

    cd "$BUILD_DIR"
    git clone https://gitlab.com/lumifaza/inferno.git
    cd inferno

    # Build statime
    log_info "Building statime..."
    cd statime
    cargo build --release --bin statime
    cp target/release/statime "$inferno_prefix/bin/"
    cd ..

    # Build inferno daemon
    log_info "Building inferno daemon..."
    cd inferno
    cargo build --release
    cp target/release/inferno "$inferno_prefix/bin/"
    cd ..

    # Build inferno2pipe (if exists)
    if [ -d "inferno2pipe" ]; then
        log_info "Building inferno2pipe..."
        cd inferno2pipe
        cargo build --release
        cp target/release/inferno2pipe "$inferno_prefix/bin/"
        cd ..
    fi

    # Build ALSA plugin (if exists)
    if [ -d "libasound_pcm_inferno" ]; then
        log_info "Building libasound_pcm_inferno.so..."
        cd libasound_pcm_inferno
        cargo build --release
        cp target/release/libasound_pcm_inferno.so "$inferno_prefix/lib/"
        cd ..
    fi

    # Create default config templates
    cat > "$inferno_prefix/config/inferno.toml.example" <<'EOF'
# Inferno AoIP Configuration Template
[network]
interface = "eth1"
multicast_base = "239.69.0.0"
sample_rate = 48000
bit_depth = 24
packet_time_us = 1000

[streams]
max_rx_streams = 8
max_tx_streams = 8

[qos]
dscp = 46
vlan_priority = 5

[buffer]
rx_buffer_us = 5000
tx_buffer_us = 2000

[logging]
level = "info"
EOF

    cat > "$inferno_prefix/config/inferno-ptpv1.toml.example" <<'EOF'
# Statime PTP Configuration for Dante (PTPv1)
[interface]
name = "eth1"

[ptp]
domain = 0
priority1 = 128
priority2 = 128
version = 1
delay_mechanism = "E2E"
log_sync_interval = 0
log_announce_interval = 1
log_min_delay_req_interval = 0
timestamping = "hardware"
EOF

    # Package Inferno
    log_info "Packaging Inferno..."
    cd "$inferno_prefix"
    tar -czf "$OUTPUT_DIR/inferno-${ARCH_NAME}.tar.gz" .

    # Generate checksum
    sha256sum "$OUTPUT_DIR/inferno-${ARCH_NAME}.tar.gz" > "$OUTPUT_DIR/inferno-${ARCH_NAME}.tar.gz.sha256"

    log_info "Inferno package created: $OUTPUT_DIR/inferno-${ARCH_NAME}.tar.gz"
}

generate_manifest() {
    log_info "Generating release manifest..."

    cat > "$OUTPUT_DIR/MANIFEST-${ARCH_NAME}.txt" <<EOF
Streon Binary Release - ${VERSION}
Architecture: ${ARCH_NAME}
Build Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

Contents:
--------
1. ffmpeg-${ARCH_NAME}.tar.gz
   - FFmpeg 6.1 with SRT, Opus, AAC support
   - Includes: ffmpeg, ffprobe
   - SHA256: $(cat "$OUTPUT_DIR/ffmpeg-${ARCH_NAME}.tar.gz.sha256" | awk '{print $1}')

2. liquidsoap-2.4.0-${ARCH_NAME}.tar.gz
   - Liquidsoap 2.4.0 with all dependencies
   - SHA256: $(cat "$OUTPUT_DIR/liquidsoap-2.4.0-${ARCH_NAME}.tar.gz.sha256" | awk '{print $1}')

3. inferno-${ARCH_NAME}.tar.gz
   - Inferno AoIP binaries (statime, inferno, inferno2pipe)
   - ALSA plugin: libasound_pcm_inferno.so
   - SHA256: $(cat "$OUTPUT_DIR/inferno-${ARCH_NAME}.tar.gz.sha256" | awk '{print $1}')

Installation:
-------------
Use the download-binaries.sh script to automatically download and install these binaries:

    sudo ./install/download-binaries.sh

Or manually extract to appropriate locations:
    - FFmpeg:     /opt/streon/ffmpeg/
    - Liquidsoap: /opt/streon/liquidsoap/
    - Inferno:    /opt/inferno/

Verification:
-------------
Verify checksums before installation:

    sha256sum -c ffmpeg-${ARCH_NAME}.tar.gz.sha256
    sha256sum -c liquidsoap-2.4.0-${ARCH_NAME}.tar.gz.sha256
    sha256sum -c inferno-${ARCH_NAME}.tar.gz.sha256

Support:
--------
GitHub: https://github.com/bricedupuy/streon
Issues: https://github.com/bricedupuy/streon/issues
EOF

    log_info "Manifest created: $OUTPUT_DIR/MANIFEST-${ARCH_NAME}.txt"
}

main() {
    check_root
    detect_architecture

    log_info "Building release binaries for Streon ${VERSION} (${ARCH_NAME})..."
    echo ""

    # Create directories
    rm -rf "$BUILD_DIR" "$OUTPUT_DIR"
    mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"

    # Ask what to build
    read -p "Build FFmpeg? (Y/n): " -n 1 -r BUILD_FFMPEG
    echo
    BUILD_FFMPEG=${BUILD_FFMPEG:-y}

    read -p "Build Liquidsoap? (Y/n): " -n 1 -r BUILD_LIQUIDSOAP
    echo
    BUILD_LIQUIDSOAP=${BUILD_LIQUIDSOAP:-y}

    read -p "Build Inferno? (Y/n): " -n 1 -r BUILD_INFERNO
    echo
    BUILD_INFERNO=${BUILD_INFERNO:-y}

    echo ""
    log_info "Starting build process..."

    # Build components
    if [[ $BUILD_FFMPEG =~ ^[Yy]$ ]]; then
        build_ffmpeg || log_error "FFmpeg build failed"
    fi

    if [[ $BUILD_LIQUIDSOAP =~ ^[Yy]$ ]]; then
        build_liquidsoap || log_error "Liquidsoap build failed"
    fi

    if [[ $BUILD_INFERNO =~ ^[Yy]$ ]]; then
        build_inferno || log_error "Inferno build failed"
    fi

    # Generate manifest
    generate_manifest

    # Cleanup
    log_info "Cleaning up build directory..."
    rm -rf "$BUILD_DIR"

    echo ""
    log_info "Build complete!"
    log_info "Release packages available in: $OUTPUT_DIR"
    echo ""
    log_info "Next steps:"
    log_info "1. Create a GitHub release: ${VERSION}"
    log_info "2. Upload all files from $OUTPUT_DIR"
    log_info "3. Test download-binaries.sh on a fresh system"
    echo ""
    log_info "Files to upload:"
    ls -lh "$OUTPUT_DIR"
}

main "$@"
