"""Configuration models"""

from pydantic import BaseModel, Field
from typing import Optional


class GlobalConfig(BaseModel):
    """Global Streon configuration"""
    streon_root: str = Field(default="/opt/streon", description="Streon installation root")
    config_dir: str = Field(default="/etc/streon", description="Configuration directory")
    log_dir: str = Field(default="/var/log/streon", description="Log directory")
    controller_host: str = Field(default="0.0.0.0", description="Controller bind address")
    controller_port: int = Field(default=8000, description="Controller port")
    inferno_enabled: bool = Field(default=False, description="Inferno AoIP enabled")
    inferno_config_path: str = Field(
        default="/opt/inferno/config/inferno.toml",
        description="Inferno config path"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "streon_root": "/opt/streon",
                "config_dir": "/etc/streon",
                "log_dir": "/var/log/streon",
                "controller_host": "0.0.0.0",
                "controller_port": 8000,
                "inferno_enabled": True,
                "inferno_config_path": "/opt/inferno/config/inferno.toml"
            }
        }


class SystemHealth(BaseModel):
    """System health status"""
    controller_up: bool = Field(..., description="Controller is running")
    inferno_up: Optional[bool] = Field(None, description="Inferno is running")
    ptp_synced: Optional[bool] = Field(None, description="PTP synchronized")
    active_flows: int = Field(..., description="Number of active Flows")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "controller_up": True,
                "inferno_up": True,
                "ptp_synced": True,
                "active_flows": 3,
                "cpu_usage_percent": 35.2,
                "memory_usage_percent": 62.1,
                "disk_usage_percent": 45.8
            }
        }
