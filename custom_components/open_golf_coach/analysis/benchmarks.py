"""Benchmarks loader and comparison helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .utils import load_json_resource

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
BENCHMARKS_PATH = DATA_DIR / "benchmarks.json"

SHOT_METRIC_MAP = {
    "ball_speed": "ball_speed_meters_per_second",
    "vertical_launch_angle": "vertical_launch_angle_degrees",
    "horizontal_launch_angle": "horizontal_launch_angle_degrees",
    "total_spin": "total_spin_rpm",
    "spin_axis": "spin_axis_degrees",
}


@dataclass(frozen=True)
class BenchmarksData:
    """Parsed benchmark data."""

    raw: dict[str, Any]
    sanitized: bool

    @property
    def benchmarks(self) -> dict[str, Any]:
        return self.raw.get("benchmarks", {})

    @property
    def cohorts(self) -> list[dict[str, Any]]:
        return self.raw.get("meta", {}).get("cohorts", [])


_cached: BenchmarksData | None = None


def load_benchmarks() -> BenchmarksData:
    """Load benchmark JSON from packaged data."""
    global _cached
    if _cached is None:
        result = load_json_resource(BENCHMARKS_PATH)
        _cached = BenchmarksData(raw=result.data, sanitized=result.sanitized)
    return _cached


def get_percentile_band(value: float, percentiles: dict[str, float]) -> str:
    """Return a percentile band string for the given value."""
    p10 = percentiles.get("p10")
    p25 = percentiles.get("p25")
    p50 = percentiles.get("p50")
    p75 = percentiles.get("p75")
    p90 = percentiles.get("p90")

    if any(v is None for v in (p10, p25, p50, p75, p90)):
        return "unknown"
    if value < p10:
        return "below_p10"
    if value < p25:
        return "p10_p25"
    if value < p50:
        return "p25_p50"
    if value < p75:
        return "p50_p75"
    if value < p90:
        return "p75_p90"
    return "above_p90"


def _category_has_reference(category_data: dict[str, Any]) -> bool:
    ball_speed = category_data.get("pga_tour", {}).get("ball_speed", {})
    return "p50" in ball_speed


def infer_club_category(measured_shot: dict[str, Any]) -> str | None:
    """Infer the club category based on PGA Tour medians."""
    data = load_benchmarks().benchmarks
    best_category = None
    best_score = None

    for category, category_data in data.items():
        if not _category_has_reference(category_data):
            continue
        pga = category_data.get("pga_tour", {})
        score = 0.0
        count = 0
        for metric in ("ball_speed", "vertical_launch_angle", "total_spin"):
            shot_key = SHOT_METRIC_MAP[metric]
            value = measured_shot.get(shot_key)
            if value is None:
                continue
            percentiles = pga.get(metric)
            if not percentiles:
                continue
            p50 = percentiles.get("p50")
            p25 = percentiles.get("p25")
            p75 = percentiles.get("p75")
            if p50 is None or p25 is None or p75 is None:
                continue
            iqr = max(p75 - p25, 1e-3)
            score += abs((value - p50) / iqr)
            count += 1
        if count == 0:
            continue
        score = score / count
        if best_score is None or score < best_score:
            best_score = score
            best_category = category

    return best_category


def compare_shot_to_cohorts(
    measured_shot: dict[str, Any],
    club_category: str | None,
) -> dict[str, Any]:
    """Compare a shot against each cohort's percentiles."""
    if not club_category:
        return {}

    data = load_benchmarks().benchmarks
    category_data = data.get(club_category, {})
    if not category_data:
        return {}

    comparisons: dict[str, Any] = {}
    for cohort_id, cohort_data in category_data.items():
        metrics_summary: dict[str, Any] = {}
        for metric, shot_key in SHOT_METRIC_MAP.items():
            value = measured_shot.get(shot_key)
            if value is None:
                continue
            percentiles = cohort_data.get(metric)
            if not percentiles:
                continue
            metrics_summary[metric] = {
                "value": value,
                "band": get_percentile_band(value, percentiles),
                "p25": percentiles.get("p25"),
                "p50": percentiles.get("p50"),
                "p75": percentiles.get("p75"),
            }
        if metrics_summary:
            comparisons[cohort_id] = metrics_summary

    return comparisons


def get_cohort_metric_window(
    club_category: str | None,
    cohort_id: str,
    metric: str,
) -> tuple[float | None, float | None]:
    """Return (p25, p75) window for a cohort metric."""
    if not club_category:
        return None, None
    data = load_benchmarks().benchmarks
    category_data = data.get(club_category, {})
    if not category_data:
        return None, None
    cohort_data = category_data.get(cohort_id, {})
    percentiles = cohort_data.get(metric, {})
    return percentiles.get("p25"), percentiles.get("p75")
