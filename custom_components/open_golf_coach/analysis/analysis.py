"""Shot analysis orchestration."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .benchmarks import compare_shot_to_cohorts, infer_club_category
from .clubhead_data import estimate_club_data
from .coaching import get_coaching_for_shape
from .shot_classifier import classify_shot
from .trajectory import simulate_trajectory
from .trajectory_analysis import analyze_trajectory
from .utils import utc_now_iso

ANALYSIS_VERSION = "0.1.0"

MEASURED_KEYS = {
    "ball_speed_meters_per_second": "ball_speed_mps",
    "vertical_launch_angle_degrees": "vertical_launch_angle_deg",
    "horizontal_launch_angle_degrees": "horizontal_launch_angle_deg",
    "total_spin_rpm": "spin_rpm",
    "spin_axis_degrees": "spin_axis_deg",
}


def _timestamp_from_shot(measured_shot: dict[str, Any]) -> str:
    ts = measured_shot.get("_last_shot_timestamp")
    if isinstance(ts, datetime):
        return ts.astimezone(timezone.utc).isoformat()
    ts_ns = measured_shot.get("timestamp_ns")
    if isinstance(ts_ns, (int, float)):
        return datetime.fromtimestamp(ts_ns / 1e9, tz=timezone.utc).isoformat()
    return utc_now_iso()


def analyze_shot(measured_shot: dict[str, Any], handedness: str = "RH") -> dict[str, Any]:
    """Analyze a shot and return measured + derived output."""
    handedness = handedness.upper()

    measured = {
        key: measured_shot.get(src_key)
        for src_key, key in MEASURED_KEYS.items()
    }

    adjusted_hla = measured.get("horizontal_launch_angle_deg")
    adjusted_spin_axis = measured.get("spin_axis_deg")
    if handedness == "LH":
        if adjusted_hla is not None:
            adjusted_hla = -adjusted_hla
        if adjusted_spin_axis is not None:
            adjusted_spin_axis = -adjusted_spin_axis

    club_category = infer_club_category(measured_shot)

    trajectory_summary = None
    trajectory_notes = []
    if all(
        measured.get(key) is not None
        for key in (
            "ball_speed_mps",
            "vertical_launch_angle_deg",
            "horizontal_launch_angle_deg",
            "spin_rpm",
            "spin_axis_deg",
        )
    ):
        points = simulate_trajectory(
            ball_speed_mps=measured["ball_speed_mps"],
            vertical_launch_angle_deg=measured["vertical_launch_angle_deg"],
            horizontal_launch_angle_deg=adjusted_hla or 0.0,
            spin_rpm=measured["spin_rpm"],
            spin_axis_deg=adjusted_spin_axis or 0.0,
        )
        trajectory_summary = analyze_trajectory(points)
    else:
        trajectory_notes.append("missing_inputs")

    classification = None
    if adjusted_hla is not None and adjusted_spin_axis is not None:
        classification = classify_shot(adjusted_hla, adjusted_spin_axis)

    coaching = (
        get_coaching_for_shape(classification.shape, handedness)
        if classification
        else {"diagnostics": [], "coaching_cues": [], "quick_checks": [], "practice_drills": []}
    )

    coaching_cues_short = coaching.get("coaching_cues", [])[:3]

    severity = classification.severity if classification else None
    if severity == "straight":
        severity = "mild"

    inferred = {
        "handedness": handedness,
        "club_category": club_category,
        "shot_shape": classification.shape if classification else None,
        "severity": severity,
    }

    inferred.update(
        estimate_club_data(
            measured.get("ball_speed_mps"),
            horizontal_launch_angle_deg=adjusted_hla,
            spin_axis_deg=adjusted_spin_axis,
            club_category=club_category,
        )
    )

    benchmarks = compare_shot_to_cohorts(measured_shot, club_category)

    derived = {
        "trajectory": trajectory_summary,
        "trajectory_notes": trajectory_notes,
    }

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
        },
    }
