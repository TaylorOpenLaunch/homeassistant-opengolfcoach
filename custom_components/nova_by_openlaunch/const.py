"""Constants for the NOVA by Open Launch integration."""
from __future__ import annotations

from dataclasses import dataclass
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfSpeed,
    UnitOfTime,
    DEGREE,
    REVOLUTIONS_PER_MINUTE,
)

DOMAIN = "nova_by_openlaunch"

DEFAULT_PORT = 2920
RECONNECT_INTERVAL = 10  # seconds

# SSDP Discovery
SSDP_ST = "urn:openlaunch:service:websocket:1"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_NAME = "name"

# Device info from SSDP
CONF_MANUFACTURER = "manufacturer"
CONF_MODEL = "model"
CONF_SERIAL = "serial"


@dataclass(frozen=True)
class NovaByOpenLaunchSensorEntityDescription(SensorEntityDescription):
    """Describes a NOVA by Open Launch sensor entity."""

    json_key: str | None = None
    message_type: str | None = None  # "shot" or "status"
    precision: int | None = None  # Number of decimal places (None = no rounding)
    value_offset: int = 0  # Add this to the raw value (e.g., +1 for 0-indexed counts)


# Shot Data Sensors (from "type": "shot" messages)
SHOT_SENSORS: tuple[NovaByOpenLaunchSensorEntityDescription, ...] = (
    NovaByOpenLaunchSensorEntityDescription(
        key="session_shot_count",
        name="Session Shot Count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        json_key="shot_number",
        message_type="shot",
        value_offset=1,  # shot_number is 0-indexed, display as 1-indexed
    ),
    NovaByOpenLaunchSensorEntityDescription(
        key="last_shot_time",
        name="Last Shot",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
        json_key="_last_shot_timestamp",  # Special: set by coordinator
        message_type="shot",
    ),
    NovaByOpenLaunchSensorEntityDescription(
        key="ball_speed",
        name="Ball Speed",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        json_key="ball_speed_meters_per_second",
        message_type="shot",
        precision=1,
    ),
    NovaByOpenLaunchSensorEntityDescription(
        key="vertical_launch_angle",
        name="Vertical Launch Angle",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:angle-acute",
        json_key="vertical_launch_angle_degrees",
        message_type="shot",
        precision=1,
    ),
    NovaByOpenLaunchSensorEntityDescription(
        key="horizontal_launch_angle",
        name="Horizontal Launch Angle",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:angle-acute",
        json_key="horizontal_launch_angle_degrees",
        message_type="shot",
        precision=1,
    ),
    NovaByOpenLaunchSensorEntityDescription(
        key="total_spin",
        name="Total Spin",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:rotate-right",
        json_key="total_spin_rpm",
        message_type="shot",
        precision=0,
    ),
    NovaByOpenLaunchSensorEntityDescription(
        key="spin_axis",
        name="Spin Axis",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:axis-arrow",
        json_key="spin_axis_degrees",
        message_type="shot",
        precision=0,
    ),
)

# Status Sensors (from "type": "status" messages)
STATUS_SENSORS: tuple[NovaByOpenLaunchSensorEntityDescription, ...] = (
    NovaByOpenLaunchSensorEntityDescription(
        key="uptime",
        name="Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        icon="mdi:timer-outline",
        json_key="uptime_seconds",
        message_type="status",
        precision=0,
    ),
)

ALL_SENSORS = SHOT_SENSORS + STATUS_SENSORS
