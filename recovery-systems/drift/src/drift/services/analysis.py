"""UI-independent analysis orchestration for DRIFT."""

from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from drift.core.atmosphere import resolve_density_kg_per_m3
from drift.core.drift import drift_distance_m
from drift.core.performance import phase_duration_s
from drift.core.sizing import (
    descent_velocity_for_diameter_m,
    recommended_diameter_m,
    theoretical_diameter_m,
)
from drift.core.warnings import generate_configuration_warnings
from drift.models import (
    AnalysisResult,
    CatalogueItem,
    Configuration,
    ParachuteSpec,
    PhaseSummary,
    Project,
)
from drift.services.validation import ValidationIssue, validate_configuration, validate_project


class AnalysisError(Exception):
    """Raised when DRIFT analysis is requested for invalid or unsupported data."""

    def __init__(
        self,
        message: str,
        *,
        issues: Sequence[ValidationIssue] | None = None,
    ) -> None:
        super().__init__(message)
        self.issues = tuple(issues or ())


def analyze_project(
    project: Project,
    catalogue_items: Sequence[CatalogueItem],
) -> Project:
    """Analyze every configuration in a project and return a new project instance."""

    validation_result = validate_project(project)
    if not validation_result.is_valid:
        raise AnalysisError(
            "Project validation failed; analysis cannot proceed.",
            issues=validation_result.issues,
        )

    analyzed_configurations = [
        analyze_configuration(configuration, catalogue_items)
        for configuration in project.configurations
    ]
    return replace(project, configurations=analyzed_configurations)


def analyze_configuration(
    configuration: Configuration,
    catalogue_items: Sequence[CatalogueItem],
) -> Configuration:
    """Analyze one validated DRIFT configuration and return updated results."""

    validation_result = validate_configuration(configuration)
    if not validation_result.is_valid:
        raise AnalysisError(
            "Configuration validation failed; analysis cannot proceed.",
            issues=validation_result.issues,
        )

    if configuration.recovery_mode == "single":
        return _analyze_single_configuration(configuration, catalogue_items)
    if configuration.recovery_mode == "dual":
        return _analyze_dual_configuration(configuration, catalogue_items)

    raise AnalysisError(f"Unsupported recovery mode: {configuration.recovery_mode!r}")


def match_catalogue_item(
    family: str,
    recommended_diameter_m_value: float,
    catalogue_items: Sequence[CatalogueItem],
) -> CatalogueItem:
    """Match a catalogue item using the frozen DRIFT MVP policy."""

    family_items = sorted(
        (item for item in catalogue_items if item.family == family),
        key=lambda item: item.nominal_diameter_m,
    )
    if not family_items:
        raise AnalysisError(
            f"No catalogue items are available for parachute family {family!r}."
        )

    if recommended_diameter_m_value <= family_items[0].nominal_diameter_m:
        return family_items[0]

    for item in family_items:
        if item.nominal_diameter_m >= recommended_diameter_m_value:
            return item

    return family_items[-1]


def _analyze_single_configuration(
    configuration: Configuration,
    catalogue_items: Sequence[CatalogueItem],
) -> Configuration:
    single_parachute = _find_parachute(configuration, "single")
    deployment_altitude_m = _require_float(
        configuration.altitude_inputs.deployment_altitude_m,
        "Single configuration deployment_altitude_m is required.",
    )
    analyzed_parachute = _analyze_parachute(
        configuration=configuration,
        parachute=single_parachute,
        deployment_altitude_m=deployment_altitude_m,
        catalogue_items=catalogue_items,
    )

    apogee_altitude_m = configuration.altitude_inputs.apogee_altitude_m
    if apogee_altitude_m is not None:
        start_altitude_m = apogee_altitude_m
        recovery_basis_label = "from_apogee"
    else:
        start_altitude_m = deployment_altitude_m
        recovery_basis_label = "from_deployment_altitude"

    descent_velocity_mps = _require_float(
        analyzed_parachute.resulting_descent_velocity_mps,
        "Single parachute analysis did not produce a resulting descent velocity.",
    )
    total_descent_time_s = phase_duration_s(
        start_altitude_m=start_altitude_m,
        end_altitude_m=0.0,
        descent_velocity_mps=descent_velocity_mps,
    )
    total_estimated_drift_m = _single_phase_drift_m(
        configuration=configuration,
        start_altitude_m=start_altitude_m,
        deployment_altitude_m=deployment_altitude_m,
        descent_velocity_mps=descent_velocity_mps,
        total_descent_time_s=total_descent_time_s,
    )

    analysis_result = AnalysisResult(
        recovery_basis_label=recovery_basis_label,
        phase_summaries=[
            PhaseSummary(
                phase_name="single",
                start_altitude_m=start_altitude_m,
                end_altitude_m=0.0,
                parachute_id=analyzed_parachute.parachute_id,
                nominal_descent_velocity_mps=descent_velocity_mps,
                estimated_duration_s=total_descent_time_s,
                estimated_drift_m=total_estimated_drift_m,
            )
        ],
        total_descent_time_s=total_descent_time_s,
        total_estimated_drift_m=total_estimated_drift_m,
        display_metrics={
            "sizing_available": True,
            "descent_time_available": True,
            "drift_available": True,
        },
    )
    analyzed_configuration = replace(
        configuration,
        parachutes=[analyzed_parachute],
        analysis_results=analysis_result,
        warnings=[],
    )
    return replace(
        analyzed_configuration,
        warnings=generate_configuration_warnings(analyzed_configuration, catalogue_items),
    )


