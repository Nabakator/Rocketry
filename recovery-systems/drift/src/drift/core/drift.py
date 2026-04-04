"""First-order recovery drift helpers for DRIFT."""

from __future__ import annotations


def drift_distance_m(duration_s: float, wind_speed_mps: float) -> float:
    """Return scalar horizontal drift distance for a constant wind speed."""

    return duration_s * wind_speed_mps
