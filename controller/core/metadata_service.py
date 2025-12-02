"""
Metadata Service for Streon
Handles real-time song metadata from Liquidsoap with WebSocket streaming
"""

import asyncio
import json
import logging
import telnetlib
from datetime import datetime
from typing import Dict, Optional, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class MetadataUpdate:
    """Represents a metadata update event"""

    def __init__(
        self,
        flow_id: str,
        artist: Optional[str] = None,
        title: Optional[str] = None,
        album: Optional[str] = None,
        duration_ms: Optional[int] = None,
        source: Optional[str] = None
    ):
        self.flow_id = flow_id
        self.artist = artist
        self.title = title
        self.album = album
        self.duration_ms = duration_ms
        self.source = source
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "flow_id": self.flow_id,
            "artist": self.artist,
            "title": self.title,
            "album": self.album,
            "duration_ms": self.duration_ms,
            "source": self.source,
            "timestamp": self.timestamp.isoformat()
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class FlowMetadataHandler:
    """Handles metadata for a single Flow"""

    def __init__(
        self,
        flow_id: str,
        liquidsoap_telnet_port: int = 1234
    ):
        self.flow_id = flow_id
        self.liquidsoap_telnet_port = liquidsoap_telnet_port

        self.current_metadata: Optional[MetadataUpdate] = None
        self.metadata_history: list[MetadataUpdate] = []
        self.max_history = 100

        self.running = False
        self.poll_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start polling Liquidsoap for metadata"""
        self.running = True
        self.poll_task = asyncio.create_task(self._poll_liquidsoap())
        logger.info(f"Metadata handler started for Flow {self.flow_id}")

    async def stop(self):
        """Stop metadata polling"""
        self.running = False
        if self.poll_task:
            self.poll_task.cancel()
            try:
                await self.poll_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Metadata handler stopped for Flow {self.flow_id}")

    async def _poll_liquidsoap(self):
        """Poll Liquidsoap telnet interface for metadata updates"""
        poll_interval = 1.0  # Poll every second

        while self.running:
            try:
                # Connect to Liquidsoap telnet interface
                # In production, each Flow would have its own telnet port
                metadata = await self._get_liquidsoap_metadata()

                if metadata:
                    update = MetadataUpdate(
                        flow_id=self.flow_id,
                        artist=metadata.get('artist'),
                        title=metadata.get('title'),
                        album=metadata.get('album'),
                        duration_ms=metadata.get('duration_ms'),
                        source=metadata.get('source', 'liquidsoap')
                    )

                    # Only update if different from current
                    if self._is_different_metadata(update):
                        self.current_metadata = update
                        self.metadata_history.append(update)

                        if len(self.metadata_history) > self.max_history:
                            self.metadata_history.pop(0)

                        logger.info(f"Metadata update for Flow {self.flow_id}: {update.artist} - {update.title}")

                        # Notify all WebSocket subscribers
                        await metadata_service.broadcast_metadata(self.flow_id, update)

            except Exception as e:
                logger.debug(f"Metadata poll error for Flow {self.flow_id}: {e}")

            await asyncio.sleep(poll_interval)

    async def _get_liquidsoap_metadata(self) -> Optional[Dict]:
        """
        Get current metadata from Liquidsoap telnet interface

        In production, this would connect to Liquidsoap's telnet interface
        and query for current metadata using commands like:
        - var.get metadata.artist
        - var.get metadata.title
        """
        # TODO: Implement actual Liquidsoap telnet connection
        # For now, return None (no metadata available)

        # Example implementation (when Liquidsoap is running):
        # try:
        #     tn = telnetlib.Telnet('localhost', self.liquidsoap_telnet_port, timeout=2)
        #     tn.write(b'var.get metadata.artist\n')
        #     artist = tn.read_until(b'\n', timeout=1).decode('utf-8').strip()
        #     tn.write(b'var.get metadata.title\n')
        #     title = tn.read_until(b'\n', timeout=1).decode('utf-8').strip()
        #     tn.close()
        #     return {'artist': artist, 'title': title}
        # except:
        #     return None

        return None

    def _is_different_metadata(self, update: MetadataUpdate) -> bool:
        """Check if metadata has changed"""
        if not self.current_metadata:
            return True

        return (
            self.current_metadata.artist != update.artist or
            self.current_metadata.title != update.title or
            self.current_metadata.album != update.album
        )

    def get_current_metadata(self) -> Optional[MetadataUpdate]:
        """Get current metadata for this Flow"""
        return self.current_metadata

    def get_metadata_history(self, limit: int = 10) -> list[MetadataUpdate]:
        """Get recent metadata history"""
        return self.metadata_history[-limit:]


class MetadataService:
    """Main metadata service managing all Flow handlers"""

    def __init__(self, config_dir: str = "/etc/streon"):
        self.config_dir = config_dir
        self.flow_handlers: Dict[str, FlowMetadataHandler] = {}
        self.websocket_clients: Set[WebSocket] = set()
        self.running = False

    async def start(self):
        """Start the metadata service"""
        self.running = True
        logger.info("Metadata Service starting...")

        # Load all Flow configurations and start handlers
        await self._load_flows()

        logger.info(f"Metadata Service started with {len(self.flow_handlers)} Flow handlers")

    async def stop(self):
        """Stop the metadata service"""
        self.running = False
        logger.info("Metadata Service stopping...")

        # Stop all Flow handlers
        tasks = [handler.stop() for handler in self.flow_handlers.values()]
        await asyncio.gather(*tasks)

        # Close all WebSocket connections
        for ws in self.websocket_clients:
            await ws.close()
        self.websocket_clients.clear()

        self.flow_handlers.clear()
        logger.info("Metadata Service stopped")

    async def _load_flows(self):
        """Load Flow configurations and create metadata handlers"""
        import yaml
        from pathlib import Path

        flows_dir = Path(self.config_dir) / "flows"
        if not flows_dir.exists():
            logger.warning(f"Flows directory not found: {flows_dir}")
            return

        for flow_file in flows_dir.glob("*.yaml"):
            try:
                with open(flow_file, 'r') as f:
                    flow_config = yaml.safe_load(f)

                flow_id = flow_config['flow']['id']
                metadata_config = flow_config['flow'].get('metadata', {})

                if not metadata_config.get('enabled', False):
                    continue

                # Create handler with unique telnet port per Flow
                # Base port 1234, increment by Flow index
                telnet_port = 1234 + len(self.flow_handlers)

                handler = FlowMetadataHandler(
                    flow_id=flow_id,
                    liquidsoap_telnet_port=telnet_port
                )

                await handler.start()
                self.flow_handlers[flow_id] = handler

                logger.info(f"Loaded metadata handler for Flow: {flow_id}")

            except Exception as e:
                logger.error(f"Failed to load metadata config from {flow_file}: {e}")

    async def reload_flow(self, flow_id: str):
        """Reload metadata configuration for a specific Flow"""
        if flow_id in self.flow_handlers:
            await self.flow_handlers[flow_id].stop()
            del self.flow_handlers[flow_id]

        await self._load_flows()

    def get_flow_handler(self, flow_id: str) -> Optional[FlowMetadataHandler]:
        """Get metadata handler for a Flow"""
        return self.flow_handlers.get(flow_id)

    def get_current_metadata(self, flow_id: str) -> Optional[MetadataUpdate]:
        """Get current metadata for a Flow"""
        handler = self.flow_handlers.get(flow_id)
        return handler.get_current_metadata() if handler else None

    def get_metadata_history(self, flow_id: str, limit: int = 10) -> list[MetadataUpdate]:
        """Get metadata history for a Flow"""
        handler = self.flow_handlers.get(flow_id)
        return handler.get_metadata_history(limit) if handler else []

    async def register_websocket(self, websocket: WebSocket):
        """Register a WebSocket client for metadata updates"""
        self.websocket_clients.add(websocket)
        logger.info(f"WebSocket client registered. Total clients: {len(self.websocket_clients)}")

    async def unregister_websocket(self, websocket: WebSocket):
        """Unregister a WebSocket client"""
        self.websocket_clients.discard(websocket)
        logger.info(f"WebSocket client unregistered. Total clients: {len(self.websocket_clients)}")

    async def broadcast_metadata(self, flow_id: str, metadata: MetadataUpdate):
        """Broadcast metadata update to all WebSocket clients"""
        if not self.websocket_clients:
            return

        message = metadata.to_json()
        disconnected = set()

        for ws in self.websocket_clients:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send metadata to WebSocket client: {e}")
                disconnected.add(ws)

        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_clients.discard(ws)

    async def inject_metadata(self, flow_id: str, metadata: Dict):
        """
        Manually inject metadata for a Flow
        Useful for testing or external metadata sources
        """
        update = MetadataUpdate(
            flow_id=flow_id,
            artist=metadata.get('artist'),
            title=metadata.get('title'),
            album=metadata.get('album'),
            duration_ms=metadata.get('duration_ms'),
            source=metadata.get('source', 'manual')
        )

        handler = self.flow_handlers.get(flow_id)
        if handler:
            handler.current_metadata = update
            handler.metadata_history.append(update)

            if len(handler.metadata_history) > handler.max_history:
                handler.metadata_history.pop(0)

        # Broadcast to WebSocket clients
        await self.broadcast_metadata(flow_id, update)


# Global metadata service instance
metadata_service = MetadataService()
