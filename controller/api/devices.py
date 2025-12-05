"""Device API endpoints"""

from fastapi import APIRouter, HTTPException
from typing import List
import logging
import subprocess
import asyncio

from models.device import AudioDevice, DeviceUpdateRequest, DeviceScanResponse
from core.device_manager import DeviceManager

logger = logging.getLogger(__name__)


async def play_test_tone(device_name: str, duration_seconds: int = 3) -> bool:
    """
    Play a test tone on the specified ALSA device.
    Returns True if successful.
    """
    try:
        # Use speaker-test for a quick sine wave test
        proc = await asyncio.create_subprocess_exec(
            'speaker-test',
            '-D', device_name,
            '-c', '2',  # stereo
            '-t', 'sine',  # sine wave
            '-f', '1000',  # 1kHz
            '-l', '1',  # 1 iteration
            '-p', str(duration_seconds),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=duration_seconds + 5)

        if proc.returncode != 0:
            logger.warning(f"speaker-test failed: {stderr.decode()}")
            return False
        return True

    except asyncio.TimeoutError:
        logger.warning("Device test timed out")
        return False
    except FileNotFoundError:
        logger.error("speaker-test not found, install alsa-utils")
        return False
    except Exception as e:
        logger.error(f"Device test error: {e}")
        return False

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

    # Play a 3-second test tone on the device
    success = await play_test_tone(device.alsa_device, duration_seconds=3)

    if success:
        return {
            "message": "Device test completed successfully",
            "device_id": device_id,
            "test_duration_seconds": 3
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Device test failed - check device connection and ALSA configuration"
        )
