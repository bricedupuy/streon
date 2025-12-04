"""GPIO SRT Embedding/Extraction Utilities

This module provides utilities for embedding and extracting GPIO data
in/from SRT streams using FFmpeg subtitle tracks or data tracks.

GPIO Data Format:
-----------------
GPIO events are encoded as JSON in subtitle tracks (format: SubRip .srt)

Subtitle format:
    1
    00:00:10,500 --> 00:00:10,600
    {"type":"START","payload":{"channel":1}}

Each GPIO event gets a 100ms subtitle entry with JSON payload.
"""

import json
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class GPIOEvent:
    """GPIO Event for SRT embedding/extraction"""

    def __init__(
        self,
        event_type: str,
        timestamp_ms: int,
        payload: Optional[Dict] = None
    ):
        self.event_type = event_type
        self.timestamp_ms = timestamp_ms
        self.payload = payload or {}

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            "type": self.event_type,
            "timestamp_ms": self.timestamp_ms,
            "payload": self.payload
        })

    @staticmethod
    def from_json(json_str: str) -> 'GPIOEvent':
        """Parse from JSON string"""
        data = json.loads(json_str)
        return GPIOEvent(
            event_type=data["type"],
            timestamp_ms=data.get("timestamp_ms", 0),
            payload=data.get("payload", {})
        )

    def to_tcp_message(self) -> str:
        """Convert to TCP message format"""
        if self.payload:
            return f"{self.event_type}:{json.dumps(self.payload)}\n"
        return f"{self.event_type}\n"


class GPIOSubtitleGenerator:
    """Generates SRT subtitle file from GPIO events for FFmpeg embedding"""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.events: List[GPIOEvent] = []
        self.sequence = 1

    def add_event(self, event: GPIOEvent):
        """Add GPIO event to subtitle stream"""
        self.events.append(event)

    def _format_timestamp(self, ms: int) -> str:
        """Format milliseconds to SRT timestamp (HH:MM:SS,mmm)"""
        td = timedelta(milliseconds=ms)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = ms % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def generate_srt_file(self):
        """Generate SRT subtitle file from events"""
        with open(self.output_path, 'w', encoding='utf-8') as f:
            for idx, event in enumerate(self.events, start=1):
                # Each subtitle entry lasts 100ms
                start_ts = self._format_timestamp(event.timestamp_ms)
                end_ts = self._format_timestamp(event.timestamp_ms + 100)

                f.write(f"{idx}\n")
                f.write(f"{start_ts} --> {end_ts}\n")
                f.write(f"{event.to_json()}\n")
                f.write("\n")

        logger.info(f"Generated SRT subtitle file with {len(self.events)} GPIO events: {self.output_path}")


class GPIOSubtitleExtractor:
    """Extracts GPIO events from SRT subtitle track"""

    @staticmethod
    def parse_srt_file(srt_path: Path) -> List[GPIOEvent]:
        """Parse SRT file and extract GPIO events"""
        events = []

        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by double newline (subtitle entries)
        entries = content.strip().split('\n\n')

        for entry in entries:
            lines = entry.strip().split('\n')
            if len(lines) < 3:
                continue

            # Line 0: sequence number
            # Line 1: timestamp
            # Line 2: JSON payload
            try:
                json_data = lines[2]
                event = GPIOEvent.from_json(json_data)
                events.append(event)
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logger.warning(f"Failed to parse GPIO event from subtitle: {e}")
                continue

        logger.info(f"Extracted {len(events)} GPIO events from {srt_path}")
        return events


class GPIOTCPSender:
    """Sends extracted GPIO events to TCP endpoint"""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False

    async def connect(self):
        """Connect to TCP endpoint"""
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
            self.writer = writer
            self.connected = True
            logger.info(f"GPIO TCP sender connected to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect GPIO TCP sender to {self.host}:{self.port}: {e}")
            raise

    async def send_event(self, event: GPIOEvent):
        """Send GPIO event to TCP endpoint"""
        if not self.connected or not self.writer:
            logger.warning("GPIO TCP sender not connected")
            return

        try:
            message = event.to_tcp_message()
            self.writer.write(message.encode('utf-8'))
            await self.writer.drain()
            logger.debug(f"Sent GPIO event: {event.event_type}")
        except Exception as e:
            logger.error(f"Failed to send GPIO event: {e}")
            self.connected = False

    async def close(self):
        """Close TCP connection"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.connected = False


class GPIOTCPReceiver:
    """Receives GPIO events from TCP for embedding in SRT"""

    def __init__(self, port: int, subtitle_generator: GPIOSubtitleGenerator):
        self.port = port
        self.subtitle_generator = subtitle_generator
        self.server: Optional[asyncio.Server] = None
        self.start_time = datetime.utcnow()

    async def start(self):
        """Start TCP server for receiving GPIO events"""
        self.server = await asyncio.start_server(
            self._handle_client,
            '0.0.0.0',
            self.port
        )
        logger.info(f"GPIO TCP receiver listening on port {self.port}")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming TCP connection"""
        addr = writer.get_extra_info('peername')
        logger.debug(f"GPIO TCP connection from {addr}")

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                message = data.decode('utf-8').strip()
                if not message:
                    continue

                # Parse: "TYPE:payload" or just "TYPE"
                parts = message.split(':', 1)
                event_type = parts[0].upper()
                payload = json.loads(parts[1]) if len(parts) > 1 else {}

                # Calculate timestamp relative to stream start
                elapsed = (datetime.utcnow() - self.start_time).total_seconds() * 1000
                timestamp_ms = int(elapsed)

                # Add to subtitle generator
                event = GPIOEvent(
                    event_type=event_type,
                    timestamp_ms=timestamp_ms,
                    payload=payload
                )
                self.subtitle_generator.add_event(event)

                # Send acknowledgment
                writer.write(b"OK\n")
                await writer.drain()

        except Exception as e:
            logger.error(f"Error handling GPIO TCP client: {e}")
        finally:
            writer.close()

    async def stop(self):
        """Stop TCP server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()


def create_ffmpeg_subtitle_input_args(srt_file: Path) -> List[str]:
    """Generate FFmpeg args for subtitle input"""
    return [
        '-i', str(srt_file),
        '-map', '1:s:0',  # Map subtitle track
        '-c:s', 'mov_text',  # Subtitle codec for Matroska
    ]


def create_ffmpeg_subtitle_extract_args(output_srt: Path) -> List[str]:
    """Generate FFmpeg args for subtitle extraction"""
    return [
        '-map', '0:s:0?',  # Map subtitle track if exists (optional)
        '-c:s', 'srt',  # Extract as SRT format
        str(output_srt)
    ]
