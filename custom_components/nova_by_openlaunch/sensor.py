"""Sensor platform for NOVA by Open Launch."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ALL_SENSORS,
    CONF_NAME,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_SERIAL,
    DOMAIN,
    NovaByOpenLaunchSensorEntityDescription,
)
from .coordinator import NovaByOpenLaunchCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NOVA by Open Launch sensors from a config entry."""
    coordinator: NovaByOpenLaunchCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data[CONF_NAME]

    entities = [
        NovaByOpenLaunchSensor(coordinator, description, entry, name)
        for description in ALL_SENSORS
    ]

    async_add_entities(entities)


class NovaByOpenLaunchSensor(
    CoordinatorEntity[NovaByOpenLaunchCoordinator], SensorEntity
):
    """Representation of a NOVA by Open Launch sensor."""

    entity_description: NovaByOpenLaunchSensorEntityDescription

    def __init__(
        self,
        coordinator: NovaByOpenLaunchCoordinator,
        description: NovaByOpenLaunchSensorEntityDescription,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._device_name = name
        self._entry = entry
        self._attr_native_value = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        # Get firmware version from coordinator's status data
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
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.connected

    def _apply_transforms(self, value: Any) -> Any:
        """Apply offset and precision transformations to value."""
        description = self.entity_description

        # Apply offset (e.g., +1 for 0-indexed counts)
        if description.value_offset and isinstance(value, (int, float)):
            value = value + description.value_offset

        # Apply precision rounding
        if description.precision is not None and isinstance(value, (int, float)):
            rounded = round(value, description.precision)
            # Convert to int if precision is 0 to avoid "123.0" display
            if description.precision == 0:
                return int(rounded)
            return rounded

        return value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return

        update_info = self.coordinator.data
        msg_type = update_info.get("type")
        data = update_info.get("data", {})

        description = self.entity_description

        # Only update if this sensor matches the message type
        if description.message_type == msg_type and description.json_key:
            value = data.get(description.json_key)
            if value is not None:
                self._attr_native_value = self._apply_transforms(value)
                self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        # On first load, check if we have cached data
        if self._attr_native_value is None:
            description = self.entity_description
            if description.message_type == "shot" and description.json_key:
                value = self.coordinator.shot_data.get(description.json_key)
                if value is not None:
                    self._attr_native_value = self._apply_transforms(value)
            elif description.message_type == "status" and description.json_key:
                value = self.coordinator.status_data.get(description.json_key)
                if value is not None:
                    self._attr_native_value = self._apply_transforms(value)

        return self._attr_native_value
