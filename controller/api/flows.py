"""Flow API endpoints"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import logging
import telnetlib
import subprocess

from models.flow import (
    FlowConfig,
    FlowStatus,
    FlowMetrics,
    FlowCreateRequest,
    FlowUpdateRequest
)

from core.flow_manager import FlowManager
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


def get_liquidsoap_audio_levels(flow_id: str, telnet_port: int = 1234) -> Optional[dict]:
    """Get audio levels from Liquidsoap telnet interface"""
    try:
        tn = telnetlib.Telnet('localhost', telnet_port, timeout=1)
        tn.write(b'var.get audio_peak_l\n')
        peak_l = float(tn.read_until(b'\n', timeout=1).decode().strip())
        tn.write(b'var.get audio_peak_r\n')
        peak_r = float(tn.read_until(b'\n', timeout=1).decode().strip())
        tn.close()
        return {'peak_l': peak_l, 'peak_r': peak_r}
    except Exception:
        return None


def get_srt_stats(flow_id: str) -> Optional[dict]:
    """Get SRT transport statistics from FFmpeg"""
    try:
        # SRT stats would typically come from parsing FFmpeg's stderr
        # or using the SRT library's stats API
        # For now, return None to indicate stats not available
        return None
    except Exception:
        return None

router = APIRouter()

# Initialize managers
flow_mgr = FlowManager()
config_mgr = ConfigManager()


@router.get("/flows", response_model=List[FlowConfig])
async def list_flows():
    """
    List all Flows

    Returns configuration for all Flows (running and stopped)
    """
    flow_ids = flow_mgr.list_flows()
    flows = []

    for flow_id in flow_ids:
        flow_config = config_mgr.load_flow_config(flow_id)
        if flow_config:
            flows.append(flow_config)

    return flows


@router.post("/flows", response_model=FlowConfig)
async def create_flow(request: FlowCreateRequest):
    """
    Create a new Flow

    - **request**: Flow configuration
    """
    try:
        flow_config = flow_mgr.create_flow(request.config)
        return flow_config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating Flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/{flow_id}", response_model=FlowConfig)
async def get_flow(flow_id: str):
    """
    Get Flow details

    - **flow_id**: Flow ID
    """
    flow_config = config_mgr.load_flow_config(flow_id)
    if not flow_config:
        raise HTTPException(status_code=404, detail="Flow not found")
    return flow_config


@router.put("/flows/{flow_id}", response_model=FlowConfig)
async def update_flow(flow_id: str, request: FlowUpdateRequest):
    """
    Update Flow configuration

    - **flow_id**: Flow ID
    - **request**: Updated configuration
    """
    try:
        flow_config = flow_mgr.update_flow(flow_id, request.config)
        return flow_config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating Flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/flows/{flow_id}")
async def delete_flow(flow_id: str):
    """
    Delete a Flow

    - **flow_id**: Flow ID to delete
    """
    try:
        flow_mgr.delete_flow(flow_id)
        return {"message": "Flow deleted successfully", "flow_id": flow_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting Flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/start")
async def start_flow(flow_id: str):
    """
    Start a Flow

    - **flow_id**: Flow ID to start
    """
    try:
        flow_mgr.start_flow(flow_id)
        return {"message": "Flow started successfully", "flow_id": flow_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting Flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/stop")
async def stop_flow(flow_id: str):
    """
    Stop a Flow

    - **flow_id**: Flow ID to stop
    """
    try:
        flow_mgr.stop_flow(flow_id)
        return {"message": "Flow stopped successfully", "flow_id": flow_id}
    except Exception as e:
        logger.error(f"Error stopping Flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/restart")
async def restart_flow(flow_id: str):
    """
    Restart a Flow

    - **flow_id**: Flow ID to restart
    """
    try:
        flow_mgr.restart_flow(flow_id)
        return {"message": "Flow restarted successfully", "flow_id": flow_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error restarting Flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/{flow_id}/status", response_model=FlowStatus)
async def get_flow_status(flow_id: str):
    """
    Get Flow runtime status

    - **flow_id**: Flow ID
    """
    # Verify Flow exists
    flow_config = config_mgr.load_flow_config(flow_id)
    if not flow_config:
        raise HTTPException(status_code=404, detail="Flow not found")

    status = flow_mgr.get_flow_status(flow_id)
    if not status:
        raise HTTPException(status_code=500, detail="Error getting Flow status")

    return status


@router.get("/flows/{flow_id}/metrics", response_model=FlowMetrics)
async def get_flow_metrics(flow_id: str):
    """
    Get Flow metrics

    - **flow_id**: Flow ID
    """
    # Verify Flow exists
    flow_config = config_mgr.load_flow_config(flow_id)
    if not flow_config:
        raise HTTPException(status_code=404, detail="Flow not found")

    # Get real audio levels from Liquidsoap
    audio_levels = get_liquidsoap_audio_levels(flow_id)
    peak_l = audio_levels['peak_l'] if audio_levels else -60.0
    peak_r = audio_levels['peak_r'] if audio_levels else -60.0

    # Determine if silent (below -50 dBFS)
    is_silent = peak_l < -50 and peak_r < -50

    # Get SRT stats if available
    srt_stats = get_srt_stats(flow_id)

    return FlowMetrics(
        flow_id=flow_id,
        audio_peak_left_dbfs=peak_l,
        audio_peak_right_dbfs=peak_r,
        is_silent=is_silent,
        srt_rtt_ms=srt_stats.get('rtt_ms') if srt_stats else None,
        srt_packet_loss=srt_stats.get('packet_loss') if srt_stats else None,
        srt_bitrate_kbps=srt_stats.get('bitrate_kbps') if srt_stats else None
    )


@router.get("/flows/{flow_id}/audio-levels")
async def get_flow_audio_levels(flow_id: str):
    """
    Get real-time audio levels for a Flow

    - **flow_id**: Flow ID
    """
    flow_config = config_mgr.load_flow_config(flow_id)
    if not flow_config:
        raise HTTPException(status_code=404, detail="Flow not found")

    audio_levels = get_liquidsoap_audio_levels(flow_id)
    if audio_levels:
        return {
            "peak_l": audio_levels['peak_l'],
            "peak_r": audio_levels['peak_r'],
            "rms_l": audio_levels['peak_l'] - 10,  # Approximate RMS
            "rms_r": audio_levels['peak_r'] - 10
        }
    else:
        # Return silence levels if Liquidsoap not responding
        return {
            "peak_l": -60.0,
            "peak_r": -60.0,
            "rms_l": -60.0,
            "rms_r": -60.0
        }


@router.get("/flows/{flow_id}/srt-stats")
async def get_flow_srt_stats(flow_id: str):
    """
    Get SRT transport statistics for a Flow

    - **flow_id**: Flow ID
    """
    flow_config = config_mgr.load_flow_config(flow_id)
    if not flow_config:
        raise HTTPException(status_code=404, detail="Flow not found")

    srt_stats = get_srt_stats(flow_id)
    if srt_stats:
        return srt_stats
    else:
        # Return null stats if SRT not active
        raise HTTPException(status_code=404, detail="SRT stats not available")
