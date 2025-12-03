"""StereoTool related models"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StereoToolLicense(BaseModel):
    """StereoTool license key information"""
    id: str = Field(..., description="Unique license identifier")
    name: str = Field(..., description="Friendly name for this license")
    license_key: str = Field(..., description="License key (partial, for display)")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    is_valid: bool = Field(default=True, description="License validation status")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "lic_abc123",
                "name": "Main Studio License",
                "license_key": "ST-1234-5678-ABCD...",
                "added_at": "2025-12-02T10:00:00Z",
                "is_valid": True
            }
        }


class StereoToolPreset(BaseModel):
    """StereoTool preset file information"""
    id: str = Field(..., description="Unique preset identifier")
    name: str = Field(..., description="Preset friendly name")
    filename: str = Field(..., description="Original .sts filename")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    file_size: int = Field(..., description="File size in bytes")
    description: Optional[str] = Field(None, description="Preset description")
    is_default: bool = Field(default=False, description="Is this the default preset")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "preset_xyz789",
                "name": "Broadcast FM",
                "filename": "broadcast_fm.sts",
                "uploaded_at": "2025-12-02T10:00:00Z",
                "file_size": 51200,
                "description": "Heavy compression for FM broadcast",
                "is_default": True
            }
        }


class PresetUploadRequest(BaseModel):
    """Request to upload a new preset"""
    name: str = Field(..., description="Friendly name for the preset")
    description: Optional[str] = Field(None, description="Optional description")


class PresetActivateRequest(BaseModel):
    """Request to activate a preset as default"""
    preset_id: str = Field(..., description="Preset ID to activate")
