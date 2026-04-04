"""Stable acceptance-test fixtures for DRIFT."""

from __future__ import annotations

from drift.models import (
    AltitudeInputs,
    AtmosphereSettings,
    CatalogueItem,
    Configuration,
    ParachuteSpec,
    Project,
    WindSettings,
)

LB_TO_KG = 0.45359237
FT_TO_M = 0.3048
FTPS_TO_MPS = 0.3048


def catalogue_items() -> list[CatalogueItem]:
    return [
        CatalogueItem(
            item_id="hemi_1_6",
            vendor="Vendor",
            product_name="1.6 m Hemispherical",
            family="hemispherical",
            nominal_diameter_m=1.6,
            nominal_diameter_display="1.6 m",
        ),
        CatalogueItem(
            item_id="hemi_1_8",
            vendor="Vendor",
            product_name="1.8 m Hemispherical",
            family="hemispherical",
            nominal_diameter_m=1.8,
            nominal_diameter_display="1.8 m",
        ),
        CatalogueItem(
            item_id="hemi_2_0",
            vendor="Vendor",
            product_name="2.0 m Hemispherical",
            family="hemispherical",
            nominal_diameter_m=2.0,
            nominal_diameter_display="2.0 m",
        ),
        CatalogueItem(
            item_id="hemi_2_2",
            vendor="Vendor",
            product_name="2.2 m Hemispherical",
            family="hemispherical",
            nominal_diameter_m=2.2,
            nominal_diameter_display="2.2 m",
        ),
        CatalogueItem(
            item_id="hemi_2_5",
            vendor="Vendor",
            product_name="2.5 m Hemispherical",
            family="hemispherical",
            nominal_diameter_m=2.5,
            nominal_diameter_display="2.5 m",
        ),
        CatalogueItem(
            item_id="hemi_3_0",
            vendor="Vendor",
            product_name="3.0 m Hemispherical",
            family="hemispherical",
            nominal_diameter_m=3.0,
            nominal_diameter_display="3.0 m",
        ),
        CatalogueItem(
            item_id="ribbon_1_0",
            vendor="Vendor",
            product_name="1.0 m Ribbon",
            family="ribbon",
            nominal_diameter_m=1.0,
            nominal_diameter_display="1.0 m",
        ),
        CatalogueItem(
            item_id="ribbon_1_2",
            vendor="Vendor",
            product_name="1.2 m Ribbon",
            family="ribbon",
            nominal_diameter_m=1.2,
            nominal_diameter_display="1.2 m",
        ),
        CatalogueItem(
            item_id="ribbon_1_5",
            vendor="Vendor",
            product_name="1.5 m Ribbon",
            family="ribbon",
            nominal_diameter_m=1.5,
            nominal_diameter_display="1.5 m",
        ),
        CatalogueItem(
            item_id="ribbon_1_8",
            vendor="Vendor",
            product_name="1.8 m Ribbon",
            family="ribbon",
            nominal_diameter_m=1.8,
            nominal_diameter_display="1.8 m",
        ),
    ]


def make_project(
    configurations: list[Configuration],
    *,
    project_id: str = "proj_acceptance",
    project_name: str = "Acceptance Project",
    default_unit_system: str = "si",
) -> Project:
    active_configuration_id = configurations[0].configuration_id if configurations else None
    return Project(
        project_id=project_id,
        project_name=project_name,
        description=None,
        created_at="2026-04-04T12:00:00Z",
        updated_at="2026-04-04T12:30:00Z",
        default_unit_system=default_unit_system,
        active_configuration_id=active_configuration_id,
        configurations=configurations,
    )


