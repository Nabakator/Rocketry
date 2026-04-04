"""Minimal SI-oriented unit helpers for DRIFT."""

from __future__ import annotations

import math

STANDARD_GRAVITY_MPS2 = 9.80665
PI = math.pi


def circle_area_from_diameter_m(diameter_m: float) -> float:
    """Return the circular canopy area for a given diameter in metres."""

    return PI * diameter_m * diameter_m / 4.0


def circle_diameter_from_area_m2(area_m2: float) -> float:
    """Return the circular canopy diameter for a given area in square metres."""

    return math.sqrt((4.0 * area_m2) / PI)
