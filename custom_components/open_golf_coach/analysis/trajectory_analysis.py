"""Trajectory summary metrics."""
from __future__ import annotations

import math
from typing import Any

from .trajectory import Trajectory
from .vector import Vec3


def _find_landing(points: Trajectory) -> tuple[Vec3, Vec3, float]:
    last_point = points[-1]
    return last_point.position_m, last_point.velocity_mps, last_point.time_s


def analyze_trajectory(points: Trajectory) -> dict[str, Any]:
    """Analyze a trajectory and return deterministic summary values."""
    if not points:
        return {
            "carry_distance_m": None,
            "total_distance_m": None,
            "offline_distance_m": None,
            "apex_height_m": None,
            "hang_time_s": None,
            "descent_angle_deg": None,
        }

    apex_height = max(point.position_m.z for point in points)

    landing_pos, landing_vel, hang_time = _find_landing(points)
    carry_distance = max(landing_pos.x, 0.0)
    offline_distance = landing_pos.y

    horiz_speed = math.hypot(landing_vel.x, landing_vel.y)
    descent_angle = math.degrees(math.atan2(-landing_vel.z, max(horiz_speed, 0.01)))

    roll_factor = max(0.2, 1.0 - abs(descent_angle) / 60.0)
    roll_distance = max(0.0, carry_distance * 0.08 * roll_factor)
    total_distance = carry_distance + roll_distance

    return {
        "carry_distance_m": round(carry_distance, 2),
        "total_distance_m": round(total_distance, 2),
        "offline_distance_m": round(offline_distance, 2),
        "apex_height_m": round(apex_height, 2),
        "hang_time_s": round(hang_time, 2),
        "descent_angle_deg": round(descent_angle, 2),
    }
