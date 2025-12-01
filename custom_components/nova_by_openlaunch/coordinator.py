"""Data coordinator for NOVA by Open Launch."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any

import websockets
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, RECONNECT_INTERVAL

_LOGGER = logging.getLogger(__name__)


class NovaByOpenLaunchCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage WebSocket connection to NOVA by Open Launch."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        name: str,
        manufacturer: str | None = None,
        model: str | None = None,
        serial: str | None = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}",
        )
        self.host = host
        self.port = port
        self.device_name = name
        self.manufacturer = manufacturer or "Open Launch"
        self.model = model or "NOVA"
        self.serial = serial

        self._websocket: WebSocketClientProtocol | None = None
        self._listen_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._running = False
        self._connected = False

        # Store latest data by message type
        self._shot_data: dict[str, Any] = {}
        self._status_data: dict[str, Any] = {}

    @property
    def connected(self) -> bool:
        """Return connection status."""
        return self._connected

    @property
    def shot_data(self) -> dict[str, Any]:
        """Return latest shot data."""
        return self._shot_data

    @property
    def status_data(self) -> dict[str, Any]:
        """Return latest status data."""
        return self._status_data

    async def async_start(self) -> None:
        """Start the coordinator and connect to device."""
        self._running = True
        await self._connect()

    async def async_stop(self) -> None:
        """Stop the coordinator and disconnect."""
        self._running = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None
        await self._disconnect()

    async def _connect(self) -> bool:
        """Connect to the device via WebSocket."""
        uri = f"ws://{self.host}:{self.port}"
        try:
            _LOGGER.debug("Connecting to %s", uri)
            self._websocket = await asyncio.wait_for(
                websockets.connect(uri),
                timeout=10.0,
            )
            self._connected = True
            _LOGGER.info("Connected to NOVA by Open Launch at %s", uri)
            # Notify entities of connection state change
            self.async_set_updated_data({"type": "connection", "data": {}})

            # Start listening for messages
            self._listen_task = asyncio.create_task(self._listen())
            return True
        except (OSError, asyncio.TimeoutError, ConnectionRefusedError) as err:
            _LOGGER.warning("Failed to connect to %s: %s", uri, err)
            self._connected = False
            self._schedule_reconnect()
            return False

    async def _disconnect(self) -> None:
        """Disconnect from the device."""
        was_connected = self._connected
        self._connected = False
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:  # noqa: BLE001
                pass
            self._websocket = None
        _LOGGER.debug("Disconnected from NOVA by Open Launch")
        # Notify entities of connection state change
        if was_connected:
            self.async_set_updated_data({"type": "connection", "data": {}})

    def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt."""
        if not self._running:
            return
        if self._reconnect_task and not self._reconnect_task.done():
            return
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        """Keep attempting to reconnect until successful or stopped."""
        while self._running and not self._connected:
            await asyncio.sleep(RECONNECT_INTERVAL)
            if not self._running:
                break
            _LOGGER.debug("Attempting to reconnect...")
            try:
                uri = f"ws://{self.host}:{self.port}"
                self._websocket = await asyncio.wait_for(
                    websockets.connect(uri),
                    timeout=10.0,
                )
                self._connected = True
                _LOGGER.info("Reconnected to NOVA by Open Launch at %s", uri)
                # Notify entities of connection state change
                self.async_set_updated_data({"type": "connection", "data": {}})
                # Start listening for messages
                self._listen_task = asyncio.create_task(self._listen())
                break
            except (OSError, asyncio.TimeoutError, ConnectionRefusedError) as err:
                _LOGGER.debug("Reconnect failed: %s, will retry in %s seconds", err, RECONNECT_INTERVAL)

    async def _listen(self) -> None:
        """Listen for incoming WebSocket messages."""
        try:
            while self._running and self._websocket:
                try:
                    message = await self._websocket.recv()
                    await self._process_message(message)
                except ConnectionClosedOK:
                    _LOGGER.info("WebSocket connection closed normally")
                    break
                except ConnectionClosedError as err:
                    _LOGGER.warning("WebSocket connection closed with error: %s", err)
                    break
                except ConnectionClosed:
                    _LOGGER.warning("WebSocket connection closed")
                    break
                except asyncio.CancelledError:
                    raise
                except Exception as err:  # noqa: BLE001
                    _LOGGER.error("Error receiving WebSocket message: %s", err)
                    break
        finally:
            await self._disconnect()
            self._schedule_reconnect()

    async def _process_message(self, message: str) -> None:
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "unknown")

            _LOGGER.debug("Received %s message: %s", msg_type, data)

            if msg_type == "shot":
                # Add timestamp for "last shot" sensor
                data["_last_shot_timestamp"] = datetime.now(timezone.utc)
                self._shot_data = data
                self.async_set_updated_data({"type": "shot", "data": data})
            elif msg_type == "status":
                self._status_data = data
                self.async_set_updated_data({"type": "status", "data": data})
            else:
                _LOGGER.warning("Unknown message type: %s", msg_type)

        except json.JSONDecodeError as err:
            _LOGGER.error("Failed to parse JSON message: %s", err)

    async def async_test_connection(self) -> bool:
        """Test connection to the device."""
        uri = f"ws://{self.host}:{self.port}"
        try:
            websocket = await asyncio.wait_for(
                websockets.connect(uri),
                timeout=10.0,
            )
            await websocket.close()
            return True
        except (OSError, asyncio.TimeoutError, ConnectionRefusedError):
            return False
