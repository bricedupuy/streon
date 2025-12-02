"""Device API endpoints"""

from fastapi import APIRouter, HTTPException
from typing import List
import logging

from models.device import AudioDevice, DeviceUpdateRequest, DeviceScanResponse
from core.device_manager import DeviceManager

logger = logging.getLogger(__name__)

router = APIRouter()
device_mgr = DeviceManager()


@router.get("/devices", response_model=List[AudioDevice])
async def list_devices():
    """
    List all audio devices

    Returns all registered audio devices including ALSA, USB, HDMI, and Inferno devices
    """
    return device_mgr.list_devices()


@router.get("/devices/scan", response_model=DeviceScanResponse)
async def scan_devices():
    """
    Trigger a device scan

    Scans the system for available audio devices and updates the registry
    """
    try:
        devices = device_mgr.scan_alsa_devices()
        return DeviceScanResponse(devices_found=len(devices))
    except Exception as e:
        logger.error(f"Error scanning devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_id}", response_model=AudioDevice)
async def get_device(device_id: str):
    """
    Get device details

    - **device_id**: Device ID
    """
    device = device_mgr.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/devices/{device_id}")
async def update_device(device_id: str, request: DeviceUpdateRequest):
    """
    Update device information

    - **device_id**: Device ID
    - **request**: Update request with friendly_name
    """
    success = device_mgr.update_device(
        device_id,
        friendly_name=request.friendly_name
    )

    if not success:
        raise HTTPException(status_code=404, detail="Device not found")

    return {"message": "Device updated successfully", "device_id": device_id}


@router.post("/devices/{device_id}/test")
async def test_device(device_id: str):
    """
    Test device (play test tone)

    - **device_id**: Device ID to test
    """
    device = device_mgr.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # TODO: Implement device test (play tone using aplay/speaker-test)

    return {
        "message": "Device test initiated",
        "device_id": device_id,
        "note": "Device test not yet implemented"
    }
