"""ISA-based atmosphere and density handling for DRIFT."""

from __future__ import annotations

import math

from .units import STANDARD_GRAVITY_MPS2

ISA_SEA_LEVEL_TEMPERATURE_K = 288.15
ISA_SEA_LEVEL_PRESSURE_PA = 101325.0
ISA_TROPOSPHERE_LAPSE_RATE_K_PER_M = 0.0065
ISA_GAS_CONSTANT_DRY_AIR = 287.05287
ISA_TROPOPAUSE_ALTITUDE_M = 11000.0


def isa_density_kg_per_m3(altitude_m: float) -> float:
    """Return ISA air density for a geometric altitude in metres.

    Uses the ISA troposphere model up to 11 km and an isothermal continuation
    above 11 km for the MVP range of interest.
    """

    if altitude_m < 0.0:
        raise ValueError("altitude_m must be greater than or equal to 0.")

    if altitude_m <= ISA_TROPOPAUSE_ALTITUDE_M:
        temperature_k = (
            ISA_SEA_LEVEL_TEMPERATURE_K
            - ISA_TROPOSPHERE_LAPSE_RATE_K_PER_M * altitude_m
        )
        pressure_pa = ISA_SEA_LEVEL_PRESSURE_PA * (
            temperature_k / ISA_SEA_LEVEL_TEMPERATURE_K
        ) ** (
            STANDARD_GRAVITY_MPS2
            / (ISA_GAS_CONSTANT_DRY_AIR * ISA_TROPOSPHERE_LAPSE_RATE_K_PER_M)
        )
        return pressure_pa / (ISA_GAS_CONSTANT_DRY_AIR * temperature_k)

    tropopause_temperature_k = (
        ISA_SEA_LEVEL_TEMPERATURE_K
        - ISA_TROPOSPHERE_LAPSE_RATE_K_PER_M * ISA_TROPOPAUSE_ALTITUDE_M
    )
    tropopause_pressure_pa = ISA_SEA_LEVEL_PRESSURE_PA * (
        tropopause_temperature_k / ISA_SEA_LEVEL_TEMPERATURE_K
    ) ** (
        STANDARD_GRAVITY_MPS2
        / (ISA_GAS_CONSTANT_DRY_AIR * ISA_TROPOSPHERE_LAPSE_RATE_K_PER_M)
    )
    pressure_pa = tropopause_pressure_pa * math.exp(
        -STANDARD_GRAVITY_MPS2
        * (altitude_m - ISA_TROPOPAUSE_ALTITUDE_M)
        / (ISA_GAS_CONSTANT_DRY_AIR * tropopause_temperature_k)
    )
    return pressure_pa / (ISA_GAS_CONSTANT_DRY_AIR * tropopause_temperature_k)


def resolve_density_kg_per_m3(
    altitude_m: float,
    manual_density_kg_per_m3: float | None = None,
) -> float:
    """Return either the manual density override or ISA density."""

    if manual_density_kg_per_m3 is not None:
        return manual_density_kg_per_m3
    return isa_density_kg_per_m3(altitude_m)