def make_single_configuration(
    *,
    configuration_id: str = "cfg_single",
    configuration_name: str = "Single Configuration",
    rocket_mass_kg: float = 9.0,
    safety_margin_fraction: float = 0.1,
    display_unit_system: str = "si",
    atmosphere_mode: str = "standard_atmosphere",
    manual_density_kg_per_m3: float | None = None,
    wind_mode: str = "constant",
    constant_wind_mps: float | None = 2.0,
    aloft_wind_mps: float | None = None,
    ground_wind_mps: float | None = None,
    deployment_altitude_m: float = 400.0,
    apogee_altitude_m: float | None = 900.0,
    family: str = "hemispherical",
    cd: float = 1.5,
    cd_source: str = "preset",
    target_descent_velocity_mps: float = 6.0,
) -> Configuration:
    return Configuration(
        configuration_id=configuration_id,
        configuration_name=configuration_name,
        recovery_mode="single",
        rocket_mass_kg=rocket_mass_kg,
        safety_margin_fraction=safety_margin_fraction,
        display_unit_system=display_unit_system,
        atmosphere_settings=AtmosphereSettings(
            mode=atmosphere_mode,
            manual_density_kg_per_m3=manual_density_kg_per_m3,
        ),
        wind_settings=WindSettings(
            mode=wind_mode,
            constant_wind_mps=constant_wind_mps,
            aloft_wind_mps=aloft_wind_mps,
            ground_wind_mps=ground_wind_mps,
        ),
        altitude_inputs=AltitudeInputs(
            deployment_altitude_m=deployment_altitude_m,
            apogee_altitude_m=apogee_altitude_m,
        ),
        parachutes=[
            ParachuteSpec(
                parachute_id=f"{configuration_id}_single",
                role="single",
                family=family,
                cd=cd,
                cd_source=cd_source,
                target_descent_velocity_mps=target_descent_velocity_mps,
            )
        ],
    )


def make_dual_configuration(
    *,
    configuration_id: str = "cfg_dual",
    configuration_name: str = "Dual Configuration",
    rocket_mass_kg: float = 12.0,
    safety_margin_fraction: float = 0.1,
    display_unit_system: str = "si",
    atmosphere_mode: str = "standard_atmosphere",
    manual_density_kg_per_m3: float | None = None,
    wind_mode: str = "two_layer",
    constant_wind_mps: float | None = None,
    aloft_wind_mps: float | None = 2.0,
    ground_wind_mps: float | None = 1.0,
    apogee_altitude_m: float | None = 3000.0,
    drogue_deployment_altitude_m: float = 2800.0,
    main_deployment_altitude_m: float = 500.0,
    drogue_family: str = "ribbon",
    drogue_cd: float = 0.7,
    drogue_cd_source: str = "preset",
    drogue_target_descent_velocity_mps: float = 18.0,
    main_family: str = "hemispherical",
    main_cd: float = 1.5,
    main_cd_source: str = "preset",
    main_target_descent_velocity_mps: float = 6.0,
) -> Configuration:
    return Configuration(
        configuration_id=configuration_id,
        configuration_name=configuration_name,
        recovery_mode="dual",
        rocket_mass_kg=rocket_mass_kg,
        safety_margin_fraction=safety_margin_fraction,
        display_unit_system=display_unit_system,
        atmosphere_settings=AtmosphereSettings(
            mode=atmosphere_mode,
            manual_density_kg_per_m3=manual_density_kg_per_m3,
        ),
        wind_settings=WindSettings(
            mode=wind_mode,
            constant_wind_mps=constant_wind_mps,
            aloft_wind_mps=aloft_wind_mps,
            ground_wind_mps=ground_wind_mps,
        ),
        altitude_inputs=AltitudeInputs(
            apogee_altitude_m=apogee_altitude_m,
            drogue_deployment_altitude_m=drogue_deployment_altitude_m,
            main_deployment_altitude_m=main_deployment_altitude_m,
        ),
        parachutes=[
            ParachuteSpec(
                parachute_id=f"{configuration_id}_drogue",
                role="drogue",
                family=drogue_family,
                cd=drogue_cd,
                cd_source=drogue_cd_source,
                target_descent_velocity_mps=drogue_target_descent_velocity_mps,
            ),
            ParachuteSpec(
                parachute_id=f"{configuration_id}_main",
                role="main",
                family=main_family,
                cd=main_cd,
                cd_source=main_cd_source,
                target_descent_velocity_mps=main_target_descent_velocity_mps,
            ),
        ],
    )


def make_single_configuration_from_imperial_inputs() -> Configuration:
    """Build a configuration from imperial source values, converted to canonical SI."""

    rocket_mass_lb = 19.84160329
    deployment_altitude_ft = 1312.33595801
    apogee_altitude_ft = 2952.75590551
    constant_wind_ftps = 6.56167979
    target_descent_velocity_ftps = 19.68503937

    return make_single_configuration(
        configuration_id="cfg_single_imperial",
        configuration_name="Single Imperial Source",
        rocket_mass_kg=rocket_mass_lb * LB_TO_KG,
        display_unit_system="imperial",
        wind_mode="constant",
        constant_wind_mps=constant_wind_ftps * FTPS_TO_MPS,
        deployment_altitude_m=deployment_altitude_ft * FT_TO_M,
        apogee_altitude_m=apogee_altitude_ft * FT_TO_M,
        target_descent_velocity_mps=target_descent_velocity_ftps * FTPS_TO_MPS,
    )
