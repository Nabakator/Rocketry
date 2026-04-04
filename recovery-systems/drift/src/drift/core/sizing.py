"""Parachute sizing helpers for DRIFT."""

from __future__ import annotations

import math

from .units import STANDARD_GRAVITY_MPS2, circle_area_from_diameter_m, circle_diameter_from_area_m2


def required_canopy_area_m2(
    mass_kg: float,
    density_kg_per_m3: float,
    cd: float,
    descent_velocity_mps: float,
) -> float:
    """Return the equilibrium canopy area required for a target descent speed."""

    return (
        2.0 * STANDARD_GRAVITY_MPS2 * mass_kg
        / (density_kg_per_m3 * cd * descent_velocity_mps * descent_velocity_mps)
    )


def theoretical_diameter_m(
    mass_kg: float,
    density_kg_per_m3: float,
    cd: float,
    target_descent_velocity_mps: float,
) -> float:
    """Return the theoretical round-canopy diameter in metres."""

    return circle_diameter_from_area_m2(
        required_canopy_area_m2(
            mass_kg=mass_kg,
            density_kg_per_m3=density_kg_per_m3,
            cd=cd,
            descent_velocity_mps=target_descent_velocity_mps,
        )
    )


def recommended_diameter_m(
    theoretical_diameter_m_value: float,
    safety_margin_fraction: float,
) -> float:
    """Apply the frozen DRIFT safety margin rule to canopy area."""

    return theoretical_diameter_m_value * math.sqrt(1.0 + safety_margin_fraction)


def descent_velocity_for_diameter_m(
    mass_kg: float,
    density_kg_per_m3: float,
    cd: float,
    diameter_m: float,
) -> float:
    """Return the equilibrium descent speed for a selected round canopy size."""

    area_m2 = circle_area_from_diameter_m(diameter_m)
    return math.sqrt(
        2.0 * STANDARD_GRAVITY_MPS2 * mass_kg / (density_kg_per_m3 * cd * area_m2)
    )
