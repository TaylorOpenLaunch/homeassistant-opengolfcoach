"""Unit conversion helpers."""
from __future__ import annotations

import math

MPS_TO_MPH = 2.2369362920544
MPH_TO_MPS = 1.0 / MPS_TO_MPH


def mps_to_mph(speed_mps: float) -> float:
    """Convert meters per second to miles per hour."""
    return speed_mps * MPS_TO_MPH


def mph_to_mps(speed_mph: float) -> float:
    """Convert miles per hour to meters per second."""
    return speed_mph * MPH_TO_MPS


def deg_to_rad(degrees: float) -> float:
    """Convert degrees to radians."""
    return math.radians(degrees)


def rad_to_deg(radians: float) -> float:
    """Convert radians to degrees."""
    return math.degrees(radians)
