"""Device related models"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class AudioDevice(BaseModel):
    """Audio device information"""
    id: str = Field(..., description="Unique device identifier")
    type: Literal["alsa", "usb", "hdmi", "inferno_rx", "inferno_tx"] = Field(
        ..., description="Device type"
    )
    device_name: str = Field(..., description="System device name (e.g., hw:USB0)")
    friendly_name: Optional[str] = Field(None, description="User-friendly name")
    channels: int = Field(..., description="Number of audio channels")
    sample_rate: int = Field(..., description="Sample rate in Hz")
    is_available: bool = Field(default=True, description="Device availability status")
    in_use_by: Optional[str] = Field(None, description="Flow ID using this device")
    last_seen: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "dev_usb0",
                "type": "usb",
                "device_name": "hw:USB0",
                "friendly_name": "Studio USB Interface",
                "channels": 2,
                "sample_rate": 48000,
                "is_available": True,
                "in_use_by": None,
                "last_seen": "2025-12-02T10:00:00Z"
            }
        }


class DeviceUpdateRequest(BaseModel):
    """Request to update device information"""
    friendly_name: Optional[str] = Field(None, description="New friendly name")


class DeviceScanResponse(BaseModel):
    """Response from device scan operation"""
    devices_found: int = Field(..., description="Number of devices discovered")
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow)
