"""Configuration management"""

import yaml
import os
from pathlib import Path
from typing import Optional
import logging

from models.config import GlobalConfig
from models.flow import FlowConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages Streon configuration files"""

    def __init__(self, config_dir: str = "/etc/streon"):
        self.config_dir = Path(config_dir)
        self.flows_dir = self.config_dir / "flows"

        # Ensure directories exist (in development mode, create them)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.flows_dir.mkdir(parents=True, exist_ok=True)

    def load_global_config(self) -> GlobalConfig:
        """Load global Streon configuration"""
        config_file = self.config_dir / "streon.yaml"

        if not config_file.exists():
            logger.info("Global config not found, using defaults")
            config = GlobalConfig()
            self.save_global_config(config)
            return config

        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
                return GlobalConfig(**data)
        except Exception as e:
            logger.error(f"Error loading global config: {e}")
            return GlobalConfig()

    def save_global_config(self, config: GlobalConfig):
        """Save global configuration"""
        config_file = self.config_dir / "streon.yaml"

        try:
            with open(config_file, 'w') as f:
                yaml.dump(config.model_dump(), f, default_flow_style=False)
            logger.info(f"Saved global config to {config_file}")
        except Exception as e:
            logger.error(f"Error saving global config: {e}")
            raise

    def load_flow_config(self, flow_id: str) -> Optional[FlowConfig]:
        """Load Flow configuration"""
        flow_file = self.flows_dir / f"{flow_id}.yaml"

        if not flow_file.exists():
            logger.warning(f"Flow config not found: {flow_id}")
            return None

        try:
            with open(flow_file, 'r') as f:
                data = yaml.safe_load(f)
                return FlowConfig(**data)
        except Exception as e:
            logger.error(f"Error loading Flow config {flow_id}: {e}")
            return None

    def save_flow_config(self, flow_config: FlowConfig):
        """Save Flow configuration"""
        flow_file = self.flows_dir / f"{flow_config.id}.yaml"

        try:
            # Atomic write: write to temp file, then rename
            temp_file = flow_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                yaml.dump(flow_config.model_dump(), f, default_flow_style=False)

            # Backup existing file if it exists
            if flow_file.exists():
                backup_file = flow_file.with_suffix('.yaml.bak')
                flow_file.rename(backup_file)

            # Rename temp to actual
            temp_file.rename(flow_file)

            logger.info(f"Saved Flow config: {flow_config.id}")
        except Exception as e:
            logger.error(f"Error saving Flow config {flow_config.id}: {e}")
            raise

    def delete_flow_config(self, flow_id: str):
        """Delete Flow configuration"""
        flow_file = self.flows_dir / f"{flow_id}.yaml"

        try:
            if flow_file.exists():
                # Move to backup instead of deleting
                backup_file = flow_file.with_suffix('.yaml.deleted')
                flow_file.rename(backup_file)
                logger.info(f"Deleted Flow config: {flow_id}")
            else:
                logger.warning(f"Flow config not found for deletion: {flow_id}")
        except Exception as e:
            logger.error(f"Error deleting Flow config {flow_id}: {e}")
            raise

    def list_flows(self) -> list[str]:
        """List all Flow IDs"""
        flow_files = self.flows_dir.glob("*.yaml")
        return [f.stem for f in flow_files if not f.name.endswith('.bak') and not f.name.endswith('.deleted')]
