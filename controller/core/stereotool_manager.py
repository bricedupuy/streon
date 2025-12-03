"""StereoTool license and preset management"""

import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging
import json

from models.stereotool import StereoToolLicense, StereoToolPreset

logger = logging.getLogger(__name__)


class StereoToolManager:
    """Manages StereoTool licenses and presets"""

    def __init__(self, streon_root: str = "/opt/streon"):
        self.streon_root = Path(streon_root)
        self.stereotool_dir = self.streon_root / "liquidsoap" / "stereotool"
        self.licenses_dir = self.stereotool_dir / "licenses"
        self.presets_dir = self.stereotool_dir / "presets"
        self.metadata_file = self.stereotool_dir / "metadata.json"

        # Ensure directories exist
        self.licenses_dir.mkdir(parents=True, exist_ok=True)
        self.presets_dir.mkdir(parents=True, exist_ok=True)

        # Load metadata
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        """Load metadata for licenses and presets"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                return {"licenses": {}, "presets": {}}
        return {"licenses": {}, "presets": {}}

    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    # License management

    async def add_license(self, license_key: str, name: str) -> StereoToolLicense:
        """Add a StereoTool license key (text string)"""
        license_id = f"lic_{uuid.uuid4().hex[:12]}"
        license_path = self.licenses_dir / f"{license_id}.txt"

        try:
            # Save license key to text file
            with open(license_path, 'w') as f:
                f.write(license_key.strip())

            # Create license record
            license = StereoToolLicense(
                id=license_id,
                name=name,
                license_key=license_key[:20] + "..." if len(license_key) > 20 else license_key,  # Partial key for display
                added_at=datetime.utcnow(),
                is_valid=True  # TODO: Implement license validation with StereoTool
            )

            # Save metadata
            self.metadata["licenses"][license_id] = license.model_dump()
            self._save_metadata()

            logger.info(f"Added license: {name} ({license_id})")
            return license

        except Exception as e:
            logger.error(f"Error adding license: {e}")
            raise

    def list_licenses(self) -> List[StereoToolLicense]:
        """List all uploaded licenses"""
        licenses = []
        for license_id, data in self.metadata["licenses"].items():
            try:
                licenses.append(StereoToolLicense(**data))
            except Exception as e:
                logger.error(f"Error loading license {license_id}: {e}")
        return licenses

    def delete_license(self, license_id: str) -> bool:
        """Delete a license"""
        if license_id not in self.metadata["licenses"]:
            logger.warning(f"License not found: {license_id}")
            return False

        try:
            # Delete file
            license_path = self.licenses_dir / f"{license_id}.txt"
            if license_path.exists():
                license_path.unlink()

            # Remove from metadata
            del self.metadata["licenses"][license_id]
            self._save_metadata()

            logger.info(f"Deleted license: {license_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting license {license_id}: {e}")
            return False

    # Preset management

    async def upload_preset(self, file_content: bytes, filename: str, name: str,
                           description: Optional[str] = None) -> StereoToolPreset:
        """Upload a StereoTool preset file"""
        preset_id = f"preset_{uuid.uuid4().hex[:12]}"
        preset_path = self.presets_dir / f"{preset_id}.sts"

        try:
            # Save file
            with open(preset_path, 'wb') as f:
                f.write(file_content)

            # Create preset record
            preset = StereoToolPreset(
                id=preset_id,
                name=name,
                filename=filename,
                uploaded_at=datetime.utcnow(),
                file_size=len(file_content),
                description=description,
                is_default=False
            )

            # Save metadata
            self.metadata["presets"][preset_id] = preset.model_dump()
            self._save_metadata()

            logger.info(f"Uploaded preset: {preset_id} ({name})")
            return preset

        except Exception as e:
            logger.error(f"Error uploading preset: {e}")
            raise

    def list_presets(self) -> List[StereoToolPreset]:
        """List all uploaded presets"""
        presets = []
        for preset_id, data in self.metadata["presets"].items():
            try:
                presets.append(StereoToolPreset(**data))
            except Exception as e:
                logger.error(f"Error loading preset {preset_id}: {e}")
        return presets

    def get_preset(self, preset_id: str) -> Optional[StereoToolPreset]:
        """Get preset by ID"""
        if preset_id not in self.metadata["presets"]:
            return None
        try:
            return StereoToolPreset(**self.metadata["presets"][preset_id])
        except Exception as e:
            logger.error(f"Error getting preset {preset_id}: {e}")
            return None

    def get_preset_path(self, preset_id: str) -> Optional[Path]:
        """Get filesystem path for preset"""
        preset_path = self.presets_dir / f"{preset_id}.sts"
        if preset_path.exists():
            return preset_path
        return None

    def activate_preset(self, preset_id: str) -> bool:
        """Set preset as default"""
        if preset_id not in self.metadata["presets"]:
            logger.warning(f"Preset not found: {preset_id}")
            return False

        try:
            # Deactivate all presets
            for pid in self.metadata["presets"]:
                self.metadata["presets"][pid]["is_default"] = False

            # Activate selected preset
            self.metadata["presets"][preset_id]["is_default"] = True
            self._save_metadata()

            logger.info(f"Activated preset: {preset_id}")
            return True

        except Exception as e:
            logger.error(f"Error activating preset {preset_id}: {e}")
            return False

    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset"""
        if preset_id not in self.metadata["presets"]:
            logger.warning(f"Preset not found: {preset_id}")
            return False

        try:
            # Delete file
            preset_path = self.presets_dir / f"{preset_id}.sts"
            if preset_path.exists():
                preset_path.unlink()

            # Remove from metadata
            del self.metadata["presets"][preset_id]
            self._save_metadata()

            logger.info(f"Deleted preset: {preset_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting preset {preset_id}: {e}")
            return False

    async def download_preset(self, preset_id: str) -> Optional[bytes]:
        """Download preset file content"""
        preset_path = self.get_preset_path(preset_id)
        if not preset_path:
            return None

        try:
            with open(preset_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading preset {preset_id}: {e}")
            return None
