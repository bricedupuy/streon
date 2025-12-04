#!/usr/bin/env python3
"""
FFmpeg SRT Decoder with GPIO Extraction Support

This script wraps FFmpeg to decode SRT streams with optional GPIO extraction.
GPIO data is extracted from subtitle tracks and sent to TCP endpoint.

Usage:
    ffmpeg-srt-gpio-decoder.py --flow-id FLOW_ID --config CONFIG_FILE
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

from utils.gpio_srt import GPIOSubtitleExtractor, GPIOTCPSender

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SRTGPIODecoder:
    """FFmpeg SRT decoder with GPIO extraction"""

    def __init__(
        self,
        flow_id: str,
        srt_input: dict,
        audio_output: str,  # ALSA device or FIFO
        gpio_config: Optional[dict] = None
    ):
        self.flow_id = flow_id
        self.srt_input = srt_input
        self.audio_output = audio_output
        self.gpio_config = gpio_config or {}

        self.ffmpeg_process: Optional[asyncio.subprocess.Process] = None
        self.gpio_sender: Optional[GPIOTCPSender] = None
        self.subtitle_file: Optional[Path] = None
        self.gpio_monitor_task: Optional[asyncio.Task] = None

        self.running = True

    async def start(self):
        """Start decoding process"""
        logger.info(f"Starting SRT decoder for Flow {self.flow_id}")

        # Setup GPIO extraction if enabled
        if self.gpio_config.get('gpio_extract', False):
            await self._setup_gpio_extraction()

        # Start FFmpeg decoder
        await self._start_ffmpeg()

        # Start GPIO monitoring if enabled
        if self.gpio_config.get('gpio_extract', False):
            self.gpio_monitor_task = asyncio.create_task(self._monitor_gpio())

    async def _setup_gpio_extraction(self):
        """Setup GPIO extraction infrastructure"""
        gpio_host = self.gpio_config.get('gpio_output_tcp_host')
        gpio_port = self.gpio_config.get('gpio_output_tcp_port')

        if not gpio_host or not gpio_port:
            logger.error("GPIO extraction enabled but no TCP endpoint specified")
            return

        # Setup subtitle extraction path
        self.subtitle_file = Path(f"/tmp/streon_{self.flow_id}_extracted_gpio.srt")

        # Create TCP sender for GPIO output
        self.gpio_sender = GPIOTCPSender(gpio_host, gpio_port)
        await self.gpio_sender.connect()

        logger.info(f"GPIO will be sent to {gpio_host}:{gpio_port}")

    async def _start_ffmpeg(self):
        """Start FFmpeg decoding process"""
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
        """Build FFmpeg command with GPIO subtitle extraction"""
        cmd = ['ffmpeg']

        # SRT input
        srt_url = self._build_srt_url()
        cmd.extend(['-i', srt_url])

        # Audio output
        cmd.extend(['-map', '0:a'])  # Map audio stream
        cmd.extend(['-c:a', 'pcm_s16le'])  # Decode to PCM
        cmd.extend(['-f', 'alsa', self.audio_output])

        # Extract subtitles if GPIO extraction is enabled
        if self.gpio_config.get('gpio_extract', False) and self.subtitle_file:
            cmd.extend(['-map', '0:s:0?'])  # Map subtitle stream if exists (optional)
            cmd.extend(['-c:s', 'srt'])  # Extract as SRT format
            cmd.append(str(self.subtitle_file))

        return cmd

    def _build_srt_url(self) -> str:
        """Build SRT URL from configuration"""
        srt_url = self.srt_input.get('srt_url')
        if srt_url:
            return srt_url

        # Build URL from components (for listener mode)
        mode = self.srt_input.get('mode', 'listener')
        port = self.srt_input.get('port', 9000)
        latency = self.srt_input.get('latency_ms', 200) * 1000

        if mode == 'caller':
            host = self.srt_input.get('host', 'localhost')
            url = f"srt://{host}:{port}"
        else:
            url = f"srt://0.0.0.0:{port}"

        params = [
            f"mode={mode}",
            f"latency={latency}"
        ]

        passphrase = self.srt_input.get('passphrase')
        if passphrase:
            params.append(f"passphrase={passphrase}")

        return url + "?" + "&".join(params)

    async def _monitor_gpio(self):
        """Monitor extracted subtitle file and send GPIO events"""
        if not self.subtitle_file or not self.gpio_sender:
            return

        logger.info("Starting GPIO monitoring")

        processed_events = set()

        while self.running:
            try:
                # Wait for subtitle file to exist
                if not self.subtitle_file.exists():
                    await asyncio.sleep(0.5)
                    continue

                # Extract GPIO events from subtitle file
                events = GPIOSubtitleExtractor.parse_srt_file(self.subtitle_file)

                # Send new events
                for event in events:
                    event_id = f"{event.timestamp_ms}_{event.event_type}"
                    if event_id not in processed_events:
                        await self.gpio_sender.send_event(event)
                        processed_events.add(event_id)

                await asyncio.sleep(0.1)  # Check every 100ms

            except Exception as e:
                logger.error(f"Error monitoring GPIO: {e}")
                await asyncio.sleep(1)

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
        """Monitor FFmpeg stderr"""
        if not self.ffmpeg_process or not self.ffmpeg_process.stderr:
            return

        while self.running:
            line = await self.ffmpeg_process.stderr.readline()
            if not line:
                break
            logger.debug(f"FFmpeg stderr: {line.decode().strip()}")

    async def stop(self):
        """Stop decoding process"""
        logger.info("Stopping SRT decoder")
        self.running = False

        # Stop GPIO monitoring
        if self.gpio_monitor_task:
            self.gpio_monitor_task.cancel()
            try:
                await self.gpio_monitor_task
            except asyncio.CancelledError:
                pass

        # Close GPIO sender
        if self.gpio_sender:
            await self.gpio_sender.close()

        # Stop FFmpeg
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            await self.ffmpeg_process.wait()

        # Cleanup subtitle file
        if self.subtitle_file and self.subtitle_file.exists():
            self.subtitle_file.unlink()

        logger.info("SRT decoder stopped")


async def main():
    parser = argparse.ArgumentParser(description='FFmpeg SRT Decoder with GPIO')
    parser.add_argument('--flow-id', required=True, help='Flow ID')
    parser.add_argument('--srt-config', required=True, help='SRT input config (JSON)')
    parser.add_argument('--audio-output', required=True, help='Audio output (ALSA device)')
    parser.add_argument('--gpio-config', help='GPIO config (JSON)')
    args = parser.parse_args()

    # Parse configs
    srt_config = json.loads(args.srt_config)
    gpio_config = json.loads(args.gpio_config) if args.gpio_config else {}

    # Create decoder
    decoder = SRTGPIODecoder(
        flow_id=args.flow_id,
        srt_input=srt_config,
        audio_output=args.audio_output,
        gpio_config=gpio_config
    )

    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Received signal, shutting down...")
        asyncio.create_task(decoder.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start decoder
    try:
        await decoder.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await decoder.stop()


if __name__ == '__main__':
    asyncio.run(main())
