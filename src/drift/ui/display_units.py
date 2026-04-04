"""UI-only unit conversion and formatting helpers for DRIFT."""

from __future__ import annotations

KG_TO_LB = 2.2046226218487757
M_TO_FT = 3.280839895013123
MPS_TO_FTPS = 3.280839895013123
KG_M3_TO_LB_FT3 = 0.062427960576145


def mass_from_si(value_kg: float, unit_system: str) -> float:
    if unit_system == "imperial":
        return value_kg * KG_TO_LB
    return value_kg


def mass_to_si(value: float, unit_system: str) -> float:
    if unit_system == "imperial":
        return value / KG_TO_LB
    return value


def length_from_si(value_m: float, unit_system: str) -> float:
    if unit_system == "imperial":
        return value_m * M_TO_FT
    return value_m


def length_to_si(value: float, unit_system: str) -> float:
    if unit_system == "imperial":
        return value / M_TO_FT
    return value


def velocity_from_si(value_mps: float, unit_system: str) -> float:
    if unit_system == "imperial":
        return value_mps * MPS_TO_FTPS
    return value_mps


def velocity_to_si(value: float, unit_system: str) -> float:
    if unit_system == "imperial":
        return value / MPS_TO_FTPS
    return value


def density_from_si(value_kg_per_m3: float, unit_system: str) -> float:
    if unit_system == "imperial":
        return value_kg_per_m3 * KG_M3_TO_LB_FT3
    return value_kg_per_m3


def density_to_si(value: float, unit_system: str) -> float:
    if unit_system == "imperial":
        return value / KG_M3_TO_LB_FT3
    return value


def mass_unit_label(unit_system: str) -> str:
    return "lb" if unit_system == "imperial" else "kg"


def length_unit_label(unit_system: str) -> str:
    return "ft" if unit_system == "imperial" else "m"


def velocity_unit_label(unit_system: str) -> str:
    return "ft/s" if unit_system == "imperial" else "m/s"


def density_unit_label(unit_system: str) -> str:
    return "lb/ft^3" if unit_system == "imperial" else "kg/m^3"


def format_length(value_m: float | None, unit_system: str, *, precision: int = 3) -> str:
    if value_m is None:
        return "N/A"
    return f"{length_from_si(value_m, unit_system):.{precision}f} {length_unit_label(unit_system)}"


def format_velocity(value_mps: float | None, unit_system: str, *, precision: int = 3) -> str:
    if value_mps is None:
        return "N/A"
    return f"{velocity_from_si(value_mps, unit_system):.{precision}f} {velocity_unit_label(unit_system)}"


def format_density(value_kg_per_m3: float | None, unit_system: str, *, precision: int = 4) -> str:
    if value_kg_per_m3 is None:
        return "N/A"
    return f"{density_from_si(value_kg_per_m3, unit_system):.{precision}f} {density_unit_label(unit_system)}"


def format_mass(value_kg: float | None, unit_system: str, *, precision: int = 3) -> str:
    if value_kg is None:
        return "N/A"
    return f"{mass_from_si(value_kg, unit_system):.{precision}f} {mass_unit_label(unit_system)}"


def format_time(value_s: float | None, *, precision: int = 2) -> str:
    if value_s is None:
        return "N/A"
    return f"{value_s:.{precision}f} s"
