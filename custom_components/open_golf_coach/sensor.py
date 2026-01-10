"""Sensors for Open Golf Coach derived shot insights."""
from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .rust_adapter import analyze_shot
from .analysis.benchmarks import get_cohort_metric_window
from .const import COHORT_PGA, DOMAIN, NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Open Golf Coach sensors from a config entry."""
    state = hass.data[DOMAIN][entry.entry_id]
    coordinator = state["coordinator"]

    entities: list[SensorEntity] = [
        OpenGolfCoachLastShotSensor(coordinator, entry, state),
        *[OpenGolfCoachCompatSensor(coordinator, entry, state, description) for description in COMPAT_SENSORS],
    ]

    async_add_entities(entities)


def _shot_id(shot: dict[str, Any]) -> str | int | None:
    if "shot_number" in shot:
        return shot.get("shot_number")
    if "timestamp_ns" in shot:
        return shot.get("timestamp_ns")
    if "_last_shot_timestamp" in shot:
        return shot.get("_last_shot_timestamp")
    return None


class OpenGolfCoachSensorEntityDescription:
    """Describes an Open Golf Coach sensor entity."""

    def __init__(
        self,
        key: str,
        name: str,
        value_fn: Callable[[dict[str, Any]], Any],
    ) -> None:
        self.key = key
        self.name = name
        self.value_fn = value_fn


COMPAT_SENSORS: tuple[OpenGolfCoachSensorEntityDescription, ...] = (
    OpenGolfCoachSensorEntityDescription(
        key="nova_shot_type",
        name="NOVA Shot Type",
        value_fn=lambda analysis: analysis.get("inferred", {}).get("shot_shape"),
    ),
    OpenGolfCoachSensorEntityDescription(
        key="nova_shot_rank",
        name="NOVA Shot Rank",
        value_fn=lambda analysis: analysis.get("inferred", {}).get("severity"),
    ),
    OpenGolfCoachSensorEntityDescription(
        key="nova_nova_shot_quality",
        name="NOVA Nova Shot Quality",
        value_fn=lambda analysis: analysis.get("derived", {}).get("shot_quality"),
    ),
    OpenGolfCoachSensorEntityDescription(
        key="nova_launch_in_window",
        name="NOVA Launch In Window",
        value_fn=lambda analysis: analysis.get("derived", {}).get("launch_in_window"),
    ),
    OpenGolfCoachSensorEntityDescription(
        key="nova_spin_in_window",
        name="NOVA Spin In Window",
        value_fn=lambda analysis: analysis.get("derived", {}).get("spin_in_window"),
    ),
    OpenGolfCoachSensorEntityDescription(
        key="nova_start_line_in_window",
        name="NOVA Start Line In Window",
        value_fn=lambda analysis: analysis.get("derived", {}).get("start_line_in_window"),
    ),
)


def _compute_shot_quality(analysis: dict[str, Any]) -> str | None:
    measured = analysis.get("measured", {})
    club_category = analysis.get("inferred", {}).get("club_category")

    in_window = 0
    total = 0
    for metric, shot_key in (
        ("ball_speed", "ball_speed_mps"),
        ("vertical_launch_angle", "vertical_launch_angle_deg"),
        ("total_spin", "spin_rpm"),
    ):
        value = measured.get(shot_key)
        if value is None:
            continue
        p25, p75 = get_cohort_metric_window(club_category, COHORT_PGA, metric)
        if p25 is None or p75 is None:
            continue
        total += 1
        if p25 <= value <= p75:
            in_window += 1

    if total == 0:
        return None
    if in_window == total:
        return "Great"
    if in_window >= max(1, total - 1):
        return "OK"
    return "Needs Work"


def _window_flag(analysis: dict[str, Any], metric: str, shot_key: str) -> bool | None:
    measured = analysis.get("measured", {})
    club_category = analysis.get("inferred", {}).get("club_category")
    value = measured.get(shot_key)
    if value is None:
        return None
    p25, p75 = get_cohort_metric_window(club_category, COHORT_PGA, metric)
    if p25 is None or p75 is None:
        return None
    return p25 <= value <= p75


def _decorate_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    if not analysis:
        return {}
    derived = analysis.setdefault("derived", {})
    derived["shot_quality"] = _compute_shot_quality(analysis)
    derived["launch_in_window"] = _window_flag(
        analysis, "vertical_launch_angle", "vertical_launch_angle_deg"
    )
    derived["spin_in_window"] = _window_flag(analysis, "total_spin", "spin_rpm")
    derived["start_line_in_window"] = _window_flag(
        analysis, "horizontal_launch_angle", "horizontal_launch_angle_deg"
    )
    return analysis


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
            name=NAME,
            manufacturer="Open Launch",
            model=NAME,
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


class OpenGolfCoachCompatSensor(OpenGolfCoachBaseSensor):
    """Compatibility sensor for existing cards."""

    entity_description: OpenGolfCoachSensorEntityDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        state: dict[str, Any],
        description: OpenGolfCoachSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry, state)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = False

    @callback
    def _handle_coordinator_update(self) -> None:
        self._ensure_analysis()
        analysis = self._state_store.get("analysis")
        if analysis:
            self._set_native_from_analysis(analysis)
            self.async_write_ha_state()

    def _set_native_from_analysis(self, analysis: dict[str, Any]) -> None:
        self._attr_native_value = self.entity_description.value_fn(analysis)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "data_source": "derived",
            "source": "open_golf_coach",
            "is_derived": True,
        }