def _analyze_dual_configuration(
    configuration: Configuration,
    catalogue_items: Sequence[CatalogueItem],
) -> Configuration:
    drogue_parachute = _find_parachute(configuration, "drogue")
    main_parachute = _find_parachute(configuration, "main")

    drogue_deployment_altitude_m = _require_float(
        configuration.altitude_inputs.drogue_deployment_altitude_m,
        "Dual configuration drogue_deployment_altitude_m is required.",
    )
    main_deployment_altitude_m = _require_float(
        configuration.altitude_inputs.main_deployment_altitude_m,
        "Dual configuration main_deployment_altitude_m is required.",
    )

    analyzed_drogue = _analyze_parachute(
        configuration=configuration,
        parachute=drogue_parachute,
        deployment_altitude_m=drogue_deployment_altitude_m,
        catalogue_items=catalogue_items,
    )
    analyzed_main = _analyze_parachute(
        configuration=configuration,
        parachute=main_parachute,
        deployment_altitude_m=main_deployment_altitude_m,
        catalogue_items=catalogue_items,
    )

    apogee_altitude_m = configuration.altitude_inputs.apogee_altitude_m
    if apogee_altitude_m is not None:
        drogue_start_altitude_m = apogee_altitude_m
        recovery_basis_label = "from_apogee"
    else:
        drogue_start_altitude_m = drogue_deployment_altitude_m
        recovery_basis_label = "from_drogue_deployment_altitude"

    drogue_descent_velocity_mps = _require_float(
        analyzed_drogue.resulting_descent_velocity_mps,
        "Drogue analysis did not produce a resulting descent velocity.",
    )
    main_descent_velocity_mps = _require_float(
        analyzed_main.resulting_descent_velocity_mps,
        "Main analysis did not produce a resulting descent velocity.",
    )

    drogue_duration_s = phase_duration_s(
        start_altitude_m=drogue_start_altitude_m,
        end_altitude_m=main_deployment_altitude_m,
        descent_velocity_mps=drogue_descent_velocity_mps,
    )
    main_duration_s = phase_duration_s(
        start_altitude_m=main_deployment_altitude_m,
        end_altitude_m=0.0,
        descent_velocity_mps=main_descent_velocity_mps,
    )

    if configuration.wind_settings.mode == "constant":
        constant_wind_mps = _require_float(
            configuration.wind_settings.constant_wind_mps,
            "Constant wind mode requires constant_wind_mps.",
        )
        drogue_drift_m = drift_distance_m(drogue_duration_s, constant_wind_mps)
        main_drift_m = drift_distance_m(main_duration_s, constant_wind_mps)
    elif configuration.wind_settings.mode == "two_layer":
        aloft_wind_mps = _require_float(
            configuration.wind_settings.aloft_wind_mps,
            "Two-layer wind mode requires aloft_wind_mps.",
        )
        ground_wind_mps = _require_float(
            configuration.wind_settings.ground_wind_mps,
            "Two-layer wind mode requires ground_wind_mps.",
        )
        drogue_drift_m = drift_distance_m(drogue_duration_s, aloft_wind_mps)
        main_drift_m = drift_distance_m(main_duration_s, ground_wind_mps)
    else:
        raise AnalysisError(
            f"Unsupported wind mode for dual analysis: {configuration.wind_settings.mode!r}"
        )

    phase_summaries = [
        PhaseSummary(
            phase_name="drogue",
            start_altitude_m=drogue_start_altitude_m,
            end_altitude_m=main_deployment_altitude_m,
            parachute_id=analyzed_drogue.parachute_id,
            nominal_descent_velocity_mps=drogue_descent_velocity_mps,
            estimated_duration_s=drogue_duration_s,
            estimated_drift_m=drogue_drift_m,
        ),
        PhaseSummary(
            phase_name="main",
            start_altitude_m=main_deployment_altitude_m,
            end_altitude_m=0.0,
            parachute_id=analyzed_main.parachute_id,
            nominal_descent_velocity_mps=main_descent_velocity_mps,
            estimated_duration_s=main_duration_s,
            estimated_drift_m=main_drift_m,
        ),
    ]

    updated_parachutes = {
        analyzed_drogue.parachute_id: analyzed_drogue,
        analyzed_main.parachute_id: analyzed_main,
    }

    analysis_result = AnalysisResult(
        recovery_basis_label=recovery_basis_label,
        phase_summaries=phase_summaries,
        total_descent_time_s=drogue_duration_s + main_duration_s,
        total_estimated_drift_m=drogue_drift_m + main_drift_m,
        display_metrics={
            "sizing_available": True,
            "descent_time_available": True,
            "drift_available": True,
        },
    )
    analyzed_configuration = replace(
        configuration,
        parachutes=[
            updated_parachutes[parachute.parachute_id]
            for parachute in configuration.parachutes
        ],
        analysis_results=analysis_result,
        warnings=[],
    )
    return replace(
        analyzed_configuration,
        warnings=generate_configuration_warnings(analyzed_configuration, catalogue_items),
    )


