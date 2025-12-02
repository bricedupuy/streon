#!/bin/bash
# Build and install Liquidsoap 2.4.0 from source

set -euo pipefail

INSTALL_DIR="${1:-/opt/streon}"
LIQUIDSOAP_VERSION="2.4.0"
BUILD_DIR="/tmp/liquidsoap-build"

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

    log_info "Building Liquidsoap $LIQUIDSOAP_VERSION..."

    # Clean previous build
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"

    # Initialize OPAM for Liquidsoap user
    log_info "Initializing OPAM environment..."

    # Create temporary user for OPAM initialization if needed
    export OPAMROOT=/opt/streon/.opam
    mkdir -p "$OPAMROOT"

    # Initialize OPAM (disable sandboxing for compatibility)
    opam init --disable-sandboxing -y --bare

    # Create OPAM switch for Liquidsoap
    log_info "Creating OPAM switch for OCaml..."
    opam switch create liquidsoap-2.4.0 ocaml-base-compiler.5.1.0 -y
    eval $(opam env --switch=liquidsoap-2.4.0)

    # Install Liquidsoap dependencies via OPAM
    log_info "Installing Liquidsoap dependencies via OPAM..."
    opam install -y \
        dune \
        menhir \
        sedlex \
        ppx_string \
        camomile \
        pcre \
        ssl \
        samplerate \
        mad \
        taglib \
        faad \
        cry \
        mm \
        ffmpeg \
        ogg \
        vorbis \
        opus \
        lame \
        fdkaac \
        alsa

    # Clone Liquidsoap repository
    log_info "Cloning Liquidsoap repository..."
    git clone https://github.com/savonet/liquidsoap.git
    cd liquidsoap
    git checkout "v${LIQUIDSOAP_VERSION}"

    # Build Liquidsoap
    log_info "Building Liquidsoap (this may take 10-20 minutes)..."
    eval $(opam env --switch=liquidsoap-2.4.0)
    make
    make install

    # Install to target directory
    log_info "Installing Liquidsoap to $INSTALL_DIR/liquidsoap..."
    mkdir -p "$INSTALL_DIR/liquidsoap/bin"

    # Find OPAM installation path
    OPAM_BIN=$(opam var bin)
    cp "$OPAM_BIN/liquidsoap" "$INSTALL_DIR/liquidsoap/bin/"

    # Create symlink in /usr/local/bin
    ln -sf "$INSTALL_DIR/liquidsoap/bin/liquidsoap" /usr/local/bin/liquidsoap

    # Set permissions
    chown -R streon:streon "$INSTALL_DIR/liquidsoap"
    chown -R streon:streon "$OPAMROOT"

    # Verify installation
    log_info "Verifying Liquidsoap installation..."
    if "$INSTALL_DIR/liquidsoap/bin/liquidsoap" --version; then
        log_info "Liquidsoap $LIQUIDSOAP_VERSION installed successfully!"
    else
        log_error "Liquidsoap installation verification failed"
        exit 1
    fi

    # Cleanup
    log_info "Cleaning up build directory..."
    cd /
    rm -rf "$BUILD_DIR"

    log_info "Liquidsoap build complete!"
}

main "$@"
