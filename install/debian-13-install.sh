#!/bin/bash
# Streon Master Installation Script for Debian 13
# Installs all components of the Streon multi-Flow audio transport system

set -euo pipefail

INSTALL_DIR="/opt/streon"
CONFIG_DIR="/etc/streon"
LOG_DIR="/var/log/streon"
USER="streon"
GROUP="streon"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

check_debian_version() {
    if [ ! -f /etc/debian_version ]; then
        log_error "This script is designed for Debian 13"
        exit 1
    fi

    DEBIAN_VERSION=$(cat /etc/debian_version | cut -d'.' -f1)
    if [ "$DEBIAN_VERSION" != "13" ]; then
        log_warn "This script is designed for Debian 13, you have Debian $DEBIAN_VERSION"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

detect_architecture() {
    ARCH=$(uname -m)
    log_info "Detected architecture: $ARCH"

    if [[ "$ARCH" != "x86_64" && "$ARCH" != "aarch64" ]]; then
        log_error "Unsupported architecture: $ARCH (supported: x86_64, aarch64)"
        exit 1
    fi
}

create_user() {
    if id "$USER" &>/dev/null; then
        log_info "User $USER already exists"
    else
        log_info "Creating user: $USER"
        useradd -r -s /bin/bash -d "$INSTALL_DIR" -G audio "$USER"
    fi
}

create_directories() {
    log_info "Creating directory structure..."

    mkdir -p "$INSTALL_DIR"/{liquidsoap,ffmpeg,flows,controller,data}
    mkdir -p "$INSTALL_DIR"/liquidsoap/{templates,lib,stereotool/{presets,licenses}}
    mkdir -p "$CONFIG_DIR"/{flows,inferno,network,monitoring}
    mkdir -p "$LOG_DIR"

    chown -R "$USER:$GROUP" "$INSTALL_DIR"
    chown -R "$USER:$GROUP" "$CONFIG_DIR"
    chown -R "$USER:$GROUP" "$LOG_DIR"
}

banner() {
    echo ""
    echo "========================================="
    echo "   Streon Installation Script"
    echo "   Professional Multi-Flow Audio System"
    echo "========================================="
    echo ""
}

prompt_configuration() {
    echo ""
    log_info "Configuration Options:"
    echo ""

    read -p "Use pre-built binaries? (Faster installation) (Y/n): " -n 1 -r USE_BINARIES
    echo
    USE_BINARIES=${USE_BINARIES:-y}

    read -p "Install Inferno AoIP (Dante/AES67 support)? (y/N): " -n 1 -r INSTALL_INFERNO
    echo
    INSTALL_INFERNO=${INSTALL_INFERNO:-n}

    if [[ $INSTALL_INFERNO =~ ^[Yy]$ ]]; then
        echo ""
        echo "Available network interfaces:"
        ip -o link show | awk '{print $2}' | sed 's/://'
        echo ""
        read -p "Enter Dante network interface (e.g., eth1): " DANTE_NIC
        DANTE_NIC=${DANTE_NIC:-eth1}

        read -p "Enter control network interface (e.g., eth0): " CONTROL_NIC
        CONTROL_NIC=${CONTROL_NIC:-eth0}
    fi

    echo ""
    read -p "Install Prometheus + Grafana monitoring? (Y/n): " -n 1 -r INSTALL_MONITORING
    echo
    INSTALL_MONITORING=${INSTALL_MONITORING:-y}

    echo ""
    log_info "Installation will proceed with:"
    echo "  - Install directory: $INSTALL_DIR"
    echo "  - Config directory: $CONFIG_DIR"
    echo "  - User: $USER"
    echo "  - Use pre-built binaries: $([ "$USE_BINARIES" == "y" ] || [ "$USE_BINARIES" == "Y" ] && echo 'Yes (faster)' || echo 'No (build from source)')"
    echo "  - Inferno AoIP: $([ "$INSTALL_INFERNO" == "y" ] || [ "$INSTALL_INFERNO" == "Y" ] && echo 'Yes' || echo 'No')"
    if [[ $INSTALL_INFERNO =~ ^[Yy]$ ]]; then
        echo "    - Dante NIC: $DANTE_NIC"
        echo "    - Control NIC: $CONTROL_NIC"
    fi
    echo "  - Monitoring: $([ "$INSTALL_MONITORING" == "y" ] || [ "$INSTALL_MONITORING" == "Y" ] && echo 'Yes' || echo 'No')"
    echo ""

    read -p "Continue with installation? (Y/n): " -n 1 -r CONTINUE
    echo
    CONTINUE=${CONTINUE:-y}

    if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
        log_info "Installation cancelled"
        exit 0
    fi
}

main() {
    banner
    check_root
    check_debian_version
    detect_architecture
    prompt_configuration

    log_info "Starting installation..."

    # Phase 1: System dependencies
    log_info "Phase 1/8: Installing system dependencies..."
    bash "$(dirname "$0")/dependencies.sh"

    # Phase 2-4: Install binaries (pre-built or build from source)
    if [[ $USE_BINARIES =~ ^[Yy]$ ]]; then
        log_info "Phase 2/8: Downloading pre-built binaries (faster)..."

        # Download FFmpeg
        log_info "  - Downloading FFmpeg..."
        export DOWNLOAD_FFMPEG=y
        export DOWNLOAD_LIQUIDSOAP=y
        export DOWNLOAD_INFERNO=$([ "$INSTALL_INFERNO" == "y" ] || [ "$INSTALL_INFERNO" == "Y" ] && echo 'y' || echo 'n')
        bash "$(dirname "$0")/download-binaries.sh" "$INSTALL_DIR"

        log_info "Phase 3/8: Skipped (using pre-built binaries)"
        log_info "Phase 4/8: Skipped (using pre-built binaries)"
    else
        log_info "Phase 2/8: Building Liquidsoap 2.4.0 from source..."
        bash "$(dirname "$0")/liquidsoap-build.sh" "$INSTALL_DIR"

        log_info "Phase 3/8: Building FFmpeg with SRT support from source..."
        bash "$(dirname "$0")/ffmpeg-build.sh" "$INSTALL_DIR"

        if [[ $INSTALL_INFERNO =~ ^[Yy]$ ]]; then
            log_info "Phase 4/8: Building Inferno AoIP from source..."
            bash "$(dirname "$0")/inferno-setup.sh" "$DANTE_NIC" "$CONTROL_NIC"
        else
            log_info "Phase 4/8: Skipping Inferno AoIP installation"
        fi
    fi

    # Phase 5: Python controller
    log_info "Phase 5/8: Setting up Python controller..."
    create_user
    create_directories

    cd "$INSTALL_DIR/controller"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate

    # Phase 6: Systemd services
    log_info "Phase 6/8: Installing systemd services..."
    bash "$(dirname "$0")/systemd-setup.sh"

    # Phase 7: Monitoring (optional)
    if [[ $INSTALL_MONITORING =~ ^[Yy]$ ]]; then
        log_info "Phase 7/8: Setting up Prometheus + Grafana..."
        bash "$(dirname "$0")/monitoring-setup.sh"
    else
        log_info "Phase 7/8: Skipping monitoring installation"
    fi

    # Phase 8: Initial configuration
    log_info "Phase 8/8: Creating initial configuration..."

    cat > "$CONFIG_DIR/streon.yaml" <<EOF
# Streon Global Configuration
version: "1.0.0"
install_dir: "$INSTALL_DIR"
config_dir: "$CONFIG_DIR"
log_dir: "$LOG_DIR"

controller:
  host: "0.0.0.0"
  port: 8000
  workers: 4

monitoring:
  prometheus_enabled: $([ "$INSTALL_MONITORING" == "y" ] || [ "$INSTALL_MONITORING" == "Y" ] && echo 'true' || echo 'false')
  metrics_port: 9090

inferno:
  enabled: $([ "$INSTALL_INFERNO" == "y" ] || [ "$INSTALL_INFERNO" == "Y" ] && echo 'true' || echo 'false')
EOF

    if [[ $INSTALL_INFERNO =~ ^[Yy]$ ]]; then
        cat >> "$CONFIG_DIR/streon.yaml" <<EOF
  dante_interface: "$DANTE_NIC"
  control_interface: "$CONTROL_NIC"
EOF
    fi

    chown "$USER:$GROUP" "$CONFIG_DIR/streon.yaml"

    log_info "Installation complete!"
    echo ""
    echo "========================================="
    echo "Next Steps:"
    echo "========================================="
    echo "1. Start the controller:"
    echo "   sudo systemctl start streon-controller"
    echo ""
    echo "2. Access the Web UI:"
    echo "   http://localhost:8000"
    echo ""
    echo "3. Create your first Flow:"
    echo "   $INSTALL_DIR/scripts/flow-create.sh my_first_flow"
    echo ""
    if [[ $INSTALL_MONITORING =~ ^[Yy]$ ]]; then
        echo "4. Access Grafana:"
        echo "   http://localhost:3000 (admin/admin)"
        echo ""
    fi
    echo "For documentation, visit:"
    echo "https://github.com/bricedupuy/streon"
    echo "========================================="
}

main "$@"
