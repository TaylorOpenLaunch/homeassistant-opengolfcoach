"""Config flow for NOVA by Open Launch integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
import websockets

from homeassistant.components import ssdp
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME

from .const import (
    DEFAULT_PORT,
    DOMAIN,
    SSDP_ST,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_SERIAL,
)

_LOGGER = logging.getLogger(__name__)


class NovaByOpenLaunchConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NOVA by Open Launch."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_host: str | None = None
        self._discovered_port: int | None = None
        self._discovered_name: str | None = None
        self._discovered_manufacturer: str | None = None
        self._discovered_model: str | None = None
        self._discovered_serial: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step (manual configuration)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            if await self._test_connection(host, port):
                unique_id = f"{host}:{port}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_MANUFACTURER: "Open Launch",
                        CONF_MODEL: "NOVA",
                    },
                )
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default="NOVA by Open Launch"): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )

    async def async_step_ssdp(
        self, discovery_info: ssdp.SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle SSDP discovery."""
        _LOGGER.debug("SSDP discovery: %s", discovery_info)

        # Extract device info from SSDP headers
        location = discovery_info.ssdp_location or ""
        parsed = urlparse(location)

        self._discovered_host = parsed.hostname or discovery_info.ssdp_headers.get(
            "X-HOSTNAME", ""
        )
        self._discovered_port = parsed.port or DEFAULT_PORT

        # Extract device code from X-HOSTNAME (e.g., "openlaunch-novaj03c" -> "j03c")
        # Use this to create a friendly default name like "NOVA j03c"
        hostname = discovery_info.ssdp_headers.get("X-HOSTNAME", "")
        device_code = None
        if hostname.startswith("openlaunch-nova"):
            device_code = hostname[len("openlaunch-nova"):]

        if device_code:
            self._discovered_name = f"NOVA {device_code}"
        else:
            # Fall back to X-FRIENDLY-NAME or default
            self._discovered_name = discovery_info.ssdp_headers.get(
                "X-FRIENDLY-NAME", "NOVA by Open Launch"
            )
        self._discovered_manufacturer = discovery_info.ssdp_headers.get(
            "X-MANUFACTURER", "Open Launch"
        )
        self._discovered_model = discovery_info.ssdp_headers.get("X-MODEL", "NOVA")

        # Use hostname as serial (e.g., "openlaunch-novaj03c")
        self._discovered_serial = hostname if hostname else None

        if not self._discovered_host:
            return self.async_abort(reason="no_host")

        # Set unique ID based on serial or host:port
        unique_id = self._discovered_serial or f"{self._discovered_host}:{self._discovered_port}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(
            updates={
                CONF_HOST: self._discovered_host,
                CONF_PORT: self._discovered_port,
            }
        )

        # Show confirmation dialog
        self.context["title_placeholders"] = {"name": self._discovered_name}

        return await self.async_step_ssdp_confirm()

    async def async_step_ssdp_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user confirmation of SSDP discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if await self._test_connection(
                self._discovered_host, self._discovered_port
            ):
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, self._discovered_name),
                    data={
                        CONF_NAME: user_input.get(CONF_NAME, self._discovered_name),
                        CONF_HOST: self._discovered_host,
                        CONF_PORT: self._discovered_port,
                        CONF_MANUFACTURER: self._discovered_manufacturer,
                        CONF_MODEL: self._discovered_model,
                        CONF_SERIAL: self._discovered_serial,
                    },
                )
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="ssdp_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=self._discovered_name
                    ): str,
                }
            ),
            description_placeholders={
                "host": self._discovered_host,
                "port": str(self._discovered_port),
                "model": self._discovered_model,
                "manufacturer": self._discovered_manufacturer,
            },
            errors=errors,
        )

    async def _test_connection(self, host: str, port: int) -> bool:
        """Test if we can connect to the device via WebSocket."""
        uri = f"ws://{host}:{port}"
        try:
            websocket = await asyncio.wait_for(
                websockets.connect(uri),
                timeout=10.0,
            )
            await websocket.close()
            return True
        except (OSError, asyncio.TimeoutError, ConnectionRefusedError) as err:
            _LOGGER.debug("Connection test failed: %s", err)
            return False
