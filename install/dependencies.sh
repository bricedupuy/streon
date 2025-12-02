#!/bin/bash
# Install system dependencies for Streon on Debian 13

set -euo pipefail

log_info() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "This script must be run as root"
        exit 1
    fi
}

main() {
    check_root

    log_info "Updating package lists..."
    apt-get update

    log_info "Installing build tools..."
    apt-get install -y \
        build-essential \
        git \
        cmake \
        pkg-config \
        autoconf \
        automake \
        libtool \
        wget \
        curl \
        ca-certificates \
        gnupg

    log_info "Installing audio libraries..."
    apt-get install -y \
        libasound2-dev \
        libpulse-dev \
        libjack-jackd2-dev \
        libsamplerate0-dev \
        libmad0-dev \
        libfaad-dev

    log_info "Installing FFmpeg dependencies..."
    apt-get install -y \
        nasm \
        yasm \
        libx264-dev \
        libx265-dev \
        libvpx-dev \
        libopus-dev \
        libfdk-aac-dev \
        libmp3lame-dev \
        libvorbis-dev \
        libssl-dev \
        libpcre3-dev

    log_info "Installing SRT library..."
    apt-get install -y \
        libsrt-gnutls-dev \
        srt-tools

    log_info "Installing OCaml and OPAM (for Liquidsoap)..."
    apt-get install -y \
        opam \
        ocaml \
        libpcre3-dev \
        libssl-dev \
        libtaglib-ocaml-dev

    log_info "Installing Python 3.11+..."
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev

    log_info "Installing network tools..."
    apt-get install -y \
        net-tools \
        iproute2 \
        ethtool \
        tcpdump \
        iperf3

    log_info "Installing system utilities..."
    apt-get install -y \
        psmisc \
        procps \
        htop \
        tmux \
        jq \
        rsync

    log_info "Installing Node.js (for Web UI build)..."
    # Install Node.js 20.x LTS
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs

    log_info "Cleaning up..."
    apt-get autoremove -y
    apt-get clean

    log_info "Dependencies installation complete!"
}

main "$@"
