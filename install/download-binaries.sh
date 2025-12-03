#!/bin/bash
# Download pre-built binaries for Streon components
# Significantly speeds up installation by skipping compilation

set -euo pipefail

ARCH=$(uname -m)
BINARY_BASE_URL="https://github.com/bricedupuy/streon/releases/download"
VERSION="v1.0.0-alpha"
INSTALL_DIR="${1:-/opt/streon}"
INFERNO_DIR="/opt/inferno"

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

    log_info "Detected architecture: $ARCH_NAME"
}

download_file() {
    local url=$1
    local output=$2

    log_info "Downloading: $(basename "$output")"

    if command -v curl &> /dev/null; then
        curl -L -o "$output" "$url" --progress-bar
    elif command -v wget &> /dev/null; then
        wget -O "$output" "$url" --show-progress
    else
        log_error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi
}

verify_checksum() {
    local file=$1
    local expected_checksum=$2

    if [ -z "$expected_checksum" ]; then
        log_warn "No checksum provided, skipping verification"
        return 0
    fi

    log_info "Verifying checksum for $(basename "$file")..."
    local actual_checksum=$(sha256sum "$file" | awk '{print $1}')

    if [ "$actual_checksum" == "$expected_checksum" ]; then
        log_info "Checksum verified ✓"
        return 0
    else
        log_error "Checksum mismatch!"
        log_error "Expected: $expected_checksum"
        log_error "Got:      $actual_checksum"
        return 1
    fi
}

download_ffmpeg() {
    log_info "Downloading FFmpeg binary for $ARCH_NAME..."

    local ffmpeg_url="${BINARY_BASE_URL}/${VERSION}/ffmpeg-${ARCH_NAME}.tar.gz"
    local ffmpeg_tar="/tmp/ffmpeg-${ARCH_NAME}.tar.gz"

    download_file "$ffmpeg_url" "$ffmpeg_tar"

    log_info "Extracting FFmpeg to $INSTALL_DIR/ffmpeg..."
    mkdir -p "$INSTALL_DIR/ffmpeg"
    tar -xzf "$ffmpeg_tar" -C "$INSTALL_DIR/ffmpeg" --strip-components=1

    # Create symlinks
    ln -sf "$INSTALL_DIR/ffmpeg/bin/ffmpeg" /usr/local/bin/ffmpeg
    ln -sf "$INSTALL_DIR/ffmpeg/bin/ffprobe" /usr/local/bin/ffprobe

    # Update library cache
    echo "$INSTALL_DIR/ffmpeg/lib" > /etc/ld.so.conf.d/streon-ffmpeg.conf
    ldconfig

    # Verify
    if "$INSTALL_DIR/ffmpeg/bin/ffmpeg" -version | grep -q "libsrt"; then
        log_info "FFmpeg with SRT support installed successfully!"
    else
        log_error "FFmpeg verification failed (SRT support not detected)"
        return 1
    fi

    rm -f "$ffmpeg_tar"
}

download_inferno() {
    log_info "Downloading Inferno AoIP binaries for $ARCH_NAME..."

    local inferno_url="${BINARY_BASE_URL}/${VERSION}/inferno-${ARCH_NAME}.tar.gz"
    local inferno_tar="/tmp/inferno-${ARCH_NAME}.tar.gz"

    download_file "$inferno_url" "$inferno_tar"

    log_info "Extracting Inferno to $INFERNO_DIR..."
    mkdir -p "$INFERNO_DIR"/{bin,config}
    tar -xzf "$inferno_tar" -C "$INFERNO_DIR" --strip-components=1

    # Set permissions
    chown -R root:audio "$INFERNO_DIR"
    chmod +x "$INFERNO_DIR/bin/"*

    # Verify binaries
    if [ -f "$INFERNO_DIR/bin/statime" ] && [ -f "$INFERNO_DIR/bin/inferno" ] && [ -f "$INFERNO_DIR/lib/libasound_pcm_inferno.so" ]; then
        log_info "Inferno AoIP binaries installed successfully!"
        log_info "  - statime: $INFERNO_DIR/bin/statime"
        log_info "  - inferno2pipe: $INFERNO_DIR/bin/inferno2pipe"
        log_info "  - libasound_pcm_inferno.so: $INFERNO_DIR/lib/libasound_pcm_inferno.so"
    else
        log_error "Inferno verification failed (binaries not found)"
        return 1
    fi

    rm -f "$inferno_tar"
}

download_liquidsoap() {
    log_info "Downloading Liquidsoap 2.4.0 binary for $ARCH_NAME..."

    local liquidsoap_url="${BINARY_BASE_URL}/${VERSION}/liquidsoap-2.4.0-${ARCH_NAME}.tar.gz"
    local liquidsoap_tar="/tmp/liquidsoap-${ARCH_NAME}.tar.gz"

    download_file "$liquidsoap_url" "$liquidsoap_tar"

    log_info "Extracting Liquidsoap to $INSTALL_DIR/liquidsoap..."
    mkdir -p "$INSTALL_DIR/liquidsoap"
    tar -xzf "$liquidsoap_tar" -C "$INSTALL_DIR/liquidsoap" --strip-components=1

    # Create symlink
    ln -sf "$INSTALL_DIR/liquidsoap/bin/liquidsoap" /usr/local/bin/liquidsoap

    # Verify
    if "$INSTALL_DIR/liquidsoap/bin/liquidsoap" --version | grep -q "2.4.0"; then
        log_info "Liquidsoap 2.4.0 installed successfully!"
    else
        log_error "Liquidsoap verification failed"
        return 1
    fi

    rm -f "$liquidsoap_tar"
}

main() {
    check_root
    detect_architecture

    log_info "Starting binary download for Streon ${VERSION}..."
    echo ""

    # Ask user what to download
    read -p "Download FFmpeg with SRT? (Y/n): " -n 1 -r DOWNLOAD_FFMPEG
    echo
    DOWNLOAD_FFMPEG=${DOWNLOAD_FFMPEG:-y}

    read -p "Download Liquidsoap 2.4.0? (Y/n): " -n 1 -r DOWNLOAD_LIQUIDSOAP
    echo
    DOWNLOAD_LIQUIDSOAP=${DOWNLOAD_LIQUIDSOAP:-y}

    read -p "Download Inferno AoIP binaries? (Y/n): " -n 1 -r DOWNLOAD_INFERNO
    echo
    DOWNLOAD_INFERNO=${DOWNLOAD_INFERNO:-y}

    echo ""
    log_info "Proceeding with downloads..."

    # Create directories
    mkdir -p "$INSTALL_DIR"

    # Download components
    if [[ $DOWNLOAD_FFMPEG =~ ^[Yy]$ ]]; then
        download_ffmpeg || log_error "FFmpeg download failed"
    fi

    if [[ $DOWNLOAD_LIQUIDSOAP =~ ^[Yy]$ ]]; then
        download_liquidsoap || log_error "Liquidsoap download failed"
    fi

    if [[ $DOWNLOAD_INFERNO =~ ^[Yy]$ ]]; then
        download_inferno || log_error "Inferno download failed"
    fi

    echo ""
    log_info "Binary downloads complete!"
    log_info ""
    log_info "Note: This script downloaded pre-built binaries to speed up installation."
    log_info "If you prefer to build from source, use the individual build scripts instead."
}

main "$@"
