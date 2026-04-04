"""Schema validation services for DRIFT models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from drift.models import Configuration, ParachuteSpec, Project

UNIT_SYSTEMS = {"si", "imperial"}
RECOVERY_MODES = {"single", "dual"}
ATMOSPHERE_MODES = {"standard_atmosphere", "manual_density"}
WIND_MODES = {"constant", "two_layer"}
PARACHUTE_ROLES = {"single", "drogue", "main"}
PARACHUTE_FAMILIES = {
    "flat_circular",
    "hemispherical",
    "toroidal",
    "cruciform",
    "ribbon",
    "streamer",
}
CD_SOURCES = {"preset", "manual_override"}


@dataclass(slots=True, frozen=True)
class ValidationIssue:
    """Represents one deterministic schema validation failure."""

    code: str
    field_path: str
    message: str


@dataclass(slots=True)
class ValidationResult:
    """Structured validation result for one project or configuration."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues

    def extend(self, issues: Iterable[ValidationIssue]) -> None:
        self.issues.extend(issues)


def validate_project(project: Project) -> ValidationResult:
    """Validate a DRIFT project model without performing calculations."""

    result = ValidationResult()

    _require_value(result, "schema_version", project.schema_version)
    _require_value(result, "project_id", project.project_id)
    _require_value(result, "project_name", project.project_name)
    _require_value(result, "created_at", project.created_at)
    _require_value(result, "updated_at", project.updated_at)
    _require_value(result, "default_unit_system", project.default_unit_system)
    _validate_enum(
        result,
        "default_unit_system",
        project.default_unit_system,
        UNIT_SYSTEMS,
    )

    for index, configuration in enumerate(project.configurations):
        result.extend(
            validate_configuration(
                configuration,
                field_prefix=f"configurations[{index}]",
            ).issues
        )

    return result


def validate_configuration(
    configuration: Configuration,
    *,
    field_prefix: str = "",
) -> ValidationResult:
    """Validate one DRIFT configuration model."""

    result = ValidationResult()

    _require_value(result, _path(field_prefix, "configuration_id"), configuration.configuration_id)
    _require_value(result, _path(field_prefix, "configuration_name"), configuration.configuration_name)
    _require_value(result, _path(field_prefix, "recovery_mode"), configuration.recovery_mode)
    _require_value(result, _path(field_prefix, "rocket_mass_kg"), configuration.rocket_mass_kg)
    _require_value(
        result,
        _path(field_prefix, "safety_margin_fraction"),
        configuration.safety_margin_fraction,
    )
    _require_value(
        result,
        _path(field_prefix, "display_unit_system"),
        configuration.display_unit_system,
    )

    _validate_enum(
        result,
        _path(field_prefix, "recovery_mode"),
        configuration.recovery_mode,
        RECOVERY_MODES,
    )
    _validate_enum(
        result,
        _path(field_prefix, "display_unit_system"),
        configuration.display_unit_system,
        UNIT_SYSTEMS,
    )
    _validate_positive(
        result,
        _path(field_prefix, "rocket_mass_kg"),
        configuration.rocket_mass_kg,
    )
    _validate_non_negative(
        result,
        _path(field_prefix, "safety_margin_fraction"),
        configuration.safety_margin_fraction,
    )

    _validate_atmosphere_settings(configuration, result, field_prefix)
    _validate_wind_settings(configuration, result, field_prefix)
    _validate_altitude_inputs(configuration, result, field_prefix)

    for index, parachute in enumerate(configuration.parachutes):
        _validate_parachute(
            parachute,
            result,
            field_prefix=_path(field_prefix, f"parachutes[{index}]"),
        )

    _validate_parachute_roles(configuration, result, field_prefix)
    return result


def _validate_atmosphere_settings(
    configuration: Configuration,
    result: ValidationResult,
    field_prefix: str,
) -> None:
    prefix = _path(field_prefix, "atmosphere_settings")
    settings = configuration.atmosphere_settings

    _require_value(result, _path(prefix, "mode"), settings.mode)
    _validate_enum(result, _path(prefix, "mode"), settings.mode, ATMOSPHERE_MODES)

    if settings.mode == "standard_atmosphere":
        if settings.manual_density_kg_per_m3 is not None:
            result.issues.append(
                ValidationIssue(
                    code="ATMOSPHERE_MODE_INCONSISTENT",
                    field_path=_path(prefix, "manual_density_kg_per_m3"),
                    message="manual_density_kg_per_m3 must be null when mode is standard_atmosphere.",
                )
            )
    elif settings.mode == "manual_density":
        if settings.manual_density_kg_per_m3 is None:
            result.issues.append(
                ValidationIssue(
                    code="REQUIRED_FIELD_MISSING",
                    field_path=_path(prefix, "manual_density_kg_per_m3"),
                    message="manual_density_kg_per_m3 is required when mode is manual_density.",
                )
            )
        else:
            _validate_positive(
                result,
                _path(prefix, "manual_density_kg_per_m3"),
                settings.manual_density_kg_per_m3,
            )


