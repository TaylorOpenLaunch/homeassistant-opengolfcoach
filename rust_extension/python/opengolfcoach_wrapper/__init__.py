"""
OpenGolfCoach Python Wrapper

This module provides a high-level Python interface to the OpenGolfCoach Rust core.
It handles JSON serialization/deserialization and provides convenient functions for
the Home Assistant integration.
"""

import json
from typing import Dict, Any, Optional

try:
    import opengolfcoach_rust
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    import warnings
    warnings.warn(
        "opengolfcoach_rust extension not available. "
        "Install with: pip install opengolfcoach-rust",
        ImportWarning
    )


class OpenGolfCoachError(Exception):
    """Base exception for OpenGolfCoach analysis errors."""
    pass


def analyze_shot(
    shot_data: Dict[str, Any],
    handedness: str = "RH"
) -> Dict[str, Any]:
    """
    Analyze a golf shot using the Rust core engine.

    This is the main entry point for shot analysis. It accepts measured shot data
    from the NOVA sensor and returns comprehensive derived metrics including
    trajectory, classification, benchmarks, and coaching recommendations.

    Args:
        shot_data: Dictionary containing measured shot data with keys:
            - ball_speed_meters_per_second (required): Ball speed in m/s
            - vertical_launch_angle_degrees (required): Vertical launch angle
            - horizontal_launch_angle_degrees: Horizontal launch angle (0 = straight)
            - total_spin_rpm: Total spin in RPM
            - spin_axis_degrees: Spin axis (0 = pure backspin)
            - Or use backspin_rpm and sidespin_rpm instead
        handedness: "RH" for right-handed or "LH" for left-handed

    Returns:
        Dictionary with derived values including:
            - carry_distance_meters: Estimated carry distance
            - total_distance_meters: Carry plus roll
            - offline_distance_meters: Lateral deviation (negative = left)
            - shot_name: Classification (e.g., "Draw", "Fade", "Straight")
            - shot_rank: Quality rank (S+, S, A, B, C, D)
            - shot_color_rgb: Color code for UI display
            - backspin_rpm / sidespin_rpm: Spin components
            - club_speed_meters_per_second: Estimated club speed
            - smash_factor: Ball speed / club speed ratio
            - And many more (see API.md for complete schema)

    Raises:
        OpenGolfCoachError: If analysis fails due to invalid input or calculation error
        ImportError: If Rust extension is not installed

    Example:
        >>> shot = {
        ...     "ball_speed_meters_per_second": 70.0,
        ...     "vertical_launch_angle_degrees": 12.5,
        ...     "horizontal_launch_angle_degrees": -2.5,
        ...     "total_spin_rpm": 2500.0,
        ...     "spin_axis_degrees": 10.0
        ... }
        >>> result = analyze_shot(shot, handedness="RH")
        >>> print(f"Carry: {result['carry_distance_meters']:.1f}m")
        >>> print(f"Shot shape: {result['shot_name']}")
    """
    if not RUST_AVAILABLE:
        raise ImportError(
            "opengolfcoach_rust extension not installed. "
            "Install with: pip install opengolfcoach-rust"
        )

    # Apply handedness normalization
    normalized_shot = _normalize_handedness(shot_data, handedness)

    # Convert to JSON
    input_json = json.dumps(normalized_shot)

    # Call Rust core
    try:
        result_json = opengolfcoach_rust.calculate_derived_values(input_json)
        result = json.loads(result_json)
    except Exception as e:
        raise OpenGolfCoachError(f"Shot analysis failed: {e}") from e

    # Add metadata
    result["metadata"] = {
        "analyzed_with": "opengolfcoach_rust",
        "handedness": handedness,
        "trajectory_is_estimated": True
    }

    return result


def _normalize_handedness(shot_data: Dict[str, Any], handedness: str) -> Dict[str, Any]:
    """
    Normalize shot data for handedness.

    The Rust core analyzes shots from a right-handed perspective. For left-handed
    golfers, we need to flip the horizontal launch angle and spin axis.

    Args:
        shot_data: Raw shot data
        handedness: "RH" or "LH"

    Returns:
        Normalized shot data
    """
    if handedness.upper() == "LH":
        # Copy the shot data
        normalized = shot_data.copy()

        # Flip horizontal launch angle
        if "horizontal_launch_angle_degrees" in normalized:
            normalized["horizontal_launch_angle_degrees"] *= -1

        # Flip spin axis
        if "spin_axis_degrees" in normalized:
            normalized["spin_axis_degrees"] *= -1

        # Flip sidespin
        if "sidespin_rpm" in normalized:
            normalized["sidespin_rpm"] *= -1

        return normalized

    return shot_data


def get_version() -> str:
    """Get the version of the opengolfcoach_rust extension."""
    if not RUST_AVAILABLE:
        return "not-installed"

    # The Rust module doesn't expose a version function yet
    # Return a placeholder for now
    return "0.2.0"


def is_rust_available() -> bool:
    """Check if the Rust extension is available."""
    return RUST_AVAILABLE


__all__ = [
    "analyze_shot",
    "get_version",
    "is_rust_available",
    "OpenGolfCoachError",
    "RUST_AVAILABLE",
]
