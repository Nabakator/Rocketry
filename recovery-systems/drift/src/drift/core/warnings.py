"""Deterministic engineering warning rules for DRIFT."""

from __future__ import annotations

from typing import Sequence

from drift.models import CatalogueItem, Configuration, Warning

MAIN_DESCENT_VELOCITY_THRESHOLD_MPS = 8.0
DROGUE_DESCENT_VELOCITY_THRESHOLD_MPS = 25.0
HIGH_DRIFT_THRESHOLD_M = 1000.0


def generate_configuration_warnings(
    configuration: Configuration,
    catalogue_items: Sequence[CatalogueItem],
) -> list[Warning]:
    """Return deterministic engineering warnings for an analysed configuration."""

    if configuration.analysis_results is None:
        return []

    warnings: list[Warning] = []

    if configuration.atmosphere_settings.mode == "manual_density":
        warnings.append(
            Warning(
                code="MANUAL_DENSITY_OVERRIDE_ACTIVE",
                severity="info",
                title="Manual density override active",
                message="A manual air-density override is active for this configuration.",
                source_field="atmosphere_settings.manual_density_kg_per_m3",
                triggered_rule="atmosphere_settings.mode == manual_density",
            )
        )

    for index, parachute in enumerate(configuration.parachutes):
        warnings.extend(
            _parachute_override_warnings(
                parachute=parachute,
                parachute_index=index,
            )
        )
        warnings.extend(
            _catalogue_range_warnings(
                parachute=parachute,
                parachute_index=index,
                catalogue_items=catalogue_items,
            )
        )
        warnings.extend(
            _descent_velocity_warnings(
                parachute=parachute,
                parachute_index=index,
            )
        )

    total_drift_m = configuration.analysis_results.total_estimated_drift_m
    if total_drift_m is not None and total_drift_m > HIGH_DRIFT_THRESHOLD_M:
        warnings.append(
            Warning(
                code="DRIFT_ESTIMATE_HIGH",
                severity="warning",
                title="Estimated drift high",
                message=(
                    "The total estimated drift exceeds the DRIFT MVP high-drift "
                    "threshold of 1000.0 m."
                ),
                source_field="analysis_results.total_estimated_drift_m",
                triggered_rule="analysis_results.total_estimated_drift_m > 1000.0",
            )
        )

    return warnings


def _parachute_override_warnings(
    *,
    parachute,
    parachute_index: int,
) -> list[Warning]:
    if parachute.cd_source != "manual_override":
        return []

    return [
        Warning(
            code="MANUAL_CD_OVERRIDE_ACTIVE",
            severity="info",
            title="Manual Cd override active",
            message=(
                f"The drag coefficient for parachute '{parachute.parachute_id}' "
                "has been manually overridden."
            ),
            source_field=f"parachutes[{parachute_index}].cd",
            triggered_rule=f"parachutes[{parachute_index}].cd_source == manual_override",
        )
    ]


def _catalogue_range_warnings(
    *,
    parachute,
    parachute_index: int,
    catalogue_items: Sequence[CatalogueItem],
) -> list[Warning]:
    recommended_diameter_m = parachute.recommended_diameter_m
    selected_nominal_diameter_m = parachute.selected_nominal_diameter_m
    if recommended_diameter_m is None or selected_nominal_diameter_m is None:
        return []

    family_items = sorted(
        (item for item in catalogue_items if item.family == parachute.family),
        key=lambda item: item.nominal_diameter_m,
    )
    if not family_items:
        return []

    minimum_diameter_m = family_items[0].nominal_diameter_m
    maximum_diameter_m = family_items[-1].nominal_diameter_m

    if (
        recommended_diameter_m < minimum_diameter_m
        and selected_nominal_diameter_m == minimum_diameter_m
    ):
        return [
            Warning(
                code="CATALOGUE_OUT_OF_RANGE",
                severity="warning",
                title="Catalogue size out of range",
                message=(
                    f"Recommended diameter for parachute '{parachute.parachute_id}' "
                    "is below the available catalogue range; the smallest available "
                    "item was selected."
                ),
                source_field=f"parachutes[{parachute_index}].recommended_diameter_m",
                triggered_rule=(
                    f"parachutes[{parachute_index}].recommended_diameter_m < "
                    f"min_catalogue_diameter_m[{parachute.family}]"
                ),
            )
        ]

    if (
        recommended_diameter_m > maximum_diameter_m
        and selected_nominal_diameter_m == maximum_diameter_m
    ):
        return [
            Warning(
                code="CATALOGUE_OUT_OF_RANGE",
                severity="warning",
                title="Catalogue size out of range",
                message=(
                    f"Recommended diameter for parachute '{parachute.parachute_id}' "
                    "is above the available catalogue range; the largest available "
                    "item was selected."
                ),
                source_field=f"parachutes[{parachute_index}].recommended_diameter_m",
                triggered_rule=(
                    f"parachutes[{parachute_index}].recommended_diameter_m > "
                    f"max_catalogue_diameter_m[{parachute.family}]"
                ),
            )
        ]

    return []


def _descent_velocity_warnings(
    *,
    parachute,
    parachute_index: int,
) -> list[Warning]:
    resulting_descent_velocity_mps = parachute.resulting_descent_velocity_mps
    if resulting_descent_velocity_mps is None:
        return []

    if parachute.role == "main" and resulting_descent_velocity_mps > MAIN_DESCENT_VELOCITY_THRESHOLD_MPS:
        return [
            Warning(
                code="MAIN_DESCENT_VELOCITY_HIGH",
                severity="warning",
                title="Main descent velocity high",
                message=(
                    f"Main parachute '{parachute.parachute_id}' exceeds the DRIFT MVP "
                    "high main-descent threshold of 8.0 m/s."
                ),
                source_field=f"parachutes[{parachute_index}].resulting_descent_velocity_mps",
                triggered_rule=(
                    f"parachutes[{parachute_index}].resulting_descent_velocity_mps > 8.0"
                ),
            )
        ]

    if parachute.role == "drogue" and resulting_descent_velocity_mps > DROGUE_DESCENT_VELOCITY_THRESHOLD_MPS:
        return [
            Warning(
                code="DROGUE_DESCENT_VELOCITY_HIGH",
                severity="warning",
                title="Drogue descent velocity high",
                message=(
                    f"Drogue parachute '{parachute.parachute_id}' exceeds the DRIFT MVP "
                    "high drogue-descent threshold of 25.0 m/s."
                ),
                source_field=f"parachutes[{parachute_index}].resulting_descent_velocity_mps",
                triggered_rule=(
                    f"parachutes[{parachute_index}].resulting_descent_velocity_mps > 25.0"
                ),
            )
        ]

    return []