def _analyze_parachute(
    configuration: Configuration,
    parachute: ParachuteSpec,
    deployment_altitude_m: float,
    catalogue_items: Sequence[CatalogueItem],
) -> ParachuteSpec:
    density_kg_per_m3 = resolve_density_kg_per_m3(
        altitude_m=deployment_altitude_m,
        manual_density_kg_per_m3=configuration.atmosphere_settings.manual_density_kg_per_m3,
    )
    theoretical = theoretical_diameter_m(
        mass_kg=configuration.rocket_mass_kg,
        density_kg_per_m3=density_kg_per_m3,
        cd=parachute.cd,
        target_descent_velocity_mps=parachute.target_descent_velocity_mps,
    )
    recommended = recommended_diameter_m(
        theoretical_diameter_m_value=theoretical,
        safety_margin_fraction=configuration.safety_margin_fraction,
    )
    matched_item = match_catalogue_item(
        family=parachute.family,
        recommended_diameter_m_value=recommended,
        catalogue_items=catalogue_items,
    )
    resulting_velocity = descent_velocity_for_diameter_m(
        mass_kg=configuration.rocket_mass_kg,
        density_kg_per_m3=density_kg_per_m3,
        cd=parachute.cd,
        diameter_m=matched_item.nominal_diameter_m,
    )
    return replace(
        parachute,
        theoretical_diameter_m=theoretical,
        recommended_diameter_m=recommended,
        selected_catalogue_item_id=matched_item.item_id,
        selected_nominal_diameter_m=matched_item.nominal_diameter_m,
        resulting_descent_velocity_mps=resulting_velocity,
    )


def _single_phase_drift_m(
    configuration: Configuration,
    start_altitude_m: float,
    deployment_altitude_m: float,
    descent_velocity_mps: float,
    total_descent_time_s: float,
) -> float:
    if configuration.wind_settings.mode == "constant":
        constant_wind_mps = _require_float(
            configuration.wind_settings.constant_wind_mps,
            "Constant wind mode requires constant_wind_mps.",
        )
        return drift_distance_m(total_descent_time_s, constant_wind_mps)

    if configuration.wind_settings.mode == "two_layer":
        aloft_wind_mps = _require_float(
            configuration.wind_settings.aloft_wind_mps,
            "Two-layer wind mode requires aloft_wind_mps.",
        )
        ground_wind_mps = _require_float(
            configuration.wind_settings.ground_wind_mps,
            "Two-layer wind mode requires ground_wind_mps.",
        )
        above_deployment_duration_s = phase_duration_s(
            start_altitude_m=start_altitude_m,
            end_altitude_m=deployment_altitude_m,
            descent_velocity_mps=descent_velocity_mps,
        )
        below_deployment_duration_s = phase_duration_s(
            start_altitude_m=min(start_altitude_m, deployment_altitude_m),
            end_altitude_m=0.0,
            descent_velocity_mps=descent_velocity_mps,
        )
        return drift_distance_m(
            above_deployment_duration_s,
            aloft_wind_mps,
        ) + drift_distance_m(
            below_deployment_duration_s,
            ground_wind_mps,
        )

    raise AnalysisError(
        f"Unsupported wind mode for single analysis: {configuration.wind_settings.mode!r}"
    )


def _find_parachute(configuration: Configuration, role: str) -> ParachuteSpec:
    for parachute in configuration.parachutes:
        if parachute.role == role:
            return parachute
    raise AnalysisError(f"No parachute with role {role!r} was found.")


def _require_float(value: float | None, message: str) -> float:
    if value is None:
        raise AnalysisError(message)
    return value
