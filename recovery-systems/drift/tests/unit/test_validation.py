"""Schema validation tests for DRIFT."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from drift.models import (
    AltitudeInputs,
    AtmosphereSettings,
    Configuration,
    ParachuteSpec,
    Project,
    WindSettings,
)
from drift.services.persistence import load_project, save_project
from drift.services.validation import validate_configuration, validate_project


def make_valid_single_configuration() -> Configuration:
    return Configuration(
        configuration_id="cfg_single",
        configuration_name="Single",
        recovery_mode="single",
        rocket_mass_kg=10.0,
        safety_margin_fraction=0.1,
        display_unit_system="si",
        atmosphere_settings=AtmosphereSettings(
            mode="standard_atmosphere",
            manual_density_kg_per_m3=None,
        ),
        wind_settings=WindSettings(
            mode="constant",
            constant_wind_mps=5.0,
        ),
        altitude_inputs=AltitudeInputs(
            deployment_altitude_m=500.0,
            apogee_altitude_m=1200.0,
        ),
        parachutes=[
            ParachuteSpec(
                parachute_id="chute_single",
                role="single",
                family="hemispherical",
                cd=1.5,
                cd_source="preset",
                target_descent_velocity_mps=6.0,
            )
        ],
    )


def make_valid_dual_configuration() -> Configuration:
    return Configuration(
        configuration_id="cfg_dual",
        configuration_name="Dual",
        recovery_mode="dual",
        rocket_mass_kg=18.0,
        safety_margin_fraction=0.2,
        display_unit_system="imperial",
        atmosphere_settings=AtmosphereSettings(
            mode="manual_density",
            manual_density_kg_per_m3=1.18,
        ),
        wind_settings=WindSettings(
            mode="two_layer",
            aloft_wind_mps=12.0,
            ground_wind_mps=4.0,
        ),
        altitude_inputs=AltitudeInputs(
            apogee_altitude_m=3200.0,
            drogue_deployment_altitude_m=3000.0,
            main_deployment_altitude_m=500.0,
        ),
        parachutes=[
            ParachuteSpec(
                parachute_id="chute_drogue",
                role="drogue",
                family="ribbon",
                cd=0.7,
                cd_source="preset",
                target_descent_velocity_mps=20.0,
            ),
            ParachuteSpec(
                parachute_id="chute_main",
                role="main",
                family="hemispherical",
                cd=1.5,
                cd_source="manual_override",
                target_descent_velocity_mps=6.0,
            ),
        ],
    )


class ValidationTests(unittest.TestCase):
    def test_valid_single_configuration_passes(self) -> None:
        result = validate_configuration(make_valid_single_configuration())
        self.assertTrue(result.is_valid)
        self.assertEqual(result.issues, [])

    def test_valid_dual_configuration_passes(self) -> None:
        result = validate_configuration(make_valid_dual_configuration())
        self.assertTrue(result.is_valid)
        self.assertEqual(result.issues, [])

    def test_invalid_enums_and_positive_rules_are_caught(self) -> None:
        configuration = make_valid_single_configuration()
        configuration.display_unit_system = "metric"
        configuration.rocket_mass_kg = 0.0
        configuration.parachutes[0].family = "round"
        configuration.parachutes[0].cd = -1.0
        configuration.parachutes[0].target_descent_velocity_mps = 0.0

        result = validate_configuration(configuration)
        codes = [issue.code for issue in result.issues]

        self.assertIn("INVALID_ENUM_VALUE", codes)
        self.assertIn("VALUE_MUST_BE_POSITIVE", codes)

    def test_single_mode_altitude_and_role_rules_are_enforced(self) -> None:
        configuration = make_valid_single_configuration()
        configuration.altitude_inputs.deployment_altitude_m = None
        configuration.altitude_inputs.apogee_altitude_m = 100.0
        configuration.parachutes.append(
            ParachuteSpec(
                parachute_id="chute_extra",
                role="main",
                family="hemispherical",
                cd=1.5,
                cd_source="preset",
                target_descent_velocity_mps=6.0,
            )
        )

        result = validate_configuration(configuration)
        issue_map = {issue.field_path: issue.code for issue in result.issues}

        self.assertEqual(
            issue_map["altitude_inputs.deployment_altitude_m"],
            "REQUIRED_FIELD_MISSING",
        )
        self.assertEqual(
            issue_map["parachutes"],
            "PARACHUTE_ROLE_INCONSISTENT",
        )

    def test_dual_mode_altitude_rules_are_enforced(self) -> None:
        configuration = make_valid_dual_configuration()
        configuration.altitude_inputs.drogue_deployment_altitude_m = 400.0
        configuration.altitude_inputs.main_deployment_altitude_m = 500.0
        configuration.altitude_inputs.apogee_altitude_m = 300.0

        result = validate_configuration(configuration)
        codes = [issue.code for issue in result.issues]

        self.assertEqual(codes.count("ALTITUDE_ORDER_INVALID"), 2)

    def test_wind_and_atmosphere_mode_rules_are_enforced(self) -> None:
        configuration = make_valid_single_configuration()
        configuration.atmosphere_settings.mode = "manual_density"
        configuration.atmosphere_settings.manual_density_kg_per_m3 = None
        configuration.wind_settings.mode = "two_layer"
        configuration.wind_settings.aloft_wind_mps = None
        configuration.wind_settings.ground_wind_mps = -1.0

        result = validate_configuration(configuration)
        issue_map = {issue.field_path: issue.code for issue in result.issues}

        self.assertEqual(
            issue_map["atmosphere_settings.manual_density_kg_per_m3"],
            "REQUIRED_FIELD_MISSING",
        )
        self.assertEqual(
            issue_map["wind_settings.aloft_wind_mps"],
            "REQUIRED_FIELD_MISSING",
        )
        self.assertEqual(
            issue_map["wind_settings.ground_wind_mps"],
            "VALUE_MUST_BE_NON_NEGATIVE",
        )

    def test_invalid_draft_project_still_round_trips_and_validates(self) -> None:
        configuration = make_valid_dual_configuration()
        configuration.altitude_inputs.drogue_deployment_altitude_m = 100.0
        configuration.altitude_inputs.main_deployment_altitude_m = 500.0
        configuration.analysis_results = None
        project = Project(
            project_id="proj_invalid",
            project_name="Draft",
            description=None,
            created_at="2026-04-04T12:00:00Z",
            updated_at="2026-04-04T12:30:00Z",
            default_unit_system="si",
            active_configuration_id="cfg_dual",
            configurations=[configuration],
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "project.json"
            save_project(project, path)
            loaded = load_project(path)

        result = validate_project(loaded)
        self.assertFalse(result.is_valid)
        self.assertEqual(
            loaded.configurations[0].analysis_results,
            None,
        )
        self.assertIn(
            "ALTITUDE_ORDER_INVALID",
            [issue.code for issue in result.issues],
        )


if __name__ == "__main__":
    unittest.main()
