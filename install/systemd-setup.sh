#!/bin/bash
# Install systemd service files for Streon

set -euo pipefail

SERVICES_DIR="$(dirname "$(dirname "$0")")/services"
SYSTEMD_DIR="/etc/systemd/system"

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

install_service() {
    local service_file=$1
    local service_name=$(basename "$service_file")

    log_info "Installing service: $service_name"
    cp "$service_file" "$SYSTEMD_DIR/"
    chmod 644 "$SYSTEMD_DIR/$service_name"
}

main() {
    check_root

    if [ ! -d "$SERVICES_DIR" ]; then
        log_error "Services directory not found: $SERVICES_DIR"
        exit 1
    fi

    log_info "Installing Streon systemd services..."

    # Install all service files
    for service in "$SERVICES_DIR"/*.service; do
        install_service "$service"
    done

    # Reload systemd daemon
    log_info "Reloading systemd daemon..."
    systemctl daemon-reload

    # Enable core services (but don't start them yet)
    log_info "Enabling core services..."
    systemctl enable streon-controller.service

    # Enable Inferno services if they exist and are configured
    if systemctl list-unit-files | grep -q "statime.service"; then
        log_info "Inferno AoIP services detected (not enabled by default)"
        log_info "  To enable: sudo systemctl enable statime inferno"
    fi

    log_info "Systemd services installed successfully!"
    log_info ""
    log_info "Installed services:"
    log_info "  - streon-controller.service (enabled)"
    log_info "  - streon-gpio-daemon.service"
    log_info "  - liquidsoap@.service (template)"
    log_info "  - ffmpeg-srt-encoder@.service (template)"
    log_info "  - ffmpeg-srt-decoder@.service (template)"
    log_info "  - statime.service (if Inferno installed)"
    log_info "  - inferno.service (if Inferno installed)"
    log_info ""
    log_info "To start the controller:"
    log_info "  sudo systemctl start streon-controller"
}

main "$@"
