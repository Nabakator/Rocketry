"""Core engineering modules for DRIFT."""

from .atmosphere import isa_density_kg_per_m3, resolve_density_kg_per_m3
from .drift import drift_distance_m
from .performance import descent_distance_m, phase_duration_s
from .sizing import (
    descent_velocity_for_diameter_m,
    recommended_diameter_m,
    required_canopy_area_m2,
    theoretical_diameter_m,
)
from .units import PI, STANDARD_GRAVITY_MPS2, circle_area_from_diameter_m, circle_diameter_from_area_m2
from .warnings import (
    DROGUE_DESCENT_VELOCITY_THRESHOLD_MPS,
    HIGH_DRIFT_THRESHOLD_M,
    MAIN_DESCENT_VELOCITY_THRESHOLD_MPS,
    generate_configuration_warnings,
)

__all__ = [
    "DROGUE_DESCENT_VELOCITY_THRESHOLD_MPS",
    "HIGH_DRIFT_THRESHOLD_M",
    "MAIN_DESCENT_VELOCITY_THRESHOLD_MPS",
    "PI",
    "STANDARD_GRAVITY_MPS2",
    "circle_area_from_diameter_m",
    "circle_diameter_from_area_m2",
    "descent_distance_m",
    "descent_velocity_for_diameter_m",
    "drift_distance_m",
    "generate_configuration_warnings",
    "isa_density_kg_per_m3",
    "phase_duration_s",
    "recommended_diameter_m",
    "required_canopy_area_m2",
    "resolve_density_kg_per_m3",
    "theoretical_diameter_m",
]
