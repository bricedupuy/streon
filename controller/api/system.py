"""System API endpoints"""

from fastapi import APIRouter, Response
import psutil
from datetime import datetime
import logging

from models.config import SystemHealth
from monitoring.prometheus import metrics_collector

logger = logging.getLogger(__name__)

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

        # TODO: Check Inferno status
        inferno_up = None
        ptp_synced = None

        # TODO: Count active Flows
        active_flows = 0

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
