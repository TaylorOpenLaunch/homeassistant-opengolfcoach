"""The Open Golf Coach integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

try:
    from homeassistant.const import Platform
except ModuleNotFoundError:  # pragma: no cover - used for local self-checks
    class Platform(str):  # type: ignore
        """Fallback platform enum for self-check execution."""

        SENSOR = "sensor"

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .const import CONF_NOVA_ENTRY_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

NOVA_DOMAIN = "nova_by_openlaunch"


async def async_setup_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    """Set up Open Golf Coach from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    nova_entry_id = entry.data.get(CONF_NOVA_ENTRY_ID)
    nova_entries = hass.data.get(NOVA_DOMAIN, {})

    if not nova_entries:
        _LOGGER.error("No NOVA by Open Launch coordinator found")
        return False

    if not nova_entry_id:
        nova_entry_id = next(iter(nova_entries))
        _LOGGER.warning("Open Golf Coach defaulting to first NOVA entry: %s", nova_entry_id)

    coordinator = nova_entries.get(nova_entry_id)
    if not coordinator:
        _LOGGER.error("NOVA entry %s not found", nova_entry_id)
        return False

    hass.data[DOMAIN][entry.entry_id] = {
        "nova_entry_id": nova_entry_id,
        "coordinator": coordinator,
        "analysis": None,
        "last_shot_id": None,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    """Unload an Open Golf Coach config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
