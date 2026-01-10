"""
Adapter module for OpenGolfCoach Rust core integration.

This module bridges the Rust core engine with the Home Assistant integration,
transforming between the Rust JSON API and the HA-expected data structures.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

_LOGGER = logging.getLogger(__name__)

try:
    import opengolfcoach_rust
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    _LOGGER.warning(
        "opengolfcoach_rust extension not available. "
        "Install with: pip install opengolfcoach-rust or maturin develop"
    )

from .analysis.benchmarks import compare_shot_to_cohorts, infer_club_category
from .analysis.coaching import get_coaching_for_shape
from .analysis.utils import utc_now_iso

ANALYSIS_VERSION = "0.2.0-rust"


def _timestamp_from_shot(measured_shot: dict[str, Any]) -> str:
    """Extract timestamp from shot data."""
    ts = measured_shot.get("_last_shot_timestamp")
    if isinstance(ts, datetime):
        return ts.astimezone(timezone.utc).isoformat()
    ts_ns = measured_shot.get("timestamp_ns")
    if isinstance(ts_ns, (int, float)):
        return datetime.fromtimestamp(ts_ns / 1e9, tz=timezone.utc).isoformat()
    return utc_now_iso()


def _normalize_handedness(
    horizontal_launch_angle: float | None,
    spin_axis: float | None,
    handedness: str,
) -> tuple[float | None, float | None]:
    """
    Normalize angles for handedness.

    The Rust core analyzes from RH perspective. For LH, flip the angles.
    """
    if handedness.upper() != "LH":
        return horizontal_launch_angle, spin_axis

    norm_hla = -horizontal_launch_angle if horizontal_launch_angle is not None else None
    norm_spin = -spin_axis if spin_axis is not None else None
    return norm_hla, norm_spin


def _prepare_rust_input(measured_shot: dict[str, Any], handedness: str) -> dict[str, Any]:
    """
    Prepare input dict for Rust core from NOVA shot data.

    Translates from NOVA field names to Rust API field names and applies
    handedness normalization.
    """
    # Extract values from NOVA shot
    ball_speed = measured_shot.get("ball_speed_meters_per_second")
    vla = measured_shot.get("vertical_launch_angle_degrees")
    hla = measured_shot.get("horizontal_launch_angle_degrees")
    spin_rpm = measured_shot.get("total_spin_rpm")
    spin_axis = measured_shot.get("spin_axis_degrees")

    # Normalize for handedness
    hla_norm, spin_axis_norm = _normalize_handedness(hla, spin_axis, handedness)

    # Build Rust input (only include non-None values)
    rust_input = {}

    if ball_speed is not None:
        rust_input["ball_speed_meters_per_second"] = float(ball_speed)
    if vla is not None:
        rust_input["vertical_launch_angle_degrees"] = float(vla)
    if hla_norm is not None:
        rust_input["horizontal_launch_angle_degrees"] = float(hla_norm)
    if spin_rpm is not None:
        rust_input["total_spin_rpm"] = float(spin_rpm)
    if spin_axis_norm is not None:
        rust_input["spin_axis_degrees"] = float(spin_axis_norm)

    return rust_input


def _extract_shot_shape_from_rust(rust_output: dict[str, Any]) -> str | None:
    """
    Extract shot shape classification from Rust output.

    Maps Rust shot_name to HA-expected shape names.
    """
    shot_name = rust_output.get("shot_name")
    if not shot_name:
        return None

    # The Rust core returns shapes like "Draw", "Fade", "Slice", etc.
    # Map to our expected format if needed
    shape_map = {
        "Straight": "Straight",
        "Draw": "Draw",
        "Fade": "Fade",
        "Hook": "Hook",
        "Slice": "Slice",
        "PushDraw": "PushDraw",
        "PushFade": "PushFade",
        "PullDraw": "PullDraw",
        "PullFade": "PullFade",
        "Push": "Push",
        "Pull": "Pull",
    }

    return shape_map.get(shot_name, shot_name)


def _extract_severity_from_rust(rust_output: dict[str, Any]) -> str | None:
    """
    Extract severity from Rust shot_rank.

    Maps S+/S/A/B/C/D ranks to severity levels.
    """
    rank = rust_output.get("shot_rank")
    if not rank:
        return None

    # Map ranks to severity
    severity_map = {
        "S+": "mild",
        "S": "mild",
        "A": "moderate",
        "B": "moderate",
        "C": "severe",
        "D": "severe",
    }

    return severity_map.get(rank, "moderate")


def _build_trajectory_summary(rust_output: dict[str, Any]) -> dict[str, Any] | None:
    """Build trajectory summary from Rust output."""
    carry = rust_output.get("carry_distance_meters")
    total = rust_output.get("total_distance_meters")
    offline = rust_output.get("offline_distance_meters")
    peak_height = rust_output.get("peak_height_meters")

    if carry is None:
        return None

    trajectory = {
        "carry_distance_m": carry,
        "total_distance_m": total if total is not None else carry,
        "offline_distance_m": offline if offline is not None else 0.0,
    }

    if peak_height is not None:
        trajectory["apex_height_m"] = peak_height

    # Add imperial units if available
    us_units = rust_output.get("us_customary_units", {})
    if us_units:
        if "carry_distance_yards" in us_units:
            trajectory["carry_distance_yds"] = us_units["carry_distance_yards"]
        if "total_distance_yards" in us_units:
            trajectory["total_distance_yds"] = us_units["total_distance_yards"]
        if "offline_distance_yards" in us_units:
            trajectory["offline_distance_yds"] = us_units["offline_distance_yards"]
        if "peak_height_yards" in us_units:
            trajectory["apex_height_yds"] = us_units["peak_height_yards"]

    return trajectory


def analyze_shot(measured_shot: dict[str, Any], handedness: str = "RH") -> dict[str, Any]:
    """
    Analyze a golf shot using the Rust core engine.

    This is the main entry point that replaces the Python-only analysis.
    It calls the Rust core for performance-critical computations and combines
    the results with HA-specific features like benchmarks and coaching.

    Args:
        measured_shot: Raw shot data from NOVA coordinator
        handedness: "RH" or "LH"

    Returns:
        Analysis dict with measured, derived, inferred, benchmarks, coaching, metadata
    """
    handedness = handedness.upper()

    # Build measured dict (HA internal format)
    measured = {
        "ball_speed_mps": measured_shot.get("ball_speed_meters_per_second"),
        "vertical_launch_angle_deg": measured_shot.get("vertical_launch_angle_degrees"),
        "horizontal_launch_angle_deg": measured_shot.get("horizontal_launch_angle_degrees"),
        "spin_rpm": measured_shot.get("total_spin_rpm"),
        "spin_axis_deg": measured_shot.get("spin_axis_degrees"),
    }

    # Call Rust core if available
    rust_output = {}
    rust_error = None

    if RUST_AVAILABLE:
        try:
            rust_input = _prepare_rust_input(measured_shot, handedness)
            rust_input_json = json.dumps(rust_input)
            rust_output_json = opengolfcoach_rust.calculate_derived_values(rust_input_json)
            rust_output = json.loads(rust_output_json)
        except Exception as e:
            _LOGGER.error("Rust analysis failed: %s", e)
            rust_error = str(e)
    else:
        rust_error = "Rust extension not installed"

    # Extract classification from Rust
    shot_shape = _extract_shot_shape_from_rust(rust_output) if rust_output else None
    severity = _extract_severity_from_rust(rust_output) if rust_output else None

    # Infer club category (Python logic, uses benchmarks data)
    club_category = infer_club_category(measured_shot)

    # Build trajectory summary from Rust output
    trajectory_summary = _build_trajectory_summary(rust_output) if rust_output else None
    trajectory_notes = []
    if not trajectory_summary:
        trajectory_notes.append("missing_inputs" if not rust_error else "rust_error")

    # Get coaching (Python logic, uses coaching data)
    coaching = {}
    if shot_shape:
        coaching = get_coaching_for_shape(shot_shape, handedness)
    else:
        coaching = {
            "diagnostics": [],
            "coaching_cues": [],
            "quick_checks": [],
            "practice_drills": []
        }

    coaching_cues_short = coaching.get("coaching_cues", [])[:3]

    # Build inferred dict
    inferred = {
        "handedness": handedness,
        "club_category": club_category,
        "shot_shape": shot_shape,
        "severity": severity if severity != "straight" else "mild",
    }

    # Add club data from Rust output
    if rust_output:
        if "club_speed_meters_per_second" in rust_output:
            inferred["club_speed_mps"] = rust_output["club_speed_meters_per_second"]
        if "smash_factor" in rust_output:
            inferred["smash_factor"] = rust_output["smash_factor"]
        if "club_path_degrees" in rust_output:
            inferred["club_path_deg"] = rust_output["club_path_degrees"]
        if "club_face_to_target_degrees" in rust_output:
            inferred["face_to_target_deg"] = rust_output["club_face_to_target_degrees"]
        if "club_face_to_path_degrees" in rust_output:
            inferred["face_to_path_deg"] = rust_output["club_face_to_path_degrees"]

    # Get benchmarks (Python logic)
    benchmarks = compare_shot_to_cohorts(measured_shot, club_category)

    # Build derived dict
    derived = {
        "estimated_trajectory": trajectory_summary,
        "trajectory_is_estimated": True,
        "trajectory_model_note": (
            "Trajectory values computed by OpenGolfCoach Rust core using "
            "physics-based simulation with drag and lift models."
        ),
        "trajectory_notes": trajectory_notes,
    }

    if rust_error:
        derived["rust_error"] = rust_error

    # Build final analysis
    return {
        "measured": measured,
        "derived": derived,
        "inferred": inferred,
        "benchmarks": benchmarks,
        "coaching": {
            **coaching,
            "coaching_cues_short": coaching_cues_short,
        },
        "metadata": {
            "timestamp_utc": _timestamp_from_shot(measured_shot),
            "version": ANALYSIS_VERSION,
            "rust_enabled": RUST_AVAILABLE,
        },
    }
