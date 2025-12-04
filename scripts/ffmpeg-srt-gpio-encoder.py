#!/usr/bin/env python3
"""
FFmpeg SRT Encoder with GPIO Embedding Support

This script wraps FFmpeg to encode audio to SRT with optional GPIO embedding.
GPIO data is embedded as subtitle tracks in the Matroska container.

Usage:
    ffmpeg-srt-gpio-encoder.py --flow-id FLOW_ID --config CONFIG_FILE
"""

import sys
import os
import asyncio
import argparse
import json
import signal
import logging
from pathlib import Path
from typing import Optional

# Add controller to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'controller'))

from utils.gpio_srt import GPIOSubtitleGenerator, GPIOTCPReceiver

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SRTGPIOEncoder:
    """FFmpeg SRT encoder with GPIO embedding"""

    def __init__(
        self,
        flow_id: str,
        fifo_input: Path,
        srt_output: dict,
        gpio_config: Optional[dict] = None
    ):
        self.flow_id = flow_id
        self.fifo_input = fifo_input
        self.srt_output = srt_output
        self.gpio_config = gpio_config or {}

        self.ffmpeg_process: Optional[asyncio.subprocess.Process] = None
        self.gpio_receiver: Optional[GPIOTCPReceiver] = None
        self.subtitle_generator: Optional[GPIOSubtitleGenerator] = None
        self.subtitle_file: Optional[Path] = None

        self.running = True

    async def start(self):
        """Start encoding process"""
        logger.info(f"Starting SRT encoder for Flow {self.flow_id}")

        # Setup GPIO embedding if enabled
        if self.gpio_config.get('gpio_embed', False):
            await self._setup_gpio_embedding()

        # Start FFmpeg encoder
        await self._start_ffmpeg()

    async def _setup_gpio_embedding(self):
        """Setup GPIO embedding infrastructure"""
        gpio_port = self.gpio_config.get('gpio_input_tcp_port')
        if not gpio_port:
            logger.error("GPIO embedding enabled but no TCP port specified")
            return

        # Create subtitle generator
        self.subtitle_file = Path(f"/tmp/streon_{self.flow_id}_gpio.srt")
        self.subtitle_generator = GPIOSubtitleGenerator(self.subtitle_file)

        # Start TCP receiver for GPIO events
        self.gpio_receiver = GPIOTCPReceiver(gpio_port, self.subtitle_generator)
        await self.gpio_receiver.start()

        logger.info(f"GPIO TCP receiver listening on port {gpio_port}")

    async def _start_ffmpeg(self):
        """Start FFmpeg encoding process"""
        # Build FFmpeg command
        cmd = self._build_ffmpeg_command()

        logger.info(f"FFmpeg command: {' '.join(cmd)}")

        # Start FFmpeg process
        self.ffmpeg_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Monitor output
        await asyncio.gather(
            self._monitor_stdout(),
            self._monitor_stderr()
        )

    def _build_ffmpeg_command(self) -> list:
        """Build FFmpeg command with GPIO subtitle embedding"""
        cmd = ['ffmpeg']

        # Input from FIFO
        cmd.extend(['-f', 'wav', '-i', str(self.fifo_input)])

        # Add subtitle input if GPIO embedding is enabled
        if self.gpio_config.get('gpio_embed', False) and self.subtitle_file:
            cmd.extend(['-i', str(self.subtitle_file)])

        # Audio codec
        codec = self.srt_output.get('codec', 'opus')
        bitrate = self.srt_output.get('bitrate_kbps', 128)

        if codec == 'opus':
            cmd.extend([
                '-c:a', 'libopus',
                '-b:a', f'{bitrate}k',
                '-application', 'audio',
                '-vbr', 'on'
            ])
        elif codec == 'aac':
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', f'{bitrate}k',
                '-profile:a', 'aac_low'
            ])
        elif codec == 'pcm':
            cmd.extend(['-c:a', 'pcm_s16le'])

        # Map streams
        cmd.extend(['-map', '0:a'])  # Map audio from first input

        if self.gpio_config.get('gpio_embed', False) and self.subtitle_file:
            cmd.extend(['-map', '1:s:0'])  # Map subtitles from second input
            cmd.extend(['-c:s', 'mov_text'])  # Subtitle codec for Matroska

        # Container format
        container = self.srt_output.get('container', 'matroska')
        cmd.extend(['-f', container])

        # Metadata
        cmd.extend(['-metadata', f'flow_id={self.flow_id}'])

        # SRT URL
        srt_url = self._build_srt_url()
        cmd.append(srt_url)

        return cmd

    def _build_srt_url(self) -> str:
        """Build SRT URL from configuration"""
        mode = self.srt_output['mode']
        port = self.srt_output['port']
        latency = self.srt_output.get('latency_ms', 200) * 1000  # Convert to microseconds

        if mode == 'caller':
            host = self.srt_output['host']
            url = f"srt://{host}:{port}"
        else:
            url = f"srt://0.0.0.0:{port}"

        # Add parameters
        params = [
            f"mode={mode}",
            f"latency={latency}"
        ]

        passphrase = self.srt_output.get('passphrase')
        if passphrase:
            params.append(f"passphrase={passphrase}")

        return url + "?" + "&".join(params)

    async def _monitor_stdout(self):
        """Monitor FFmpeg stdout"""
        if not self.ffmpeg_process or not self.ffmpeg_process.stdout:
            return

        while self.running:
            line = await self.ffmpeg_process.stdout.readline()
            if not line:
                break
            logger.debug(f"FFmpeg stdout: {line.decode().strip()}")

    async def _monitor_stderr(self):
        """Monitor FFmpeg stderr for stats"""
        if not self.ffmpeg_process or not self.ffmpeg_process.stderr:
            return

        while self.running:
            line = await self.ffmpeg_process.stderr.readline()
            if not line:
                break
            logger.debug(f"FFmpeg stderr: {line.decode().strip()}")

    async def stop(self):
        """Stop encoding process"""
        logger.info("Stopping SRT encoder")
        self.running = False

        # Generate final subtitle file if GPIO was used
        if self.subtitle_generator:
            self.subtitle_generator.generate_srt_file()

        # Stop GPIO receiver
        if self.gpio_receiver:
            await self.gpio_receiver.stop()

        # Stop FFmpeg
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            await self.ffmpeg_process.wait()

        logger.info("SRT encoder stopped")


async def main():
    parser = argparse.ArgumentParser(description='FFmpeg SRT Encoder with GPIO')
    parser.add_argument('--flow-id', required=True, help='Flow ID')
    parser.add_argument('--fifo-input', required=True, help='FIFO input path')
    parser.add_argument('--srt-config', required=True, help='SRT output config (JSON)')
    parser.add_argument('--gpio-config', help='GPIO config (JSON)')
    args = parser.parse_args()

    # Parse configs
    srt_config = json.loads(args.srt_config)
    gpio_config = json.loads(args.gpio_config) if args.gpio_config else {}

    # Create encoder
    encoder = SRTGPIOEncoder(
        flow_id=args.flow_id,
        fifo_input=Path(args.fifo_input),
        srt_output=srt_config,
        gpio_config=gpio_config
    )

    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Received signal, shutting down...")
        asyncio.create_task(encoder.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start encoder
    try:
        await encoder.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await encoder.stop()


if __name__ == '__main__':
    asyncio.run(main())
