"""
GPIO Daemon for Streon
Handles TCP/HTTP GPIO input/output for Flow automation
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Set
from aiohttp import web
import yaml

logger = logging.getLogger(__name__)


class GPIOEvent:
    """Represents a GPIO event"""

    def __init__(
        self,
        flow_id: str,
        direction: str,  # "input" or "output"
        event_type: str,  # START, STOP, SKIP, etc.
        payload: Optional[Dict] = None
    ):
        self.flow_id = flow_id
        self.direction = direction
        self.event_type = event_type
        self.payload = payload or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "flow_id": self.flow_id,
            "direction": self.direction,
            "type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class FlowGPIOHandler:
    """Handles GPIO for a single Flow"""

    def __init__(
        self,
        flow_id: str,
        tcp_input_port: Optional[int] = None,
        http_input_port: Optional[int] = None,
        tcp_output_host: Optional[str] = None,
        tcp_output_port: Optional[int] = None
    ):
        self.flow_id = flow_id
        self.tcp_input_port = tcp_input_port
        self.http_input_port = http_input_port
        self.tcp_output_host = tcp_output_host
        self.tcp_output_port = tcp_output_port

        self.tcp_server: Optional[asyncio.Server] = None
        self.http_app: Optional[web.Application] = None
        self.http_runner: Optional[web.AppRunner] = None
        self.tcp_output_writer: Optional[asyncio.StreamWriter] = None

        self.event_history: list[GPIOEvent] = []
        self.max_history = 1000

    async def start(self):
        """Start GPIO handlers for this Flow"""
        tasks = []

        if self.tcp_input_port:
            tasks.append(self._start_tcp_server())

        if self.http_input_port:
            tasks.append(self._start_http_server())

        if self.tcp_output_host and self.tcp_output_port:
            tasks.append(self._connect_tcp_output())

        if tasks:
            await asyncio.gather(*tasks)
            logger.info(f"GPIO handlers started for Flow {self.flow_id}")

    async def stop(self):
        """Stop all GPIO handlers"""
        if self.tcp_server:
            self.tcp_server.close()
            await self.tcp_server.wait_closed()

        if self.http_runner:
            await self.http_runner.cleanup()

        if self.tcp_output_writer:
            self.tcp_output_writer.close()
            await self.tcp_output_writer.wait_closed()

        logger.info(f"GPIO handlers stopped for Flow {self.flow_id}")

    async def _start_tcp_server(self):
        """Start TCP input server"""
        self.tcp_server = await asyncio.start_server(
            self._handle_tcp_client,
            '0.0.0.0',
            self.tcp_input_port
        )
        logger.info(f"TCP GPIO input server started on port {self.tcp_input_port} for Flow {self.flow_id}")

    async def _handle_tcp_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        """Handle incoming TCP GPIO connections"""
        addr = writer.get_extra_info('peername')
        logger.debug(f"TCP GPIO connection from {addr} for Flow {self.flow_id}")

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                message = data.decode('utf-8').strip()
                if not message:
                    continue

                # Parse GPIO command
                # Format: "TYPE:payload" or just "TYPE"
                parts = message.split(':', 1)
                event_type = parts[0].upper()
                payload = json.loads(parts[1]) if len(parts) > 1 else {}

                event = GPIOEvent(
                    flow_id=self.flow_id,
                    direction="input",
                    event_type=event_type,
                    payload=payload
                )

                await self._process_input_event(event)

                # Send acknowledgment
                writer.write(b"OK\n")
                await writer.drain()

        except Exception as e:
            logger.error(f"TCP GPIO error for Flow {self.flow_id}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _start_http_server(self):
        """Start HTTP input server"""
        self.http_app = web.Application()
        self.http_app.router.add_post('/gpio', self._handle_http_gpio)
        self.http_app.router.add_get('/gpio/status', self._handle_http_status)

        self.http_runner = web.AppRunner(self.http_app)
        await self.http_runner.setup()

        site = web.TCPSite(self.http_runner, '0.0.0.0', self.http_input_port)
        await site.start()

        logger.info(f"HTTP GPIO input server started on port {self.http_input_port} for Flow {self.flow_id}")

    async def _handle_http_gpio(self, request: web.Request) -> web.Response:
        """Handle HTTP GPIO POST requests"""
        try:
            data = await request.json()

            event_type = data.get('type', '').upper()
            payload = data.get('payload', {})

            if not event_type:
                return web.json_response({'error': 'Missing event type'}, status=400)

            event = GPIOEvent(
                flow_id=self.flow_id,
                direction="input",
                event_type=event_type,
                payload=payload
            )

            await self._process_input_event(event)

            return web.json_response({
                'status': 'ok',
                'event': event.to_dict()
            })

        except json.JSONDecodeError:
            return web.json_response({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"HTTP GPIO error for Flow {self.flow_id}: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def _handle_http_status(self, request: web.Request) -> web.Response:
        """Get GPIO status for this Flow"""
        return web.json_response({
            'flow_id': self.flow_id,
            'tcp_input_port': self.tcp_input_port,
            'http_input_port': self.http_input_port,
            'tcp_output_enabled': bool(self.tcp_output_host),
            'event_count': len(self.event_history),
            'recent_events': [e.to_dict() for e in self.event_history[-10:]]
        })

    async def _connect_tcp_output(self):
        """Connect to TCP output destination"""
        try:
            reader, writer = await asyncio.open_connection(
                self.tcp_output_host,
                self.tcp_output_port
            )
            self.tcp_output_writer = writer
            logger.info(f"TCP GPIO output connected to {self.tcp_output_host}:{self.tcp_output_port} for Flow {self.flow_id}")
        except Exception as e:
            logger.error(f"Failed to connect TCP GPIO output for Flow {self.flow_id}: {e}")

    async def _process_input_event(self, event: GPIOEvent):
        """Process an incoming GPIO event"""
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        logger.info(f"GPIO input for Flow {self.flow_id}: {event.event_type} - {event.payload}")

        # TODO: Forward to Flow automation logic
        # This could trigger actions like:
        # - START: Start playing a specific track
        # - STOP: Stop playback
        # - SKIP: Skip to next track
        # - FADE: Trigger crossfade
        # - VOLUME: Adjust volume

    async def send_output_event(self, event: GPIOEvent):
        """Send a GPIO output event"""
        if not self.tcp_output_writer:
            logger.warning(f"No TCP output configured for Flow {self.flow_id}")
            return

        try:
            message = f"{event.event_type}:{json.dumps(event.payload)}\n"
            self.tcp_output_writer.write(message.encode('utf-8'))
            await self.tcp_output_writer.drain()

            # Store in history
            event.direction = "output"
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)

            logger.info(f"GPIO output for Flow {self.flow_id}: {event.event_type}")

        except Exception as e:
            logger.error(f"Failed to send GPIO output for Flow {self.flow_id}: {e}")


class GPIODaemon:
    """Main GPIO daemon managing all Flow handlers"""

    def __init__(self, config_dir: str = "/etc/streon"):
        self.config_dir = config_dir
        self.flow_handlers: Dict[str, FlowGPIOHandler] = {}
        self.running = False

    async def start(self):
        """Start the GPIO daemon"""
        self.running = True
        logger.info("GPIO Daemon starting...")

        # Load all Flow configurations and start handlers
        await self._load_flows()

        logger.info(f"GPIO Daemon started with {len(self.flow_handlers)} Flow handlers")

    async def stop(self):
        """Stop the GPIO daemon"""
        self.running = False
        logger.info("GPIO Daemon stopping...")

        # Stop all Flow handlers
        tasks = [handler.stop() for handler in self.flow_handlers.values()]
        await asyncio.gather(*tasks)

        self.flow_handlers.clear()
        logger.info("GPIO Daemon stopped")

    async def _load_flows(self):
        """Load Flow configurations and create GPIO handlers"""
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
                gpio_config = flow_config['flow'].get('gpio', {})

                if not gpio_config.get('tcp_input', {}).get('enabled') and \
                   not gpio_config.get('http_input', {}).get('enabled') and \
                   not gpio_config.get('tcp_output', {}).get('enabled'):
                    # No GPIO configured for this Flow
                    continue

                # Create handler
                handler = FlowGPIOHandler(
                    flow_id=flow_id,
                    tcp_input_port=gpio_config.get('tcp_input', {}).get('port') if gpio_config.get('tcp_input', {}).get('enabled') else None,
                    http_input_port=gpio_config.get('http_input', {}).get('port') if gpio_config.get('http_input', {}).get('enabled') else None,
                    tcp_output_host=gpio_config.get('tcp_output', {}).get('host') if gpio_config.get('tcp_output', {}).get('enabled') else None,
                    tcp_output_port=gpio_config.get('tcp_output', {}).get('port') if gpio_config.get('tcp_output', {}).get('enabled') else None
                )

                await handler.start()
                self.flow_handlers[flow_id] = handler

                logger.info(f"Loaded GPIO handler for Flow: {flow_id}")

            except Exception as e:
                logger.error(f"Failed to load GPIO config from {flow_file}: {e}")

    async def reload_flow(self, flow_id: str):
        """Reload GPIO configuration for a specific Flow"""
        # Stop existing handler
        if flow_id in self.flow_handlers:
            await self.flow_handlers[flow_id].stop()
            del self.flow_handlers[flow_id]

        # Reload
        await self._load_flows()

    def get_flow_handler(self, flow_id: str) -> Optional[FlowGPIOHandler]:
        """Get GPIO handler for a Flow"""
        return self.flow_handlers.get(flow_id)


async def main():
    """Main entry point for GPIO daemon"""
    import sys
    import os

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/var/log/streon/gpio-daemon.log')
        ]
    )

    # Get config directory from environment
    config_dir = os.getenv('STREON_CONFIG_DIR', '/etc/streon')

    # Create and start daemon
    daemon = GPIODaemon(config_dir=config_dir)

    try:
        await daemon.start()

        # Run until interrupted
        while daemon.running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")

    finally:
        await daemon.stop()


if __name__ == "__main__":
    asyncio.run(main())
