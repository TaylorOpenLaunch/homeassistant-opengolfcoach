"""Estimated clubhead metrics derived from ball flight."""
from __future__ import annotations

from typing import Any


SMASH_FACTORS = {
    "woods": 1.48,
    "mid_irons": 1.35,
    "wedges": 1.25,
}


def estimate_club_data(
    ball_speed_mps: float,
    horizontal_launch_angle_deg: float | None = None,
    spin_axis_deg: float | None = None,
    club_category: str | None = None,
) -> dict[str, Any]:
    """Estimate club metrics using simple deterministic heuristics."""
    assumed_smash = SMASH_FACTORS.get(club_category or "", 1.4)
    club_speed = None
    smash = None

    if ball_speed_mps is not None:
        club_speed = ball_speed_mps / assumed_smash
        smash = ball_speed_mps / club_speed if club_speed else None

    estimates: dict[str, Any] = {
        "estimated_club_speed_mps": round(club_speed, 2) if club_speed else None,
        "smash_factor": round(smash, 2) if smash else None,
    }

    if horizontal_launch_angle_deg is not None and spin_axis_deg is not None:
        face_angle = horizontal_launch_angle_deg * 0.8 + spin_axis_deg * 0.1
        path_angle = horizontal_launch_angle_deg * 0.5 - spin_axis_deg * 0.1
        estimates.update(
            {
                "estimated_face_angle_deg": round(face_angle, 2),
                "estimated_path_angle_deg": round(path_angle, 2),
                "estimated_face_to_path_deg": round(face_angle - path_angle, 2),
            }
        )

    return estimates
