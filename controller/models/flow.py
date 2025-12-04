"""Flow related models"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class FlowInput(BaseModel):
    """Flow input configuration"""
    type: Literal["inferno", "alsa", "usb", "srt", "ndi", "file"] = Field(
        ..., description="Input type"
    )
    device: Optional[str] = Field(None, description="Device name for ALSA/USB/Inferno")
    channels: int = Field(default=2, description="Number of channels")
    sample_rate: int = Field(default=48000, description="Sample rate in Hz")
    priority: int = Field(..., description="Input priority (1=highest)")
    fallback: bool = Field(default=False, description="Is this a fallback input")

    # SRT-specific fields
    srt_url: Optional[str] = Field(None, description="SRT URL for SRT inputs")

    # GPIO extraction (per-input)
    gpio_extract: bool = Field(default=False, description="Extract GPIO data from this input (SRT only)")
    gpio_output_tcp_host: Optional[str] = Field(None, description="TCP host for extracted GPIO output")
    gpio_output_tcp_port: Optional[int] = Field(None, description="TCP port for extracted GPIO output")

    # File-specific fields
    file_path: Optional[str] = Field(None, description="File path for file inputs")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "inferno",
                "device": "hw:InfernoStream0",
                "channels": 2,
                "sample_rate": 48000,
                "priority": 1,
                "fallback": False
            }
        }


class StereoToolConfig(BaseModel):
    """StereoTool processing configuration"""
    enabled: bool = Field(default=False, description="Enable StereoTool processing")
    preset: Optional[str] = Field(None, description="Preset file path or ID")


class SilenceDetectionConfig(BaseModel):
    """Silence detection configuration"""
    threshold_dbfs: float = Field(default=-50.0, description="Silence threshold in dBFS")
    duration_s: int = Field(default=5, description="Duration in seconds to trigger alert")


class ProcessingConfig(BaseModel):
    """Flow audio processing configuration"""
    stereotool: StereoToolConfig = Field(default_factory=StereoToolConfig)
    silence_detection: SilenceDetectionConfig = Field(default_factory=SilenceDetectionConfig)
    crossfade: bool = Field(default=False, description="Enable crossfade")
    crossfade_duration_s: float = Field(default=2.0, description="Crossfade duration")


class SRTOutput(BaseModel):
    """SRT output configuration"""
    mode: Literal["caller", "listener"] = Field(..., description="SRT mode")
    host: Optional[str] = Field(None, description="Remote host (for caller mode)")
    port: int = Field(..., description="Port number")
    latency_ms: int = Field(default=200, description="SRT latency in milliseconds")
    passphrase: Optional[str] = Field(None, description="Encryption passphrase")
    codec: Literal["opus", "aac", "pcm"] = Field(default="opus", description="Audio codec")
    bitrate_kbps: int = Field(default=128, description="Bitrate in kbps")
    container: Literal["matroska", "mpegts"] = Field(default="matroska", description="Container format")

    # GPIO embedding (per-output)
    gpio_embed: bool = Field(default=False, description="Embed GPIO data in this SRT output")
    gpio_input_tcp_port: Optional[int] = Field(None, description="TCP port to receive GPIO for embedding")

    class Config:
        json_schema_extra = {
            "example": {
                "mode": "caller",
                "host": "srt.example.com",
                "port": 9000,
                "latency_ms": 200,
                "passphrase": "mysecret",
                "codec": "opus",
                "bitrate_kbps": 128,
                "container": "matroska"
            }
        }


class ALSAOutput(BaseModel):
    """ALSA output configuration"""
    device: str = Field(..., description="ALSA device name")
    channels: int = Field(default=2, description="Number of channels")
    sample_rate: int = Field(default=48000, description="Sample rate in Hz")

    # GPIO routing (per-output)
    gpio_output_tcp_host: Optional[str] = Field(None, description="TCP host for GPIO output (for Dante outputs)")
    gpio_output_tcp_port: Optional[int] = Field(None, description="TCP port for GPIO output")


class OutputsConfig(BaseModel):
    """Flow outputs configuration"""
    srt: List[SRTOutput] = Field(default_factory=list, description="SRT outputs")
    alsa: List[ALSAOutput] = Field(default_factory=list, description="ALSA outputs")


class GPIOConfig(BaseModel):
    """GPIO configuration for Flow"""
    tcp_input: bool = Field(default=False, description="Enable TCP input")
    tcp_input_port: Optional[int] = Field(None, description="TCP input port")
    http_input: bool = Field(default=False, description="Enable HTTP input")
    http_input_port: Optional[int] = Field(None, description="HTTP input port")
    tcp_output: bool = Field(default=False, description="Enable TCP output")
    tcp_output_host: Optional[str] = Field(None, description="TCP output host")
    tcp_output_port: Optional[int] = Field(None, description="TCP output port")
    embed_in_srt: bool = Field(default=False, description="Embed GPIO in SRT stream")


class MetadataConfig(BaseModel):
    """Metadata configuration for Flow"""
    enabled: bool = Field(default=True, description="Enable metadata")
    websocket: bool = Field(default=True, description="Expose via WebSocket")
    embed_in_srt: bool = Field(default=False, description="Embed in SRT stream")
    rest_endpoint: bool = Field(default=True, description="Expose via REST")


class MonitoringConfig(BaseModel):
    """Monitoring configuration for Flow"""
    metering: bool = Field(default=True, description="Enable audio metering")
    silence_detection: bool = Field(default=True, description="Enable silence detection")
    srt_stats: bool = Field(default=True, description="Enable SRT statistics")
    prometheus: bool = Field(default=True, description="Expose Prometheus metrics")


class FlowConfig(BaseModel):
    """Complete Flow configuration"""
    id: str = Field(..., description="Unique Flow identifier")
    name: str = Field(..., description="Flow name")
    enabled: bool = Field(default=True, description="Flow enabled status")
    inputs: List[FlowInput] = Field(..., description="Input sources")
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    outputs: OutputsConfig = Field(default_factory=OutputsConfig)
    gpio: GPIOConfig = Field(default_factory=GPIOConfig)
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "main_flow",
                "name": "Main Program Feed",
                "enabled": True,
                "inputs": [
                    {
                        "type": "inferno",
                        "device": "hw:InfernoStream0",
                        "channels": 2,
                        "sample_rate": 48000,
                        "priority": 1,
                        "fallback": False
                    }
                ],
                "processing": {
                    "stereotool": {
                        "enabled": True,
                        "preset": "preset_xyz789"
                    },
                    "silence_detection": {
                        "threshold_dbfs": -50.0,
                        "duration_s": 5
                    },
                    "crossfade": True,
                    "crossfade_duration_s": 2.0
                },
                "outputs": {
                    "srt": [
                        {
                            "mode": "caller",
                            "host": "srt.example.com",
                            "port": 9000,
                            "latency_ms": 200,
                            "codec": "opus",
                            "bitrate_kbps": 128,
                            "container": "matroska"
                        }
                    ],
                    "alsa": []
                },
                "gpio": {
                    "tcp_input": True,
                    "tcp_input_port": 7000,
                    "http_input": False,
                    "tcp_output": False,
                    "embed_in_srt": False
                },
                "metadata": {
                    "enabled": True,
                    "websocket": True,
                    "embed_in_srt": False,
                    "rest_endpoint": True
                },
                "monitoring": {
                    "metering": True,
                    "silence_detection": True,
                    "srt_stats": True,
                    "prometheus": True
                }
            }
        }


class FlowStatus(BaseModel):
    """Flow runtime status"""
    flow_id: str = Field(..., description="Flow identifier")
    status: Literal["running", "stopped", "starting", "stopping", "error"] = Field(
        ..., description="Current status"
    )
    liquidsoap_pid: Optional[int] = Field(None, description="Liquidsoap process ID")
    ffmpeg_pids: List[int] = Field(default_factory=list, description="FFmpeg process IDs")
    uptime_seconds: Optional[int] = Field(None, description="Uptime in seconds")
    last_error: Optional[str] = Field(None, description="Last error message")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "flow_id": "main_flow",
                "status": "running",
                "liquidsoap_pid": 12345,
                "ffmpeg_pids": [12346, 12347],
                "uptime_seconds": 3600,
                "last_error": None,
                "updated_at": "2025-12-02T11:00:00Z"
            }
        }


class FlowMetrics(BaseModel):
    """Flow metrics"""
    flow_id: str = Field(..., description="Flow identifier")
    audio_peak_left_dbfs: float = Field(..., description="Left channel peak in dBFS")
    audio_peak_right_dbfs: float = Field(..., description="Right channel peak in dBFS")
    is_silent: bool = Field(default=False, description="Silence detected")
    srt_rtt_ms: Optional[float] = Field(None, description="SRT round-trip time in ms")
    srt_packet_loss: Optional[float] = Field(None, description="SRT packet loss ratio")
    srt_bitrate_kbps: Optional[float] = Field(None, description="SRT bitrate in kbps")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "flow_id": "main_flow",
                "audio_peak_left_dbfs": -12.5,
                "audio_peak_right_dbfs": -11.8,
                "is_silent": False,
                "srt_rtt_ms": 15.2,
                "srt_packet_loss": 0.0001,
                "srt_bitrate_kbps": 128.4,
                "timestamp": "2025-12-02T11:00:00Z"
            }
        }


class FlowCreateRequest(BaseModel):
    """Request to create a new Flow"""
    config: FlowConfig = Field(..., description="Flow configuration")


class FlowUpdateRequest(BaseModel):
    """Request to update an existing Flow"""
    config: FlowConfig = Field(..., description="Updated Flow configuration")
