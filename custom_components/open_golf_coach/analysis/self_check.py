"""Minimal self-check for Open Golf Coach analysis."""
from __future__ import annotations

import json
from pathlib import Path

from .analysis import analyze_shot
from .shot_classifier import classify_shot, normalize_for_handedness
from .benchmarks import load_benchmarks
from .coaching import _load_tips


def run() -> None:
    """Run a quick analysis to ensure loaders and analysis work."""
    _ = load_benchmarks()
    _ = _load_tips()

    sample_shot = {
        "ball_speed_meters_per_second": 60.5,
        "vertical_launch_angle_degrees": 12.3,
        "horizontal_launch_angle_degrees": 1.2,
        "total_spin_rpm": 2600,
        "spin_axis_degrees": 3.5,
        "timestamp_ns": 1764477382748215552,
    }

    output = analyze_shot(sample_shot, handedness="RH")
    print(json.dumps(output, indent=2))
    _check_sign_conventions()


def _check_sign_conventions() -> None:
    cases = [
        (2.0, 10.0, "RH", {"PushFade", "PushSlice"}),
        (-2.0, -10.0, "RH", {"PullDraw", "PullHook"}),
        (2.0, 10.0, "LH", {"PullDraw", "PullHook"}),
        (-2.0, -10.0, "LH", {"PushFade", "PushSlice"}),
    ]
    for hla, axis, handedness, expected in cases:
        norm_hla, norm_axis = normalize_for_handedness(hla, axis, handedness)
        result = classify_shot(norm_hla or 0.0, norm_axis or 0.0).shape
        if result not in expected:
            raise RuntimeError(
                f"Sign convention check failed for {handedness} {hla}/{axis}: {result}"
            )


if __name__ == "__main__":
    run()
