"""Shot shape classification."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShotClassification:
    """Classified shot result."""

    shape: str
    severity: str


DEFAULT_START_LINE_CENTER_THRESHOLD_DEG = 1.0
DEFAULT_CURVATURE_MILD_THRESHOLD_DEG = 3.0
DEFAULT_CURVATURE_SEVERE_THRESHOLD_DEG = 8.0


def normalize_for_handedness(
    horizontal_launch_angle_deg: float | None,
    spin_axis_deg: float | None,
    handedness: str,
) -> tuple[float | None, float | None]:
    """Normalize values to RH sign convention for classification."""
    handedness = handedness.upper()
    if handedness != "LH":
        return horizontal_launch_angle_deg, spin_axis_deg
    hla = -horizontal_launch_angle_deg if horizontal_launch_angle_deg is not None else None
    axis = -spin_axis_deg if spin_axis_deg is not None else None
    return hla, axis


def classify_shot(
    horizontal_launch_angle_deg: float,
    spin_axis_deg: float,
    start_line_center_threshold_deg: float = DEFAULT_START_LINE_CENTER_THRESHOLD_DEG,
    curvature_mild_threshold_deg: float = DEFAULT_CURVATURE_MILD_THRESHOLD_DEG,
    curvature_severe_threshold_deg: float = DEFAULT_CURVATURE_SEVERE_THRESHOLD_DEG,
) -> ShotClassification:
    """Classify shot shape using launch direction and spin axis."""
    start_line = horizontal_launch_angle_deg
    curvature = spin_axis_deg

    abs_start = abs(start_line)
    abs_curve = abs(curvature)

    if abs_curve <= curvature_mild_threshold_deg:
        severity = "mild"
    elif abs_curve <= curvature_severe_threshold_deg:
        severity = "moderate"
    else:
        severity = "severe"

    if abs_start <= start_line_center_threshold_deg:
        if abs_curve <= curvature_mild_threshold_deg:
            return ShotClassification("Straight", "straight")
        if curvature > 0:
            return ShotClassification("Fade" if abs_curve <= curvature_severe_threshold_deg else "Slice", severity)
        return ShotClassification("Draw" if abs_curve <= curvature_severe_threshold_deg else "Hook", severity)

    if start_line > 0:
        if abs_curve <= curvature_mild_threshold_deg:
            return ShotClassification("Push", "mild")
        if curvature > 0:
            return ShotClassification("PushFade" if abs_curve <= curvature_severe_threshold_deg else "PushSlice", severity)
        return ShotClassification("PushDraw", severity)

    if abs_curve <= curvature_mild_threshold_deg:
        return ShotClassification("Pull", "mild")
    if curvature < 0:
        return ShotClassification("PullDraw" if abs_curve <= curvature_severe_threshold_deg else "PullHook", severity)
    return ShotClassification("PullFade" if abs_curve <= curvature_severe_threshold_deg else "PullSlice", severity)
