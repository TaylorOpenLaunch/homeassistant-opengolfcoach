"""Minimal self-check for Open Golf Coach analysis."""
from __future__ import annotations

import json
from pathlib import Path

from .analysis import analyze_shot
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


if __name__ == "__main__":
    run()
