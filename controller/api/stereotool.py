"""StereoTool API endpoints"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from typing import List
import logging

from models.stereotool import StereoToolLicense, StereoToolPreset, PresetActivateRequest
from core.stereotool_manager import StereoToolManager

logger = logging.getLogger(__name__)

router = APIRouter()
stereotool_mgr = StereoToolManager()


@router.post("/stereotool/licenses", response_model=StereoToolLicense)
async def upload_license(file: UploadFile = File(...)):
    """
    Upload a StereoTool license file

    - **file**: License file to upload
    """
    try:
        content = await file.read()
        license = await stereotool_mgr.upload_license(content, file.filename or "license.key")
        return license
    except Exception as e:
        logger.error(f"Error uploading license: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stereotool/licenses", response_model=List[StereoToolLicense])
async def list_licenses():
    """List all uploaded StereoTool licenses"""
    return stereotool_mgr.list_licenses()


@router.delete("/stereotool/licenses/{license_id}")
async def delete_license(license_id: str):
    """
    Delete a StereoTool license

    - **license_id**: License ID to delete
    """
    success = stereotool_mgr.delete_license(license_id)
    if not success:
        raise HTTPException(status_code=404, detail="License not found")
    return {"message": "License deleted successfully", "license_id": license_id}


@router.post("/stereotool/presets", response_model=StereoToolPreset)
async def upload_preset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(None)
):
    """
    Upload a StereoTool preset file

    - **file**: Preset .sts file to upload
    - **name**: Friendly name for the preset
    - **description**: Optional description
    """
    try:
        content = await file.read()
        preset = await stereotool_mgr.upload_preset(
            content,
            file.filename or "preset.sts",
            name,
            description
        )
        return preset
    except Exception as e:
        logger.error(f"Error uploading preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stereotool/presets", response_model=List[StereoToolPreset])
async def list_presets():
    """List all uploaded StereoTool presets"""
    return stereotool_mgr.list_presets()


@router.get("/stereotool/presets/{preset_id}", response_model=StereoToolPreset)
async def get_preset(preset_id: str):
    """
    Get preset details

    - **preset_id**: Preset ID
    """
    preset = stereotool_mgr.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset


@router.get("/stereotool/presets/{preset_id}/download")
async def download_preset(preset_id: str):
    """
    Download preset file

    - **preset_id**: Preset ID to download
    """
    preset = stereotool_mgr.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    content = await stereotool_mgr.download_preset(preset_id)
    if not content:
        raise HTTPException(status_code=500, detail="Error reading preset file")

    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={preset.filename}"}
    )


@router.put("/stereotool/presets/{preset_id}/activate")
async def activate_preset(preset_id: str):
    """
    Set preset as default

    - **preset_id**: Preset ID to activate
    """
    success = stereotool_mgr.activate_preset(preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"message": "Preset activated successfully", "preset_id": preset_id}


@router.delete("/stereotool/presets/{preset_id}")
async def delete_preset(preset_id: str):
    """
    Delete a StereoTool preset

    - **preset_id**: Preset ID to delete
    """
    success = stereotool_mgr.delete_preset(preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"message": "Preset deleted successfully", "preset_id": preset_id}
