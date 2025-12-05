"""System API endpoints"""

from fastapi import APIRouter, Response
import psutil
import subprocess
from datetime import datetime
import logging
from pathlib import Path

from models.config import SystemHealth
from monitoring.prometheus import metrics_collector
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


def check_inferno_status() -> tuple[bool, bool]:
    """
    Check Inferno daemon status and PTP sync.
    Returns (inferno_up, ptp_synced)
    """
    try:
        # Check if inferno service is running
        result = subprocess.run(
            ['systemctl', 'is-active', 'inferno'],
            capture_output=True, text=True, timeout=5
        )
        inferno_up = result.returncode == 0

        # Check PTP sync status via statime
        ptp_synced = False
        if inferno_up:
            try:
                # Read statime status file or check via socket
                statime_status = Path('/run/statime/status')
                if statime_status.exists():
                    status_text = statime_status.read_text()
                    ptp_synced = 'SLAVE' in status_text or 'MASTER' in status_text
            except Exception:
                pass

        return inferno_up, ptp_synced

    except Exception as e:
        logger.debug(f"Error checking Inferno status: {e}")
        return None, None


def count_active_flows() -> int:
    """Count number of running Flow processes"""
    try:
        config_mgr = ConfigManager()
        flow_ids = config_mgr.list_flows()

        active_count = 0
        for flow_id in flow_ids:
            # Check if liquidsoap process exists for this flow
            try:
                result = subprocess.run(
                    ['pgrep', '-f', f'liquidsoap.*{flow_id}'],
                    capture_output=True, timeout=2
                )
                if result.returncode == 0:
                    active_count += 1
            except Exception:
                pass

        return active_count
    except Exception as e:
        logger.debug(f"Error counting active flows: {e}")
        return 0

router = APIRouter()


@router.get("/system/health", response_model=SystemHealth)
async def get_system_health():
    """
    Get system health status

    Returns overall system health including CPU, memory, disk usage,
    and status of Inferno and active Flows
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Check Inferno/PTP status
        inferno_up, ptp_synced = check_inferno_status()

        # Count active Flows
        active_flows = count_active_flows()

        health = SystemHealth(
            controller_up=True,
            inferno_up=inferno_up,
            ptp_synced=ptp_synced,
            active_flows=active_flows,
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory.percent,
            disk_usage_percent=disk.percent
        )

        return health

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return SystemHealth(
            controller_up=True,
            inferno_up=None,
            ptp_synced=None,
            active_flows=0,
            cpu_usage_percent=0.0,
            memory_usage_percent=0.0,
            disk_usage_percent=0.0
        )


@router.get("/system/metrics")
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus format for scraping by Prometheus server
    """
    # Update system metrics before generating output
    metrics_collector.update_system_metrics()

    # Generate metrics in Prometheus text format
    metrics_data = metrics_collector.generate_metrics()

    return Response(
        content=metrics_data,
        media_type=metrics_collector.get_content_type()
    )


@router.get("/system/logs")
async def get_system_logs(lines: int = 100):
    """
    Get recent system logs

    - **lines**: Number of log lines to return
    """
    # TODO: Implement log retrieval
    return {"note": "System logs not yet implemented", "lines": lines}
