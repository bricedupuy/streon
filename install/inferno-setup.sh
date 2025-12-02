#!/bin/bash
# Install and configure Inferno AoIP for Dante/AES67 support

set -euo pipefail

DANTE_NIC="${1:-eth1}"
CONTROL_NIC="${2:-eth0}"
INFERNO_DIR="/opt/inferno"
BUILD_DIR="/tmp/inferno-build"

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

verify_network_interface() {
    local iface=$1
    if ! ip link show "$iface" &> /dev/null; then
        log_error "Network interface $iface does not exist"
        log_info "Available interfaces:"
        ip -o link show | awk '{print "  - " $2}' | sed 's/://'
        exit 1
    fi
}

install_rust() {
    log_info "Installing Rust compiler (required for Inferno)..."

    # Install Rust via rustup for system-wide use
    if ! command -v rustc &> /dev/null; then
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
        source "$HOME/.cargo/env"
    else
        log_info "Rust already installed"
    fi
}

main() {
    check_root
    verify_network_interface "$DANTE_NIC"
    verify_network_interface "$CONTROL_NIC"

    log_info "Installing Inferno AoIP..."
    log_info "  Dante NIC: $DANTE_NIC"
    log_info "  Control NIC: $CONTROL_NIC"

    # Install Rust
    install_rust

    # Clean previous build
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"

    # Clone Inferno repository
    log_info "Cloning Inferno repository..."
    git clone https://gitlab.com/lumifaza/inferno.git
    cd inferno

    # Build statime (PTP daemon)
    log_info "Building statime PTP daemon..."
    cd statime
    cargo build --release --bin statime
    cd ..

    # Build inferno daemon
    log_info "Building inferno daemon..."
    cd inferno
    cargo build --release
    cd ..

    # Install binaries
    log_info "Installing Inferno binaries to $INFERNO_DIR..."
    mkdir -p "$INFERNO_DIR"/{bin,config}

    cp statime/target/release/statime "$INFERNO_DIR/bin/"
    cp inferno/target/release/inferno "$INFERNO_DIR/bin/"

    # Create configuration files
    log_info "Creating Inferno configuration files..."

    # statime PTP configuration (PTPv1 for Dante compatibility)
    cat > "$INFERNO_DIR/config/inferno-ptpv1.toml" <<EOF
# Statime PTP Configuration for Dante (PTPv1)
# Dante uses PTPv1 (IEEE 1588-2002)

[interface]
name = "$DANTE_NIC"

[ptp]
domain = 0
priority1 = 128
priority2 = 128

# Dante uses PTPv1 (delay request-response)
version = 1
delay_mechanism = "E2E"  # End-to-End delay measurement

# Sync interval (Dante typically uses 1 packet/sec = 0)
log_sync_interval = 0
log_announce_interval = 1
log_min_delay_req_interval = 0

# Hardware timestamping (if supported by NIC)
timestamping = "hardware"
EOF

    # Inferno AoIP configuration
    cat > "$INFERNO_DIR/config/inferno.toml" <<EOF
# Inferno AoIP Configuration

[network]
# Dante/AES67 network interface
interface = "$DANTE_NIC"

# Multicast base address for AES67 (Dante uses 239.x.x.x)
multicast_base = "239.69.0.0"

# Sample rate (48kHz standard for AES67/Dante)
sample_rate = 48000

# Bit depth
bit_depth = 24

# Audio packet time (1ms typical for Dante)
packet_time_us = 1000

[streams]
# Receive streams configuration
# Inferno will create ALSA devices: hw:InfernoStream0, hw:InfernoStream1, etc.
max_rx_streams = 8

# Transmit streams configuration
# Inferno will create ALSA devices: hw:InfernoTx0, hw:InfernoTx1, etc.
max_tx_streams = 8

[qos]
# DSCP marking for audio packets (EF = Expedited Forwarding)
dscp = 46

# Use VLAN priority tagging if available
vlan_priority = 5

[buffer]
# Buffer size in microseconds (lower = lower latency, but less jitter tolerance)
rx_buffer_us = 5000
tx_buffer_us = 2000

[logging]
level = "info"
EOF

    # Set permissions
    chown -R root:audio "$INFERNO_DIR"
    chmod +x "$INFERNO_DIR/bin/"*
    chmod 644 "$INFERNO_DIR/config/"*

    # Configure network interface for Dante
    log_info "Configuring network interface for Dante/AES67..."

    # Enable multicast on the Dante interface
    ip link set "$DANTE_NIC" multicast on
    ip link set "$DANTE_NIC" up

    # Set MTU to 1500 (standard for Dante)
    ip link set "$DANTE_NIC" mtu 1500

    # Add multicast route for AES67/Dante
    ip route add 239.69.0.0/16 dev "$DANTE_NIC" 2>/dev/null || true

    # Enable hardware timestamping (if supported)
    ethtool -K "$DANTE_NIC" rx-timestamping on tx-timestamping on 2>/dev/null || log_info "Hardware timestamping not supported by $DANTE_NIC"

    # Verify installation
    log_info "Verifying Inferno installation..."
    if [ -f "$INFERNO_DIR/bin/inferno" ] && [ -f "$INFERNO_DIR/bin/statime" ]; then
        log_info "Inferno AoIP installed successfully!"
        log_info "Binaries:"
        log_info "  - statime: $INFERNO_DIR/bin/statime"
        log_info "  - inferno: $INFERNO_DIR/bin/inferno"
        log_info "Configuration:"
        log_info "  - PTP config: $INFERNO_DIR/config/inferno-ptpv1.toml"
        log_info "  - Inferno config: $INFERNO_DIR/config/inferno.toml"
    else
        log_error "Inferno installation verification failed"
        exit 1
    fi

    # Cleanup
    log_info "Cleaning up build directory..."
    cd /
    rm -rf "$BUILD_DIR"

    log_info "Inferno setup complete!"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Review and customize configs in $INFERNO_DIR/config/"
    log_info "  2. Start services: sudo systemctl start statime inferno"
    log_info "  3. Check PTP sync: journalctl -u statime -f"
}

main "$@"
