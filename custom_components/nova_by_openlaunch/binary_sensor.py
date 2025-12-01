"""Binary sensor platform for NOVA by Open Launch."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_NAME,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_SERIAL,
    DOMAIN,
)
from .coordinator import NovaByOpenLaunchCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NOVA by Open Launch binary sensors from a config entry."""
    coordinator: NovaByOpenLaunchCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data[CONF_NAME]

    async_add_entities([NovaByOpenLaunchConnectionSensor(coordinator, entry, name)])


class NovaByOpenLaunchConnectionSensor(
    CoordinatorEntity[NovaByOpenLaunchCoordinator], BinarySensorEntity
):
    """Binary sensor showing connection status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = "Connection"

    def __init__(
        self,
        coordinator: NovaByOpenLaunchCoordinator,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connection"
        self._device_name = name
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        fw_version = self.coordinator.status_data.get("firmware_version")

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._device_name,
            manufacturer=self._entry.data.get(CONF_MANUFACTURER, "Open Launch"),
            model=self._entry.data.get(CONF_MODEL, "NOVA"),
            serial_number=self._entry.data.get(CONF_SERIAL),
            sw_version=fw_version,
        )

    @property
    def is_on(self) -> bool:
        """Return True if connected."""
        return self.coordinator.connected

    @property
    def available(self) -> bool:
        """Return True - this sensor is always available."""
        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
