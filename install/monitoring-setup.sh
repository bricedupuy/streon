#!/bin/bash
# Install and configure Prometheus + Grafana monitoring stack

set -euo pipefail

MONITORING_DIR="/opt/streon/monitoring"
PROMETHEUS_VERSION="2.47.0"
GRAFANA_VERSION="10.2.0"

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

install_prometheus() {
    log_info "Installing Prometheus $PROMETHEUS_VERSION..."

    # Install via apt (easier than building from source)
    apt-get install -y prometheus prometheus-node-exporter

    # Create Prometheus configuration
    log_info "Configuring Prometheus..."

    cat > /etc/prometheus/prometheus.yml <<EOF
# Prometheus Configuration for Streon

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'streon'
    environment: 'production'

# Alerting configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093

# Load alert rules
rule_files:
  - "/etc/prometheus/alerts.yml"

# Scrape configurations
scrape_configs:
  # Streon Controller metrics
  - job_name: 'streon-controller'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/system/metrics'

  # Node Exporter (system metrics)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

    # Create alert rules
    cat > /etc/prometheus/alerts.yml <<EOF
# Prometheus Alert Rules for Streon

groups:
  - name: streon_alerts
    interval: 30s
    rules:
      # Flow down alert
      - alert: FlowDown
        expr: streon_flow_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Flow {{ \$labels.flow }} is down"
          description: "Flow {{ \$labels.flow }} has been down for more than 1 minute"

      # Silence detection
      - alert: ProgramSilence
        expr: streon_program_silence_seconds > 10
        for: 30s
        labels:
          severity: warning
        annotations:
          summary: "Silence detected in Flow {{ \$labels.flow }}"
          description: "Flow {{ \$labels.flow }} has been silent for {{ \$value }} seconds"

      # SRT packet loss
      - alert: HighSRTPacketLoss
        expr: streon_srt_packet_loss_ratio > 0.001
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High SRT packet loss in Flow {{ \$labels.flow }}"
          description: "SRT output {{ \$labels.output }} has {{ \$value }}% packet loss"

      # SRT high latency
      - alert: HighSRTLatency
        expr: streon_srt_rtt_ms > 500
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High SRT latency in Flow {{ \$labels.flow }}"
          description: "SRT RTT is {{ \$value }}ms (threshold: 500ms)"

      # Inferno PTP sync lost
      - alert: InfernoPTPSyncLost
        expr: streon_inferno_ptp_synced == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Inferno PTP sync lost"
          description: "Interface {{ \$labels.iface }} has lost PTP synchronization"

      # Controller down
      - alert: ControllerDown
        expr: streon_controller_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Streon controller is down"
          description: "The Streon controller has been unreachable for more than 1 minute"
EOF

    # Set permissions
    chown -R prometheus:prometheus /etc/prometheus

    # Enable and start Prometheus
    systemctl enable prometheus
    systemctl restart prometheus

    log_info "Prometheus installed and configured"
}

install_grafana() {
    log_info "Installing Grafana $GRAFANA_VERSION..."

    # Add Grafana repository (using modern approach instead of deprecated apt-key)
    apt-get install -y software-properties-common
    mkdir -p /etc/apt/keyrings
    wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor -o /etc/apt/keyrings/grafana.gpg
    echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list

    apt-get update
    apt-get install -y grafana

    # Configure Grafana
    log_info "Configuring Grafana..."

    # Enable Prometheus datasource
    mkdir -p /etc/grafana/provisioning/datasources
    cat > /etc/grafana/provisioning/datasources/prometheus.yml <<EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: false
EOF

    # Import Streon dashboards
    log_info "Installing Streon Grafana dashboards..."
    mkdir -p /etc/grafana/provisioning/dashboards

    cat > /etc/grafana/provisioning/dashboards/streon.yml <<EOF
apiVersion: 1

providers:
  - name: 'Streon Dashboards'
    orgId: 1
    folder: 'Streon'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards/streon
EOF

    mkdir -p /var/lib/grafana/dashboards/streon
    chown -R grafana:grafana /var/lib/grafana/dashboards

    # Enable and start Grafana
    systemctl enable grafana-server
    systemctl restart grafana-server

    log_info "Grafana installed and configured"
}

main() {
    check_root

    log_info "Setting up monitoring stack..."

    install_prometheus
    install_grafana

    log_info "Monitoring setup complete!"
    log_info ""
    log_info "Access points:"
    log_info "  - Prometheus: http://localhost:9090"
    log_info "  - Grafana: http://localhost:3000 (admin/admin)"
    log_info "  - Node Exporter: http://localhost:9100/metrics"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Access Grafana and change the default password"
    log_info "  2. Import Streon dashboards from /var/lib/grafana/dashboards/streon"
    log_info "  3. Configure alert notifications in Grafana"
}

main "$@"