def _validate_wind_settings(
    configuration: Configuration,
    result: ValidationResult,
    field_prefix: str,
) -> None:
    prefix = _path(field_prefix, "wind_settings")
    settings = configuration.wind_settings

    _require_value(result, _path(prefix, "mode"), settings.mode)
    _validate_enum(result, _path(prefix, "mode"), settings.mode, WIND_MODES)

    if settings.mode == "constant":
        if settings.constant_wind_mps is None:
            result.issues.append(
                ValidationIssue(
                    code="REQUIRED_FIELD_MISSING",
                    field_path=_path(prefix, "constant_wind_mps"),
                    message="constant_wind_mps is required when mode is constant.",
                )
            )
        else:
            _validate_non_negative(
                result,
                _path(prefix, "constant_wind_mps"),
                settings.constant_wind_mps,
            )
    elif settings.mode == "two_layer":
        if settings.aloft_wind_mps is None:
            result.issues.append(
                ValidationIssue(
                    code="REQUIRED_FIELD_MISSING",
                    field_path=_path(prefix, "aloft_wind_mps"),
                    message="aloft_wind_mps is required when mode is two_layer.",
                )
            )
        else:
            _validate_non_negative(
                result,
                _path(prefix, "aloft_wind_mps"),
                settings.aloft_wind_mps,
            )

        if settings.ground_wind_mps is None:
            result.issues.append(
                ValidationIssue(
                    code="REQUIRED_FIELD_MISSING",
                    field_path=_path(prefix, "ground_wind_mps"),
                    message="ground_wind_mps is required when mode is two_layer.",
                )
            )
        else:
            _validate_non_negative(
                result,
                _path(prefix, "ground_wind_mps"),
                settings.ground_wind_mps,
            )


def _validate_altitude_inputs(
    configuration: Configuration,
    result: ValidationResult,
    field_prefix: str,
) -> None:
    prefix = _path(field_prefix, "altitude_inputs")
    altitudes = configuration.altitude_inputs

    if configuration.recovery_mode == "single":
        if altitudes.deployment_altitude_m is None:
            result.issues.append(
                ValidationIssue(
                    code="REQUIRED_FIELD_MISSING",
                    field_path=_path(prefix, "deployment_altitude_m"),
                    message="deployment_altitude_m is required for single deployment mode.",
                )
            )
        else:
            _validate_non_negative(
                result,
                _path(prefix, "deployment_altitude_m"),
                altitudes.deployment_altitude_m,
            )

        if (
            altitudes.apogee_altitude_m is not None
            and altitudes.deployment_altitude_m is not None
            and altitudes.apogee_altitude_m < altitudes.deployment_altitude_m
        ):
            result.issues.append(
                ValidationIssue(
                    code="ALTITUDE_ORDER_INVALID",
                    field_path=_path(prefix, "apogee_altitude_m"),
                    message="apogee_altitude_m must be greater than or equal to deployment_altitude_m in single mode.",
                )
            )

    elif configuration.recovery_mode == "dual":
        if altitudes.drogue_deployment_altitude_m is None:
            result.issues.append(
                ValidationIssue(
                    code="REQUIRED_FIELD_MISSING",
                    field_path=_path(prefix, "drogue_deployment_altitude_m"),
                    message="drogue_deployment_altitude_m is required for dual deployment mode.",
                )
            )
        else:
            _validate_non_negative(
                result,
                _path(prefix, "drogue_deployment_altitude_m"),
                altitudes.drogue_deployment_altitude_m,
            )

        if altitudes.main_deployment_altitude_m is None:
            result.issues.append(
                ValidationIssue(
                    code="REQUIRED_FIELD_MISSING",
                    field_path=_path(prefix, "main_deployment_altitude_m"),
                    message="main_deployment_altitude_m is required for dual deployment mode.",
                )
            )
        else:
            _validate_non_negative(
                result,
                _path(prefix, "main_deployment_altitude_m"),
                altitudes.main_deployment_altitude_m,
            )

        if (
            altitudes.drogue_deployment_altitude_m is not None
            and altitudes.main_deployment_altitude_m is not None
            and altitudes.drogue_deployment_altitude_m
            <= altitudes.main_deployment_altitude_m
        ):
            result.issues.append(
                ValidationIssue(
                    code="ALTITUDE_ORDER_INVALID",
                    field_path=_path(prefix, "drogue_deployment_altitude_m"),
                    message="drogue_deployment_altitude_m must be greater than main_deployment_altitude_m in dual mode.",
                )
            )

        if (
            altitudes.apogee_altitude_m is not None
            and altitudes.drogue_deployment_altitude_m is not None
            and altitudes.apogee_altitude_m < altitudes.drogue_deployment_altitude_m
        ):
            result.issues.append(
                ValidationIssue(
                    code="ALTITUDE_ORDER_INVALID",
                    field_path=_path(prefix, "apogee_altitude_m"),
                    message="apogee_altitude_m must be greater than or equal to drogue_deployment_altitude_m in dual mode.",
                )
            )


