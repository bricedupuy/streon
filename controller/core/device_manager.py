"""Audio device discovery and management"""

import subprocess
import re
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import logging
import json

from models.device import AudioDevice

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages audio device discovery and registry"""

    def __init__(self, config_dir: str = "/etc/streon"):
        self.config_dir = Path(config_dir)
        self.device_registry_file = self.config_dir / "devices.json"
        self.devices: Dict[str, AudioDevice] = {}

        # Load device registry
        self._load_registry()

    def _load_registry(self):
        """Load device registry from file"""
        if self.device_registry_file.exists():
            try:
                with open(self.device_registry_file, 'r') as f:
                    data = json.load(f)
                    for dev_id, dev_data in data.items():
                        try:
                            self.devices[dev_id] = AudioDevice(**dev_data)
                        except Exception as e:
                            logger.error(f"Error loading device {dev_id}: {e}")
            except Exception as e:
                logger.error(f"Error loading device registry: {e}")

    def _save_registry(self):
        """Save device registry to file"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.device_registry_file, 'w') as f:
                data = {dev_id: dev.model_dump() for dev_id, dev in self.devices.items()}
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving device registry: {e}")

    def scan_alsa_devices(self) -> List[AudioDevice]:
        """Scan for ALSA audio devices"""
        devices = []

        try:
            # Scan playback devices
            playback_devices = self._parse_aplay_list()
            devices.extend(playback_devices)

            # Scan capture devices
            capture_devices = self._parse_arecord_list()
            devices.extend(capture_devices)

            # Scan Inferno devices (if available)
            inferno_devices = self._scan_inferno_devices()
            devices.extend(inferno_devices)

            # Update registry
            for device in devices:
                if device.id in self.devices:
                    # Update existing device, preserve friendly name
                    existing = self.devices[device.id]
                    device.friendly_name = existing.friendly_name or device.friendly_name
                    device.in_use_by = existing.in_use_by

                self.devices[device.id] = device

            self._save_registry()
            logger.info(f"Scanned {len(devices)} devices")

        except Exception as e:
            logger.error(f"Error scanning ALSA devices: {e}")

        return devices

    def _parse_aplay_list(self) -> List[AudioDevice]:
        """Parse aplay -l output"""
        devices = []

        try:
            result = subprocess.run(
                ["aplay", "-l"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return devices

            # Parse output
            # Example: card 0: PCH [HDA Intel PCH], device 0: ALC269VC Analog [ALC269VC Analog]
            pattern = r'card (\d+): (.+?) \[(.+?)\], device (\d+): (.+?) \[(.+?)\]'

            for match in re.finditer(pattern, result.stdout):
                card_id = match.group(1)
                card_name = match.group(2)
                device_id = match.group(4)
                device_name = match.group(5)

                dev_id = f"dev_alsa_p_{card_id}_{device_id}"
                hw_name = f"hw:{card_id},{device_id}"

                device = AudioDevice(
                    id=dev_id,
                    type="alsa",
                    device_name=hw_name,
                    friendly_name=f"{card_name} - {device_name}",
                    channels=2,  # Default, can be detected later
                    sample_rate=48000,  # Default
                    is_available=True,
                    last_seen=datetime.utcnow()
                )
                devices.append(device)

        except subprocess.TimeoutExpired:
            logger.warning("aplay -l command timed out")
        except FileNotFoundError:
            logger.warning("aplay command not found")
        except Exception as e:
            logger.error(f"Error parsing aplay output: {e}")

        return devices

    def _parse_arecord_list(self) -> List[AudioDevice]:
        """Parse arecord -l output"""
        devices = []

        try:
            result = subprocess.run(
                ["arecord", "-l"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return devices

            # Parse output (same format as aplay)
            pattern = r'card (\d+): (.+?) \[(.+?)\], device (\d+): (.+?) \[(.+?)\]'

            for match in re.finditer(pattern, result.stdout):
                card_id = match.group(1)
                card_name = match.group(2)
                device_id = match.group(4)
                device_name = match.group(5)

                dev_id = f"dev_alsa_c_{card_id}_{device_id}"
                hw_name = f"hw:{card_id},{device_id}"

                device = AudioDevice(
                    id=dev_id,
                    type="alsa",
                    device_name=hw_name,
                    friendly_name=f"{card_name} - {device_name} (Capture)",
                    channels=2,
                    sample_rate=48000,
                    is_available=True,
                    last_seen=datetime.utcnow()
                )
                devices.append(device)

        except subprocess.TimeoutExpired:
            logger.warning("arecord -l command timed out")
        except FileNotFoundError:
            logger.warning("arecord command not found")
        except Exception as e:
            logger.error(f"Error parsing arecord output: {e}")

        return devices

    def _scan_inferno_devices(self) -> List[AudioDevice]:
        """Scan for Inferno AoIP devices"""
        devices = []

        try:
            # Look for Inferno ALSA devices
            # They appear as hw:InfernoStream0, hw:InfernoStream1, etc.
            result = subprocess.run(
                ["aplay", "-L"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return devices

            # Find Inferno devices
            for line in result.stdout.splitlines():
                if "InfernoStream" in line or "InfernoTx" in line:
                    device_name = line.strip()

                    # Determine if it's RX or TX
                    if "InfernoTx" in device_name:
                        dev_type = "inferno_tx"
                        friendly_prefix = "Inferno TX"
                    else:
                        dev_type = "inferno_rx"
                        friendly_prefix = "Inferno RX"

                    dev_id = f"dev_{device_name.replace(':', '_').replace(',', '_')}"

                    device = AudioDevice(
                        id=dev_id,
                        type=dev_type,
                        device_name=device_name,
                        friendly_name=f"{friendly_prefix} - {device_name}",
                        channels=2,
                        sample_rate=48000,
                        is_available=True,
                        last_seen=datetime.utcnow()
                    )
                    devices.append(device)

        except Exception as e:
            logger.error(f"Error scanning Inferno devices: {e}")

        return devices

    def list_devices(self) -> List[AudioDevice]:
        """List all registered devices"""
        return list(self.devices.values())

    def get_device(self, device_id: str) -> Optional[AudioDevice]:
        """Get device by ID"""
        return self.devices.get(device_id)

    def update_device(self, device_id: str, friendly_name: Optional[str] = None) -> bool:
        """Update device information"""
        if device_id not in self.devices:
            logger.warning(f"Device not found: {device_id}")
            return False

        try:
            if friendly_name is not None:
                self.devices[device_id].friendly_name = friendly_name

            self._save_registry()
            logger.info(f"Updated device: {device_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating device {device_id}: {e}")
            return False

    def mark_device_in_use(self, device_id: str, flow_id: str):
        """Mark device as in use by a Flow"""
        if device_id in self.devices:
            self.devices[device_id].in_use_by = flow_id
            self._save_registry()

    def mark_device_available(self, device_id: str):
        """Mark device as available"""
        if device_id in self.devices:
            self.devices[device_id].in_use_by = None
            self._save_registry()
