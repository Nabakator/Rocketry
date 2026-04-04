"""Configuration-oriented models for DRIFT."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .phases import AnalysisResult


@dataclass(slots=True)
class AtmosphereSettings:
    """Persistence shape for atmosphere inputs."""

    mode: str = "standard_atmosphere"
    manual_density_kg_per_m3: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "manual_density_kg_per_m3": self.manual_density_kg_per_m3,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AtmosphereSettings":
        return cls(
            mode=data["mode"],
            manual_density_kg_per_m3=data.get("manual_density_kg_per_m3"),
        )


@dataclass(slots=True)
class WindSettings:
    """Persistence shape for wind inputs."""

    mode: str = "constant"
    constant_wind_mps: float | None = None
    aloft_wind_mps: float | None = None
    ground_wind_mps: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "constant_wind_mps": self.constant_wind_mps,
            "aloft_wind_mps": self.aloft_wind_mps,
            "ground_wind_mps": self.ground_wind_mps,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WindSettings":
        return cls(
            mode=data["mode"],
            constant_wind_mps=data.get("constant_wind_mps"),
            aloft_wind_mps=data.get("aloft_wind_mps"),
            ground_wind_mps=data.get("ground_wind_mps"),
        )


@dataclass(slots=True)
class AltitudeInputs:
    """Persistence shape for single and dual deployment altitude inputs."""

    deployment_altitude_m: float | None = None
    apogee_altitude_m: float | None = None
    drogue_deployment_altitude_m: float | None = None
    main_deployment_altitude_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment_altitude_m": self.deployment_altitude_m,
            "apogee_altitude_m": self.apogee_altitude_m,
            "drogue_deployment_altitude_m": self.drogue_deployment_altitude_m,
            "main_deployment_altitude_m": self.main_deployment_altitude_m,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AltitudeInputs":
        return cls(
            deployment_altitude_m=data.get("deployment_altitude_m"),
            apogee_altitude_m=data.get("apogee_altitude_m"),
            drogue_deployment_altitude_m=data.get("drogue_deployment_altitude_m"),
            main_deployment_altitude_m=data.get("main_deployment_altitude_m"),
        )


@dataclass(slots=True)
class Warning:
    """Represents one deterministic warning or informational note."""

    code: str
    severity: str
    title: str
    message: str
    source_field: str | None
    triggered_rule: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "source_field": self.source_field,
            "triggered_rule": self.triggered_rule,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Warning":
        return cls(
            code=data["code"],
            severity=data["severity"],
            title=data["title"],
            message=data["message"],
            source_field=data.get("source_field"),
            triggered_rule=data["triggered_rule"],
        )


@dataclass(slots=True)
class ParachuteSpec:
    """Represents one parachute entry in a configuration."""

    parachute_id: str
    role: str
    family: str
    cd: float
    cd_source: str
    target_descent_velocity_mps: float
    theoretical_diameter_m: float | None = None
    recommended_diameter_m: float | None = None
    selected_catalogue_item_id: str | None = None
    selected_nominal_diameter_m: float | None = None
    resulting_descent_velocity_mps: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "parachute_id": self.parachute_id,
            "role": self.role,
            "family": self.family,
            "cd": self.cd,
            "cd_source": self.cd_source,
            "target_descent_velocity_mps": self.target_descent_velocity_mps,
            "theoretical_diameter_m": self.theoretical_diameter_m,
            "recommended_diameter_m": self.recommended_diameter_m,
            "selected_catalogue_item_id": self.selected_catalogue_item_id,
            "selected_nominal_diameter_m": self.selected_nominal_diameter_m,
            "resulting_descent_velocity_mps": self.resulting_descent_velocity_mps,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParachuteSpec":
        return cls(
            parachute_id=data["parachute_id"],
            role=data["role"],
            family=data["family"],
            cd=data["cd"],
            cd_source=data["cd_source"],
            target_descent_velocity_mps=data["target_descent_velocity_mps"],
            theoretical_diameter_m=data.get("theoretical_diameter_m"),
            recommended_diameter_m=data.get("recommended_diameter_m"),
            selected_catalogue_item_id=data.get("selected_catalogue_item_id"),
            selected_nominal_diameter_m=data.get("selected_nominal_diameter_m"),
            resulting_descent_velocity_mps=data.get("resulting_descent_velocity_mps"),
        )


@dataclass(slots=True)
class Configuration:
    """Represents one recovery design option."""

    configuration_id: str
    configuration_name: str
    recovery_mode: str
    rocket_mass_kg: float
    safety_margin_fraction: float
    display_unit_system: str
    atmosphere_settings: AtmosphereSettings = field(default_factory=AtmosphereSettings)
    wind_settings: WindSettings = field(default_factory=WindSettings)
    altitude_inputs: AltitudeInputs = field(default_factory=AltitudeInputs)
    parachutes: list[ParachuteSpec] = field(default_factory=list)
    analysis_results: AnalysisResult | None = None
    warnings: list[Warning] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration_id": self.configuration_id,
            "configuration_name": self.configuration_name,
            "recovery_mode": self.recovery_mode,
            "rocket_mass_kg": self.rocket_mass_kg,
            "safety_margin_fraction": self.safety_margin_fraction,
            "display_unit_system": self.display_unit_system,
            "atmosphere_settings": self.atmosphere_settings.to_dict(),
            "wind_settings": self.wind_settings.to_dict(),
            "altitude_inputs": self.altitude_inputs.to_dict(),
            "parachutes": [parachute.to_dict() for parachute in self.parachutes],
            "analysis_results": (
                None if self.analysis_results is None else self.analysis_results.to_dict()
            ),
            "warnings": [warning.to_dict() for warning in self.warnings],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Configuration":
        analysis_data = data.get("analysis_results")
        return cls(
            configuration_id=data["configuration_id"],
            configuration_name=data["configuration_name"],
            recovery_mode=data["recovery_mode"],
            rocket_mass_kg=data["rocket_mass_kg"],
            safety_margin_fraction=data["safety_margin_fraction"],
            display_unit_system=data["display_unit_system"],
            atmosphere_settings=AtmosphereSettings.from_dict(data["atmosphere_settings"]),
            wind_settings=WindSettings.from_dict(data["wind_settings"]),
            altitude_inputs=AltitudeInputs.from_dict(data["altitude_inputs"]),
            parachutes=[
                ParachuteSpec.from_dict(item) for item in data.get("parachutes", [])
            ],
            analysis_results=(
                None if analysis_data is None else AnalysisResult.from_dict(analysis_data)
            ),
            warnings=[Warning.from_dict(item) for item in data.get("warnings", [])],
        )
