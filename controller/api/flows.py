"""Flow API endpoints"""

from fastapi import APIRouter, HTTPException
from typing import List
import logging

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

    # TODO: Implement metrics collection from Liquidsoap and FFmpeg
    # For now, return mock data
    return FlowMetrics(
        flow_id=flow_id,
        audio_peak_left_dbfs=-12.5,
        audio_peak_right_dbfs=-11.8,
        is_silent=False,
        srt_rtt_ms=15.2,
        srt_packet_loss=0.0001,
        srt_bitrate_kbps=128.4
    )
