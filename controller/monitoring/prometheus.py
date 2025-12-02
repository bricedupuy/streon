"""
Prometheus Metrics Exporter for Streon
Collects and exposes metrics for all Flows, Dante integration, and system health
"""

import logging
import psutil
from typing import Dict
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)

logger = logging.getLogger(__name__)


class StreonMetricsCollector:
    """Collects and exposes Prometheus metrics for Streon"""

    def __init__(self):
        self.registry = CollectorRegistry()

        # Flow status metrics
        self.flow_up = Gauge(
            'streon_flow_up',
            'Flow status (1=running, 0=stopped)',
            ['flow'],
            registry=self.registry
        )

        # Audio level metrics
        self.audio_peak_dbfs = Gauge(
            'streon_audio_peak_dbfs',
            'Peak audio level in dBFS',
            ['flow', 'channel'],
            registry=self.registry
        )

        self.audio_rms_dbfs = Gauge(
            'streon_audio_rms_dbfs',
            'RMS audio level in dBFS',
            ['flow', 'channel'],
            registry=self.registry
        )

        # Silence detection
        self.program_silence_seconds = Gauge(
            'streon_program_silence_seconds',
            'Duration of current silence in seconds',
            ['flow'],
            registry=self.registry
        )

        # SRT transport metrics
        self.srt_rtt_ms = Gauge(
            'streon_srt_rtt_ms',
            'SRT round-trip time in milliseconds',
            ['flow', 'output'],
            registry=self.registry
        )

        self.srt_packet_loss_ratio = Gauge(
            'streon_srt_packet_loss_ratio',
            'SRT packet loss ratio',
            ['flow', 'output'],
            registry=self.registry
        )

        self.srt_bitrate_kbps = Gauge(
            'streon_srt_bitrate_kbps',
            'SRT bitrate in kbps',
            ['flow', 'output'],
            registry=self.registry
        )

        self.srt_reconnections_total = Counter(
            'streon_srt_reconnections_total',
            'Total SRT reconnections',
            ['flow', 'output'],
            registry=self.registry
        )

        # GPIO event metrics
        self.gpio_events_total = Counter(
            'streon_gpio_events_total',
            'Total GPIO events',
            ['flow', 'direction', 'type'],
            registry=self.registry
        )

        # Metadata metrics
        self.metadata_updates_total = Counter(
            'streon_metadata_updates_total',
            'Total metadata updates',
            ['flow'],
            registry=self.registry
        )

        # Dante AoIP metrics
        self.dante_ptp_synced = Gauge(
            'streon_dante_ptp_synced',
            'Dante PTP sync status (1=synced, 0=not synced)',
            ['iface'],
            registry=self.registry
        )

        self.dante_ptp_offset_ns = Gauge(
            'streon_dante_ptp_offset_ns',
            'Dante PTP clock offset in nanoseconds',
            ['iface'],
            registry=self.registry
        )

        self.dante_stream_up = Gauge(
            'streon_dante_stream_up',
            'Dante stream status (1=up, 0=down)',
            ['stream'],
            registry=self.registry
        )

        self.dante_xruns_total = Counter(
            'streon_dante_xruns_total',
            'Total Dante XRUN events',
            ['stream'],
            registry=self.registry
        )

        self.dante_active_streams = Gauge(
            'streon_dante_active_streams',
            'Number of active Dante streams',
            registry=self.registry
        )

        self.dante_rx_packets_total = Counter(
            'streon_dante_rx_packets_total',
            'Total Dante RX packets',
            ['stream'],
            registry=self.registry
        )

        self.dante_tx_packets_total = Counter(
            'streon_dante_tx_packets_total',
            'Total Dante TX packets',
            ['stream'],
            registry=self.registry
        )

        # Device health metrics
        self.device_available = Gauge(
            'streon_device_available',
            'Device availability (1=available, 0=unavailable)',
            ['device'],
            registry=self.registry
        )

        self.device_xruns_total = Counter(
            'streon_device_xruns_total',
            'Total device XRUN events',
            ['device'],
            registry=self.registry
        )

        # System metrics
        self.controller_up = Gauge(
            'streon_controller_up',
            'Controller status (1=up, 0=down)',
            registry=self.registry
        )

        self.system_cpu_percent = Gauge(
            'streon_system_cpu_percent',
            'System CPU usage percentage',
            registry=self.registry
        )

        self.system_memory_percent = Gauge(
            'streon_system_memory_percent',
            'System memory usage percentage',
            registry=self.registry
        )

        self.system_disk_percent = Gauge(
            'streon_system_disk_percent',
            'System disk usage percentage',
            ['mount'],
            registry=self.registry
        )

        # Flow process metrics
        self.flow_cpu_percent = Gauge(
            'streon_flow_cpu_percent',
            'Flow CPU usage percentage',
            ['flow', 'process'],
            registry=self.registry
        )

        self.flow_memory_mb = Gauge(
            'streon_flow_memory_mb',
            'Flow memory usage in MB',
            ['flow', 'process'],
            registry=self.registry
        )

        # Mark controller as up
        self.controller_up.set(1)

        logger.info("Prometheus metrics collector initialized")

    def update_flow_status(self, flow_id: str, is_running: bool):
        """Update Flow status metric"""
        self.flow_up.labels(flow=flow_id).set(1 if is_running else 0)

    def update_audio_levels(self, flow_id: str, left_peak: float, right_peak: float,
                           left_rms: float, right_rms: float):
        """Update audio level metrics"""
        self.audio_peak_dbfs.labels(flow=flow_id, channel='left').set(left_peak)
        self.audio_peak_dbfs.labels(flow=flow_id, channel='right').set(right_peak)
        self.audio_rms_dbfs.labels(flow=flow_id, channel='left').set(left_rms)
        self.audio_rms_dbfs.labels(flow=flow_id, channel='right').set(right_rms)

    def update_silence_duration(self, flow_id: str, duration_seconds: float):
        """Update silence detection metric"""
        self.program_silence_seconds.labels(flow=flow_id).set(duration_seconds)

    def update_srt_stats(self, flow_id: str, output_name: str, rtt_ms: float,
                        packet_loss: float, bitrate_kbps: float):
        """Update SRT transport metrics"""
        self.srt_rtt_ms.labels(flow=flow_id, output=output_name).set(rtt_ms)
        self.srt_packet_loss_ratio.labels(flow=flow_id, output=output_name).set(packet_loss)
        self.srt_bitrate_kbps.labels(flow=flow_id, output=output_name).set(bitrate_kbps)

    def increment_srt_reconnection(self, flow_id: str, output_name: str):
        """Increment SRT reconnection counter"""
        self.srt_reconnections_total.labels(flow=flow_id, output=output_name).inc()

    def increment_gpio_event(self, flow_id: str, direction: str, event_type: str):
        """Increment GPIO event counter"""
        self.gpio_events_total.labels(flow=flow_id, direction=direction, type=event_type).inc()

    def increment_metadata_update(self, flow_id: str):
        """Increment metadata update counter"""
        self.metadata_updates_total.labels(flow=flow_id).inc()

    def update_dante_ptp_status(self, iface: str, synced: bool, offset_ns: int):
        """Update Dante PTP synchronization metrics"""
        self.dante_ptp_synced.labels(iface=iface).set(1 if synced else 0)
        self.dante_ptp_offset_ns.labels(iface=iface).set(offset_ns)

    def update_dante_stream_status(self, stream_name: str, is_up: bool):
        """Update Dante stream status"""
        self.dante_stream_up.labels(stream=stream_name).set(1 if is_up else 0)

    def increment_dante_xrun(self, stream_name: str):
        """Increment Dante XRUN counter"""
        self.dante_xruns_total.labels(stream=stream_name).inc()

    def update_dante_active_streams(self, count: int):
        """Update active Dante streams count"""
        self.dante_active_streams.set(count)

    def increment_dante_rx_packets(self, stream_name: str, count: int = 1):
        """Increment Dante RX packet counter"""
        self.dante_rx_packets_total.labels(stream=stream_name).inc(count)

    def increment_dante_tx_packets(self, stream_name: str, count: int = 1):
        """Increment Dante TX packet counter"""
        self.dante_tx_packets_total.labels(stream=stream_name).inc(count)

    def update_device_status(self, device_id: str, available: bool):
        """Update device availability"""
        self.device_available.labels(device=device_id).set(1 if available else 0)

    def increment_device_xrun(self, device_id: str):
        """Increment device XRUN counter"""
        self.device_xruns_total.labels(device=device_id).inc()

    def update_system_metrics(self):
        """Update system-level metrics using psutil"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_percent.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_percent.set(memory.percent)

            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_disk_percent.labels(mount='/').set(disk.percent)

        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")

    def update_flow_process_metrics(self, flow_id: str, liquidsoap_pid: int = None,
                                   ffmpeg_pids: list[int] = None):
        """Update Flow process metrics"""
        try:
            if liquidsoap_pid:
                try:
                    proc = psutil.Process(liquidsoap_pid)
                    cpu = proc.cpu_percent(interval=0.1)
                    mem_mb = proc.memory_info().rss / 1024 / 1024

                    self.flow_cpu_percent.labels(flow=flow_id, process='liquidsoap').set(cpu)
                    self.flow_memory_mb.labels(flow=flow_id, process='liquidsoap').set(mem_mb)
                except psutil.NoSuchProcess:
                    pass

            if ffmpeg_pids:
                for idx, pid in enumerate(ffmpeg_pids):
                    try:
                        proc = psutil.Process(pid)
                        cpu = proc.cpu_percent(interval=0.1)
                        mem_mb = proc.memory_info().rss / 1024 / 1024

                        self.flow_cpu_percent.labels(flow=flow_id, process=f'ffmpeg_{idx}').set(cpu)
                        self.flow_memory_mb.labels(flow=flow_id, process=f'ffmpeg_{idx}').set(mem_mb)
                    except psutil.NoSuchProcess:
                        pass

        except Exception as e:
            logger.error(f"Failed to update Flow process metrics for {flow_id}: {e}")

    def generate_metrics(self) -> bytes:
        """Generate Prometheus metrics in text format"""
        return generate_latest(self.registry)

    def get_content_type(self) -> str:
        """Get Prometheus metrics content type"""
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
metrics_collector = StreonMetricsCollector()
