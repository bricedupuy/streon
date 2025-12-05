"""Flow lifecycle management"""

import os
import subprocess
import signal
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import logging
import psutil
from jinja2 import Template

from models.flow import FlowConfig, FlowStatus
from core.config_manager import ConfigManager
from core.stereotool_manager import StereoToolManager

logger = logging.getLogger(__name__)


class FlowManager:
    """Manages Flow lifecycle, Liquidsoap, and FFmpeg processes"""

    def __init__(
        self,
        streon_root: str = "/opt/streon",
        liquidsoap_bin: str = "/opt/streon/liquidsoap/bin/liquidsoap",
        ffmpeg_bin: str = "/usr/bin/ffmpeg"
    ):
        self.streon_root = Path(streon_root)
        self.flows_dir = self.streon_root / "flows"
        self.liquidsoap_templates_dir = self.streon_root / "liquidsoap" / "templates"
        self.liquidsoap_bin = liquidsoap_bin
        self.ffmpeg_bin = ffmpeg_bin
        self.config_mgr = ConfigManager()
        self.stereotool_mgr = StereoToolManager(str(self.streon_root))

        # Track running processes
        self.flow_processes: Dict[str, Dict] = {}

        # Ensure flows directory exists
        self.flows_dir.mkdir(parents=True, exist_ok=True)

    def create_flow(self, flow_config: FlowConfig) -> FlowConfig:
        """Create a new Flow"""
        flow_id = flow_config.id

        # Check if Flow already exists
        if self.config_mgr.load_flow_config(flow_id):
            raise ValueError(f"Flow already exists: {flow_id}")

        # Validate Flow configuration
        self._validate_flow_config(flow_config)

        # Create Flow directory
        flow_dir = self.flows_dir / flow_id
        flow_dir.mkdir(parents=True, exist_ok=True)

        # Generate Liquidsoap script
        script_path = flow_dir / "script.liq"
        self._generate_liquidsoap_script(flow_config, script_path)

        # Save Flow configuration
        self.config_mgr.save_flow_config(flow_config)

        logger.info(f"Created Flow: {flow_id}")
        return flow_config

    def update_flow(self, flow_id: str, flow_config: FlowConfig) -> FlowConfig:
        """Update existing Flow"""
        # Verify Flow exists
        existing = self.config_mgr.load_flow_config(flow_id)
        if not existing:
            raise ValueError(f"Flow not found: {flow_id}")

        # Check if Flow is running
        status = self.get_flow_status(flow_id)
        if status and status.status == "running":
            raise ValueError(f"Cannot update running Flow. Stop it first: {flow_id}")

        # Validate new configuration
        self._validate_flow_config(flow_config)

        # Regenerate Liquidsoap script
        flow_dir = self.flows_dir / flow_id
        script_path = flow_dir / "script.liq"
        self._generate_liquidsoap_script(flow_config, script_path)

        # Save updated configuration
        self.config_mgr.save_flow_config(flow_config)

        logger.info(f"Updated Flow: {flow_id}")
        return flow_config

    def delete_flow(self, flow_id: str):
        """Delete a Flow"""
        # Verify Flow exists
        existing = self.config_mgr.load_flow_config(flow_id)
        if not existing:
            raise ValueError(f"Flow not found: {flow_id}")

        # Stop Flow if running
        status = self.get_flow_status(flow_id)
        if status and status.status == "running":
            self.stop_flow(flow_id)

        # Delete configuration
        self.config_mgr.delete_flow_config(flow_id)

        # Delete Flow directory
        flow_dir = self.flows_dir / flow_id
        if flow_dir.exists():
            import shutil
            shutil.rmtree(flow_dir)

        logger.info(f"Deleted Flow: {flow_id}")

    def start_flow(self, flow_id: str):
        """Start a Flow"""
        # Load Flow configuration
        flow_config = self.config_mgr.load_flow_config(flow_id)
        if not flow_config:
            raise ValueError(f"Flow not found: {flow_id}")

        # Check if already running
        status = self.get_flow_status(flow_id)
        if status and status.status == "running":
            raise ValueError(f"Flow already running: {flow_id}")

        # Start Liquidsoap
        liquidsoap_pid = self._start_liquidsoap(flow_id, flow_config)

        # Start FFmpeg encoders (if any SRT outputs)
        ffmpeg_pids = []
        if flow_config.outputs.srt:
            ffmpeg_pids = self._start_ffmpeg_encoders(flow_id, flow_config)

        # Track processes
        self.flow_processes[flow_id] = {
            "liquidsoap_pid": liquidsoap_pid,
            "ffmpeg_pids": ffmpeg_pids,
            "started_at": datetime.utcnow()
        }

        logger.info(f"Started Flow: {flow_id} (Liquidsoap PID: {liquidsoap_pid})")

    def stop_flow(self, flow_id: str):
        """Stop a Flow"""
        if flow_id not in self.flow_processes:
            logger.warning(f"Flow not running: {flow_id}")
            return

        processes = self.flow_processes[flow_id]

        # Stop FFmpeg processes
        for pid in processes.get("ffmpeg_pids", []):
            self._stop_process(pid, "FFmpeg")

        # Stop Liquidsoap
        liquidsoap_pid = processes.get("liquidsoap_pid")
        if liquidsoap_pid:
            self._stop_process(liquidsoap_pid, "Liquidsoap")

        # Remove from tracking
        del self.flow_processes[flow_id]

        logger.info(f"Stopped Flow: {flow_id}")

    def restart_flow(self, flow_id: str):
        """Restart a Flow"""
        self.stop_flow(flow_id)
        import time
        time.sleep(2)  # Wait for processes to fully stop
        self.start_flow(flow_id)

    def get_flow_status(self, flow_id: str) -> Optional[FlowStatus]:
        """Get Flow runtime status"""
        if flow_id not in self.flow_processes:
            return FlowStatus(
                flow_id=flow_id,
                status="stopped",
                liquidsoap_pid=None,
                ffmpeg_pids=[],
                uptime_seconds=None
            )

        processes = self.flow_processes[flow_id]
        liquidsoap_pid = processes.get("liquidsoap_pid")
        ffmpeg_pids = processes.get("ffmpeg_pids", [])

        # Check if Liquidsoap is still running
        if liquidsoap_pid and not psutil.pid_exists(liquidsoap_pid):
            # Process died
            logger.error(f"Liquidsoap process died for Flow: {flow_id}")
            del self.flow_processes[flow_id]
            return FlowStatus(
                flow_id=flow_id,
                status="error",
                liquidsoap_pid=None,
                ffmpeg_pids=[],
                uptime_seconds=None,
                last_error="Liquidsoap process died unexpectedly"
            )

        # Calculate uptime
        started_at = processes.get("started_at")
        uptime_seconds = None
        if started_at:
            uptime_seconds = int((datetime.utcnow() - started_at).total_seconds())

        return FlowStatus(
            flow_id=flow_id,
            status="running",
            liquidsoap_pid=liquidsoap_pid,
            ffmpeg_pids=ffmpeg_pids,
            uptime_seconds=uptime_seconds
        )

    def list_flows(self) -> List[str]:
        """List all Flow IDs"""
        return self.config_mgr.list_flows()

    # Private methods

    def _validate_flow_config(self, flow_config: FlowConfig):
        """Validate Flow configuration"""
        # Check if StereoTool preset exists (if enabled)
        if flow_config.processing.stereotool.enabled:
            preset_id = flow_config.processing.stereotool.preset
            if preset_id:
                preset = self.stereotool_mgr.get_preset(preset_id)
                if not preset:
                    raise ValueError(f"StereoTool preset not found: {preset_id}")

        # Validate inputs
        if not flow_config.inputs:
            raise ValueError("Flow must have at least one input")

        # Validate outputs
        if not flow_config.outputs.srt and not flow_config.outputs.alsa:
            raise ValueError("Flow must have at least one output")

    def _generate_liquidsoap_script(self, flow_config: FlowConfig, script_path: Path):
        """Generate Liquidsoap script from Jinja2 template"""
        template_path = self.liquidsoap_templates_dir / "flow.liq.j2"

        # Get StereoTool preset path if enabled
        stereotool_preset_path = ""
        if flow_config.processing.stereotool.enabled and flow_config.processing.stereotool.preset:
            preset_path = self.stereotool_mgr.get_preset_path(flow_config.processing.stereotool.preset)
            if preset_path:
                stereotool_preset_path = str(preset_path)

        # Check if template exists
        if template_path.exists():
            # Use Jinja2 template
            with open(template_path, 'r') as f:
                template_content = f.read()

            template = Template(template_content)
            script_content = template.render(
                flow=flow_config,
                stereotool_preset_path=stereotool_preset_path,
                timestamp=datetime.utcnow().isoformat(),
                enumerate=enumerate
            )
        else:
            # Fallback to basic script generation
            logger.warning(f"Template not found: {template_path}, using basic script")
            script_content = self._generate_basic_script(flow_config, stereotool_preset_path)

        # Write script
        with open(script_path, 'w') as f:
            f.write(script_content)

        # Make executable
        script_path.chmod(0o755)

        logger.info(f"Generated Liquidsoap script: {script_path}")

    def _generate_basic_script(self, flow_config: FlowConfig, stereotool_preset_path: str) -> str:
        """Generate basic Liquidsoap script without template"""
        script_content = f"""#!/usr/bin/liquidsoap

# Flow: {flow_config.id}
# Name: {flow_config.name}

# Set log level
settings.log.level.set(4)

# Input sources
"""

        # Add inputs
        for idx, input_config in enumerate(flow_config.inputs):
            if input_config.type in ["alsa", "usb", "inferno_rx"]:
                script_content += f'input_{idx} = input.alsa(device="{input_config.device}")\n'

        # Fallback logic
        script_content += "\n# Fallback logic\n"
        script_content += "source = fallback(track_sensitive=false, ["
        script_content += ", ".join([f"input_{i}" for i in range(len(flow_config.inputs))])
        script_content += "])\n"

        # StereoTool processing
        if stereotool_preset_path:
            script_content += f'\n# StereoTool processing\nsource = stereotool(preset="{stereotool_preset_path}", source)\n'

        # Output to FIFO for FFmpeg
        if flow_config.outputs.srt:
            for idx in range(len(flow_config.outputs.srt)):
                fifo_path = f"/tmp/streon_{flow_config.id}_srt{idx}.fifo"
                script_content += f'\n# Output to FIFO for FFmpeg\noutput.file(%wav, "{fifo_path}", source)\n'

        # ALSA outputs
        for alsa_output in flow_config.outputs.alsa:
            script_content += f'\n# ALSA output\noutput.alsa(device="{alsa_output.device}", source)\n'

        return script_content

    def _start_liquidsoap(self, flow_id: str, flow_config: FlowConfig = None) -> int:
        """Start Liquidsoap process"""
        flow_dir = self.flows_dir / flow_id
        script_path = flow_dir / "script.liq"
        log_path = flow_dir / "liquidsoap.log"

        # Create FIFOs for each SRT output
        if flow_config and flow_config.outputs.srt:
            for idx in range(len(flow_config.outputs.srt)):
                fifo_path = f"/tmp/streon_{flow_id}_srt{idx}.fifo"
                if not os.path.exists(fifo_path):
                    os.mkfifo(fifo_path)
                    # Set permissions so both liquidsoap and ffmpeg can access
                    os.chmod(fifo_path, 0o666)

        # Start Liquidsoap
        cmd = [self.liquidsoap_bin, str(script_path)]

        with open(log_path, 'a') as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

        return process.pid

    def _start_ffmpeg_encoders(self, flow_id: str, flow_config: FlowConfig) -> List[int]:
        """Start FFmpeg encoder processes for SRT outputs"""
        pids = []

        for idx, srt_output in enumerate(flow_config.outputs.srt):
            # Each SRT output has its own FIFO
            fifo_path = f"/tmp/streon_{flow_id}_srt{idx}.fifo"

            # Build FFmpeg command
            cmd = [self.ffmpeg_bin, "-f", "wav", "-i", fifo_path]

            # Audio encoding
            if srt_output.codec == "opus":
                cmd.extend(["-c:a", "libopus", "-b:a", f"{srt_output.bitrate_kbps}k"])
            elif srt_output.codec == "aac":
                cmd.extend(["-c:a", "aac", "-b:a", f"{srt_output.bitrate_kbps}k"])
            else:  # pcm
                cmd.extend(["-c:a", "pcm_s16le"])

            # Container format
            cmd.extend(["-f", srt_output.container])

            # SRT output URL
            srt_url = self._build_srt_url(srt_output)
            cmd.append(srt_url)

            # Start process
            flow_dir = self.flows_dir / flow_id
            log_path = flow_dir / f"ffmpeg-encoder-{idx}.log"

            with open(log_path, 'a') as log_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )

            pids.append(process.pid)
            logger.info(f"Started FFmpeg encoder for Flow {flow_id}: PID {process.pid}")

        return pids

    def _build_srt_url(self, srt_output) -> str:
        """Build SRT URL from output config"""
        if srt_output.mode == "caller":
            url = f"srt://{srt_output.host}:{srt_output.port}"
        else:  # listener
            url = f"srt://0.0.0.0:{srt_output.port}"

        params = [
            f"mode={srt_output.mode}",
            f"latency={srt_output.latency_ms * 1000}"  # Convert to microseconds
        ]

        if srt_output.passphrase:
            params.append(f"passphrase={srt_output.passphrase}")

        return url + "?" + "&".join(params)

    def _stop_process(self, pid: int, process_name: str):
        """Stop a process gracefully"""
        try:
            if not psutil.pid_exists(pid):
                logger.warning(f"{process_name} process {pid} not found")
                return

            process = psutil.Process(pid)

            # Send SIGTERM
            process.terminate()

            # Wait up to 5 seconds for graceful shutdown
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                # Force kill if not stopped
                logger.warning(f"{process_name} process {pid} did not stop gracefully, killing")
                process.kill()

            logger.info(f"Stopped {process_name} process: {pid}")

        except psutil.NoSuchProcess:
            logger.warning(f"{process_name} process {pid} already stopped")
        except Exception as e:
            logger.error(f"Error stopping {process_name} process {pid}: {e}")