def _validate_parachute(
    parachute: ParachuteSpec,
    result: ValidationResult,
    *,
    field_prefix: str,
) -> None:
    _require_value(result, _path(field_prefix, "parachute_id"), parachute.parachute_id)
    _require_value(result, _path(field_prefix, "role"), parachute.role)
    _require_value(result, _path(field_prefix, "family"), parachute.family)
    _require_value(result, _path(field_prefix, "cd"), parachute.cd)
    _require_value(result, _path(field_prefix, "cd_source"), parachute.cd_source)
    _require_value(
        result,
        _path(field_prefix, "target_descent_velocity_mps"),
        parachute.target_descent_velocity_mps,
    )

    _validate_enum(result, _path(field_prefix, "role"), parachute.role, PARACHUTE_ROLES)
    _validate_enum(
        result,
        _path(field_prefix, "family"),
        parachute.family,
        PARACHUTE_FAMILIES,
    )
    _validate_enum(
        result,
        _path(field_prefix, "cd_source"),
        parachute.cd_source,
        CD_SOURCES,
    )
    _validate_positive(result, _path(field_prefix, "cd"), parachute.cd)
    _validate_positive(
        result,
        _path(field_prefix, "target_descent_velocity_mps"),
        parachute.target_descent_velocity_mps,
    )


def _validate_parachute_roles(
    configuration: Configuration,
    result: ValidationResult,
    field_prefix: str,
) -> None:
    prefix = _path(field_prefix, "parachutes")
    roles = [parachute.role for parachute in configuration.parachutes]

    if configuration.recovery_mode == "single":
        if len(configuration.parachutes) != 1 or roles.count("single") != 1:
            result.issues.append(
                ValidationIssue(
                    code="PARACHUTE_ROLE_INCONSISTENT",
                    field_path=prefix,
                    message="single mode requires exactly one parachute with role 'single'.",
                )
            )
    elif configuration.recovery_mode == "dual":
        if (
            len(configuration.parachutes) != 2
            or roles.count("drogue") != 1
            or roles.count("main") != 1
        ):
            result.issues.append(
                ValidationIssue(
                    code="PARACHUTE_ROLE_INCONSISTENT",
                    field_path=prefix,
                    message="dual mode requires exactly one 'drogue' parachute and one 'main' parachute.",
                )
            )


def _require_value(
    result: ValidationResult,
    field_path: str,
    value: object,
) -> None:
    if value is None:
        result.issues.append(
            ValidationIssue(
                code="REQUIRED_FIELD_MISSING",
                field_path=field_path,
                message=f"{field_path} is required.",
            )
        )


def _validate_enum(
    result: ValidationResult,
    field_path: str,
    value: object,
    allowed_values: set[str],
) -> None:
    if value is None:
        return
    if value not in allowed_values:
        result.issues.append(
            ValidationIssue(
                code="INVALID_ENUM_VALUE",
                field_path=field_path,
                message=f"{field_path} must be one of {sorted(allowed_values)}.",
            )
        )


def _validate_positive(
    result: ValidationResult,
    field_path: str,
    value: object,
) -> None:
    if value is None:
        return
    if value <= 0:
        result.issues.append(
            ValidationIssue(
                code="VALUE_MUST_BE_POSITIVE",
                field_path=field_path,
                message=f"{field_path} must be greater than 0.",
            )
        )


def _validate_non_negative(
    result: ValidationResult,
    field_path: str,
    value: object,
) -> None:
    if value is None:
        return
    if value < 0:
        result.issues.append(
            ValidationIssue(
                code="VALUE_MUST_BE_NON_NEGATIVE",
                field_path=field_path,
                message=f"{field_path} must be greater than or equal to 0.",
            )
        )


def _path(prefix: str, leaf: str) -> str:
    if not prefix:
        return leaf
    return f"{prefix}.{leaf}"
