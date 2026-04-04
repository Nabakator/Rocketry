"""Acceptance suite for DRIFT engine and persistence behaviour."""

from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from drift.models import Project
from drift.services.analysis import AnalysisError, analyze_configuration, analyze_project
from drift.services.persistence import load_project, save_project
from drift.services.validation import validate_project

from .fixtures import (
    catalogue_items,
    make_dual_configuration,
    make_project,
    make_single_configuration,
    make_single_configuration_from_imperial_inputs,
)

ABS_TOL = 1e-5


class AcceptanceSuiteTests(unittest.TestCase):
    """Acceptance cases AC-01 through AC-10 from the DRIFT MVP spec."""

    def setUp(self) -> None:
        self.catalogue = catalogue_items()

    def test_ac_01_single_deployment_with_known_apogee(self) -> None:
        configuration = make_single_configuration()
        analyzed = analyze_configuration(configuration, self.catalogue)
        result = analyzed.analysis_results

        self.assertIsNotNone(result)
        self.assertEqual(result.recovery_basis_label, "from_apogee")
        self.assertEqual(len(result.phase_summaries), 1)
        self.assertEqual(result.phase_summaries[0].phase_name, "single")
        self.assertEqual(result.phase_summaries[0].start_altitude_m, 900.0)
        self.assertEqual(result.phase_summaries[0].end_altitude_m, 0.0)
        self.assertIsNotNone(analyzed.parachutes[0].theoretical_diameter_m)
        self.assertIsNotNone(analyzed.parachutes[0].recommended_diameter_m)
        self.assertIsNotNone(analyzed.parachutes[0].selected_catalogue_item_id)
        self.assertIsNotNone(analyzed.parachutes[0].resulting_descent_velocity_mps)
        self.assertEqual(
            [warning.code for warning in analyzed.warnings],
            [],
        )

        project = make_project([analyzed])
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "ac01.json"
            save_project(project, path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            loaded = load_project(path)

        self.assertEqual(payload["schema_version"], "1.0.0")
        self.assertIsNone(
            payload["configurations"][0]["altitude_inputs"]["drogue_deployment_altitude_m"]
        )
        self.assertIsNone(
            payload["configurations"][0]["altitude_inputs"]["main_deployment_altitude_m"]
        )
        self.assertEqual(loaded.to_dict(), project.to_dict())

    def test_ac_02_single_deployment_without_apogee(self) -> None:
        configuration = make_single_configuration(apogee_altitude_m=None)
        analyzed = analyze_configuration(configuration, self.catalogue)
        result = analyzed.analysis_results

        self.assertIsNotNone(result)
        self.assertEqual(result.recovery_basis_label, "from_deployment_altitude")
        self.assertEqual(result.phase_summaries[0].start_altitude_m, 400.0)
        self.assertEqual(result.phase_summaries[0].end_altitude_m, 0.0)
        self.assertEqual([warning.code for warning in analyzed.warnings], [])

        project = make_project([analyzed])
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "ac02.json"
            save_project(project, path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            loaded = load_project(path)

        self.assertIn("apogee_altitude_m", payload["configurations"][0]["altitude_inputs"])
        self.assertIsNone(payload["configurations"][0]["altitude_inputs"]["apogee_altitude_m"])
        self.assertEqual(loaded.to_dict(), project.to_dict())

    def test_ac_03_dual_deployment_with_known_apogee(self) -> None:
        configuration = make_dual_configuration()
        analyzed = analyze_configuration(configuration, self.catalogue)
        result = analyzed.analysis_results

        self.assertIsNotNone(result)
        self.assertEqual(result.recovery_basis_label, "from_apogee")
        self.assertEqual([phase.phase_name for phase in result.phase_summaries], ["drogue", "main"])
        self.assertEqual(result.phase_summaries[0].start_altitude_m, 3000.0)
        self.assertEqual(result.phase_summaries[0].end_altitude_m, 500.0)
        self.assertEqual(result.phase_summaries[1].start_altitude_m, 500.0)
        self.assertEqual(result.phase_summaries[1].end_altitude_m, 0.0)
        self.assertEqual([warning.code for warning in analyzed.warnings], [])

        project = make_project([analyzed])
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "ac03.json"
            save_project(project, path)
            loaded = load_project(path)

        self.assertEqual(loaded.to_dict(), project.to_dict())

    def test_ac_04_dual_deployment_without_apogee(self) -> None:
        configuration = make_dual_configuration(apogee_altitude_m=None)
        analyzed = analyze_configuration(configuration, self.catalogue)
        result = analyzed.analysis_results

        self.assertIsNotNone(result)
        self.assertEqual(result.recovery_basis_label, "from_drogue_deployment_altitude")
        self.assertEqual(result.phase_summaries[0].start_altitude_m, 2800.0)
        self.assertEqual(result.phase_summaries[0].end_altitude_m, 500.0)
        self.assertEqual(result.phase_summaries[1].start_altitude_m, 500.0)
        self.assertEqual([warning.code for warning in analyzed.warnings], [])

        project = make_project([analyzed])
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "ac04.json"
            save_project(project, path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            loaded = load_project(path)

        self.assertIsNone(payload["configurations"][0]["altitude_inputs"]["apogee_altitude_m"])
        self.assertEqual(loaded.to_dict(), project.to_dict())

    def test_ac_05_invalid_altitude_ordering(self) -> None:
        invalid_configuration = make_dual_configuration(
            apogee_altitude_m=2500.0,
            drogue_deployment_altitude_m=400.0,
            main_deployment_altitude_m=500.0,
        )
        project = make_project([invalid_configuration], project_id="proj_invalid")

        with self.assertRaises(AnalysisError):
            analyze_configuration(invalid_configuration, self.catalogue)

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "ac05.json"
            save_project(project, path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            loaded = load_project(path)

        validation_result = validate_project(loaded)
        self.assertFalse(validation_result.is_valid)
        self.assertIsNone(payload["configurations"][0]["analysis_results"])
        self.assertIn(
            "ALTITUDE_ORDER_INVALID",
            [issue.code for issue in validation_result.issues],
        )

    def test_ac_06_manual_density_override(self) -> None:
        configuration = make_single_configuration(
            atmosphere_mode="manual_density",
            manual_density_kg_per_m3=1.15,
        )
        analyzed = analyze_configuration(configuration, self.catalogue)

        self.assertIn(
            "MANUAL_DENSITY_OVERRIDE_ACTIVE",
            [warning.code for warning in analyzed.warnings],
        )

        project = make_project([analyzed])
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "ac06.json"
            save_project(project, path)
            loaded = load_project(path)

        loaded_configuration = loaded.configurations[0]
        self.assertEqual(loaded_configuration.atmosphere_settings.mode, "manual_density")
        self.assertEqual(
            loaded_configuration.atmosphere_settings.manual_density_kg_per_m3,
            1.15,
        )
        self.assertEqual(loaded.to_dict(), project.to_dict())

    def test_ac_07_cd_override_with_catalogue_match(self) -> None:
        configuration = make_single_configuration(
            cd=1.8,
            cd_source="manual_override",
            atmosphere_mode="standard_atmosphere",
            manual_density_kg_per_m3=None,
        )
        analyzed = analyze_configuration(configuration, self.catalogue)

        self.assertIn(
            "MANUAL_CD_OVERRIDE_ACTIVE",
            [warning.code for warning in analyzed.warnings],
        )
        self.assertEqual(analyzed.parachutes[0].family, "hemispherical")
        self.assertIsNotNone(analyzed.parachutes[0].selected_catalogue_item_id)

        project = make_project([analyzed])
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "ac07.json"
            save_project(project, path)
            loaded = load_project(path)

        reanalyzed = analyze_configuration(loaded.configurations[0], self.catalogue)
        self.assertTrue(
            math.isclose(
                reanalyzed.parachutes[0].recommended_diameter_m,
                analyzed.parachutes[0].recommended_diameter_m,
                abs_tol=ABS_TOL,
            )
        )
        self.assertTrue(
            math.isclose(
                reanalyzed.parachutes[0].resulting_descent_velocity_mps,
                analyzed.parachutes[0].resulting_descent_velocity_mps,
                abs_tol=ABS_TOL,
            )
        )

    def test_ac_08_catalogue_out_of_range_result(self) -> None:
        cases = [
            (
                "below_minimum",
                make_single_configuration(
                    target_descent_velocity_mps=20.0,
                    safety_margin_fraction=0.0,
                ),
                "hemi_1_6",
            ),
            (
                "above_maximum",
                make_single_configuration(
                    rocket_mass_kg=45.0,
                    target_descent_velocity_mps=4.0,
                    safety_margin_fraction=0.15,
                ),
                "hemi_3_0",
            ),
        ]

        for label, configuration, expected_item_id in cases:
            with self.subTest(label=label):
                analyzed = analyze_configuration(configuration, self.catalogue)
                codes = [warning.code for warning in analyzed.warnings]

                self.assertIsNotNone(analyzed.parachutes[0].theoretical_diameter_m)
                self.assertIsNotNone(analyzed.parachutes[0].recommended_diameter_m)
                self.assertEqual(analyzed.parachutes[0].selected_catalogue_item_id, expected_item_id)
                self.assertIn("CATALOGUE_OUT_OF_RANGE", codes)

                project = make_project([analyzed], project_id=f"proj_{label}")
                with tempfile.TemporaryDirectory() as tmp_dir:
                    path = Path(tmp_dir) / f"{label}.json"
                    save_project(project, path)
                    loaded = load_project(path)

                self.assertEqual(loaded.to_dict(), project.to_dict())

    def test_ac_09_comparison_of_two_valid_configurations(self) -> None:
        project = make_project(
            [
                make_single_configuration(configuration_id="cfg_compare_single"),
                make_dual_configuration(
                    configuration_id="cfg_compare_dual",
                    display_unit_system="si",
                ),
            ],
            project_id="proj_compare",
        )
        analyzed_project = analyze_project(project, self.catalogue)

        self.assertEqual(len(analyzed_project.configurations), 2)
        self.assertEqual(
            [configuration.display_unit_system for configuration in analyzed_project.configurations],
            ["si", "si"],
        )

        comparison_rows = []
        for configuration in analyzed_project.configurations:
            comparison_rows.append(
                {
                    "mode": configuration.recovery_mode,
                    "diameters": [
                        parachute.selected_nominal_diameter_m for parachute in configuration.parachutes
                    ],
                    "velocities": [
                        parachute.resulting_descent_velocity_mps for parachute in configuration.parachutes
                    ],
                    "descent_time_s": configuration.analysis_results.total_descent_time_s,
                    "drift_m": configuration.analysis_results.total_estimated_drift_m,
                    "warning_codes": [warning.code for warning in configuration.warnings],
                }
            )

        self.assertEqual([row["mode"] for row in comparison_rows], ["single", "dual"])
        self.assertTrue(all(row["descent_time_s"] is not None for row in comparison_rows))
        self.assertTrue(all(row["drift_m"] is not None for row in comparison_rows))

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "ac09.json"
            save_project(analyzed_project, path)
            loaded = load_project(path)

        self.assertEqual(loaded.to_dict(), analyzed_project.to_dict())

    def test_ac_10_si_imperial_round_trip_consistency(self) -> None:
        si_configuration = make_single_configuration(
            configuration_id="cfg_single_si",
            configuration_name="Single SI Source",
        )
        imperial_configuration = make_single_configuration_from_imperial_inputs()

        analyzed_si = analyze_configuration(si_configuration, self.catalogue)
        analyzed_imperial = analyze_configuration(imperial_configuration, self.catalogue)

        si_parachute = analyzed_si.parachutes[0]
        imperial_parachute = analyzed_imperial.parachutes[0]

        self.assertTrue(
            math.isclose(
                si_parachute.theoretical_diameter_m,
                imperial_parachute.theoretical_diameter_m,
                abs_tol=ABS_TOL,
            )
        )
        self.assertTrue(
            math.isclose(
                si_parachute.recommended_diameter_m,
                imperial_parachute.recommended_diameter_m,
                abs_tol=ABS_TOL,
            )
        )
        self.assertEqual(
            si_parachute.selected_nominal_diameter_m,
            imperial_parachute.selected_nominal_diameter_m,
        )
        self.assertTrue(
            math.isclose(
                analyzed_si.analysis_results.total_descent_time_s,
                analyzed_imperial.analysis_results.total_descent_time_s,
                abs_tol=ABS_TOL,
            )
        )
        self.assertTrue(
            math.isclose(
                analyzed_si.analysis_results.total_estimated_drift_m,
                analyzed_imperial.analysis_results.total_estimated_drift_m,
                abs_tol=ABS_TOL,
            )
        )

        project = make_project(
            [analyzed_imperial],
            project_id="proj_imperial",
            default_unit_system="imperial",
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "ac10.json"
            save_project(project, path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            loaded = load_project(path)

        persisted_configuration = payload["configurations"][0]
        self.assertEqual(persisted_configuration["display_unit_system"], "imperial")
        self.assertTrue(
            math.isclose(
                persisted_configuration["rocket_mass_kg"],
                analyzed_imperial.rocket_mass_kg,
                abs_tol=ABS_TOL,
            )
        )
        self.assertTrue(
            math.isclose(
                persisted_configuration["altitude_inputs"]["deployment_altitude_m"],
                analyzed_imperial.altitude_inputs.deployment_altitude_m,
                abs_tol=ABS_TOL,
            )
        )
        self.assertEqual(loaded.to_dict(), project.to_dict())


if __name__ == "__main__":
    unittest.main()
