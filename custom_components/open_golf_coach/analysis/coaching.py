"""Coaching cue lookup."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import load_json_resource

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TIPS_PATH = DATA_DIR / "tips.json"

_cached: dict[str, Any] | None = None


def _load_tips() -> dict[str, Any]:
    global _cached
    if _cached is None:
        result = load_json_resource(TIPS_PATH)
        _cached = result.data
    return _cached


def get_coaching_for_shape(shape: str, handedness: str) -> dict[str, list[str]]:
    """Return coaching guidance for a shot shape and handedness."""
    data = _load_tips()
    tips = data.get("tips", [])
    handedness = handedness.upper()

    matched = []
    for tip in tips:
        if tip.get("shape") != shape:
            continue
        tip_handed = (tip.get("handedness") or "both").upper()
        if tip_handed not in ("BOTH", handedness):
            continue
        matched.append(tip)

    if not matched:
        return {
            "diagnostics": [],
            "coaching_cues": [],
            "quick_checks": [],
            "practice_drills": [],
        }

    matched.sort(key=lambda tip: tip.get("priority", 0), reverse=True)
    tip = matched[0]

    return {
        "diagnostics": tip.get("diagnostics", []),
        "coaching_cues": tip.get("coaching_cues", []),
        "quick_checks": tip.get("quick_checks", []),
        "practice_drills": tip.get("practice_drills", []),
    }
