"""First-order descent performance helpers for DRIFT."""

from __future__ import annotations


def descent_distance_m(start_altitude_m: float, end_altitude_m: float) -> float:
    """Return the scalar descent distance between two altitudes."""

    return max(start_altitude_m - end_altitude_m, 0.0)


def phase_duration_s(
    start_altitude_m: float,
    end_altitude_m: float,
    descent_velocity_mps: float,
) -> float:
    """Return constant-velocity phase duration in seconds."""

    return descent_distance_m(start_altitude_m, end_altitude_m) / descent_velocity_mps
