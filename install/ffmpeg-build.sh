#!/bin/bash
# Build and install FFmpeg with SRT support

set -euo pipefail

INSTALL_DIR="${1:-/opt/streon}"
FFMPEG_VERSION="6.1"
BUILD_DIR="/tmp/ffmpeg-build"

log_info() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

main() {
    check_root

    log_info "Building FFmpeg $FFMPEG_VERSION with SRT support..."

    # Clean previous build
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"

    # Download FFmpeg source
    log_info "Downloading FFmpeg source..."
    wget "https://ffmpeg.org/releases/ffmpeg-${FFMPEG_VERSION}.tar.xz"
    tar -xf "ffmpeg-${FFMPEG_VERSION}.tar.xz"
    cd "ffmpeg-${FFMPEG_VERSION}"

    # Configure FFmpeg with all required features
    log_info "Configuring FFmpeg..."
    ./configure \
        --prefix="$INSTALL_DIR/ffmpeg" \
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
        --enable-demuxer=srt \
        --enable-muxer=srt \
        --enable-openssl \
        --enable-shared \
        --disable-static \
        --disable-doc \
        --disable-ffplay \
        --extra-cflags="-I/usr/include" \
        --extra-ldflags="-L/usr/lib"

    # Build FFmpeg (use all CPU cores)
    log_info "Building FFmpeg (this may take 20-30 minutes)..."
    NPROC=$(nproc)
    make -j"$NPROC"

    # Install FFmpeg
    log_info "Installing FFmpeg to $INSTALL_DIR/ffmpeg..."
    make install

    # Create symlinks in /usr/local/bin
    ln -sf "$INSTALL_DIR/ffmpeg/bin/ffmpeg" /usr/local/bin/ffmpeg
    ln -sf "$INSTALL_DIR/ffmpeg/bin/ffprobe" /usr/local/bin/ffprobe

    # Update library cache
    echo "$INSTALL_DIR/ffmpeg/lib" > /etc/ld.so.conf.d/streon-ffmpeg.conf
    ldconfig

    # Set permissions
    chown -R streon:streon "$INSTALL_DIR/ffmpeg"

    # Verify installation
    log_info "Verifying FFmpeg installation..."
    if "$INSTALL_DIR/ffmpeg/bin/ffmpeg" -version | grep -q "libsrt"; then
        log_info "FFmpeg $FFMPEG_VERSION with SRT support installed successfully!"
    else
        log_error "FFmpeg installation verification failed (SRT support not detected)"
        exit 1
    fi

    # Cleanup
    log_info "Cleaning up build directory..."
    cd /
    rm -rf "$BUILD_DIR"

    log_info "FFmpeg build complete!"
}

main "$@"
