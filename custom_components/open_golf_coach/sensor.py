"""Sensors for Open Golf Coach derived shot insights."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .analysis import analyze_shot
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Open Golf Coach sensors from a config entry."""
    state = hass.data[DOMAIN][entry.entry_id]
    coordinator = state["coordinator"]

    entities: list[SensorEntity] = [OpenGolfCoachLastShotSensor(coordinator, entry, state)]

    async_add_entities(entities)


def _shot_id(shot: dict[str, Any]) -> str | int | None:
    if "shot_number" in shot:
        return shot.get("shot_number")
    if "timestamp_ns" in shot:
        return shot.get("timestamp_ns")
    if "_last_shot_timestamp" in shot:
        return shot.get("_last_shot_timestamp")
    return None


def _decorate_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    return analysis or {}


class OpenGolfCoachBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Open Golf Coach sensors."""

    def __init__(self, coordinator, entry: ConfigEntry, state: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._state_store = state
        self._attr_has_entity_name = True
        self._attr_native_value = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Open Golf Coach",
            manufacturer="Open Launch",
            model="Open Golf Coach",
        )

    def _ensure_analysis(self) -> None:
        update_info = self.coordinator.data
        if not update_info or update_info.get("type") != "shot":
            return
        shot = update_info.get("data", {})
        shot_id = _shot_id(shot)
        if shot_id is None:
            return
        if shot_id == self._state_store.get("last_shot_id"):
            return
        analysis = analyze_shot(shot, handedness="RH")
        self._state_store["analysis"] = _decorate_analysis(analysis)
        self._state_store["last_shot_id"] = shot_id

    def _set_native_from_analysis(self, analysis: dict[str, Any]) -> None:
        """Set native value from analysis payload."""

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._ensure_analysis()
        analysis = self._state_store.get("analysis")
        if analysis:
            self._set_native_from_analysis(analysis)


class OpenGolfCoachLastShotSensor(OpenGolfCoachBaseSensor):
    """Rich last shot sensor with analysis attributes."""

    _attr_name = "Open Golf Coach Last Shot"

    def __init__(self, coordinator, entry: ConfigEntry, state: dict[str, Any]) -> None:
        super().__init__(coordinator, entry, state)
        self._attr_unique_id = f"{entry.entry_id}_open_golf_coach_last_shot"

    @callback
    def _handle_coordinator_update(self) -> None:
        self._ensure_analysis()
        analysis = self._state_store.get("analysis")
        if analysis:
            self._set_native_from_analysis(analysis)
            self.async_write_ha_state()

    def _set_native_from_analysis(self, analysis: dict[str, Any]) -> None:
        self._attr_native_value = analysis.get("inferred", {}).get("shot_shape")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        analysis = self._state_store.get("analysis") or {}
        if not analysis:
            return {}
        return {
            **analysis,
            "data_sources": {
                "measured": list(analysis.get("measured", {}).keys()),
                "derived": list(analysis.get("derived", {}).keys()),
            },
        }

