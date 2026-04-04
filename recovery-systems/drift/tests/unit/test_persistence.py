"""Round-trip tests for DRIFT model persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from drift.models import (
    AltitudeInputs,
    AtmosphereSettings,
    Configuration,
    ParachuteSpec,
    Project,
    Warning,
    WindSettings,
)
from drift.services.persistence import load_project, save_project


class PersistenceRoundTripTests(unittest.TestCase):
    def test_project_round_trip_preserves_explicit_nulls(self) -> None:
        project = Project(
            project_id="proj_001",
            project_name="Test Project",
            description=None,
            created_at="2026-04-04T12:00:00Z",
            updated_at="2026-04-04T12:30:00Z",
            default_unit_system="si",
            active_configuration_id="cfg_draft",
            configurations=[
                Configuration(
                    configuration_id="cfg_draft",
                    configuration_name="Draft Configuration",
                    recovery_mode="single",
                    rocket_mass_kg=12.5,
                    safety_margin_fraction=0.1,
                    display_unit_system="imperial",
                    atmosphere_settings=AtmosphereSettings(
                        mode="manual_density",
                        manual_density_kg_per_m3=1.18,
                    ),
                    wind_settings=WindSettings(
                        mode="constant",
                        constant_wind_mps=6.0,
                    ),
                    altitude_inputs=AltitudeInputs(
                        deployment_altitude_m=500.0,
                        apogee_altitude_m=None,
                    ),
                    parachutes=[
                        ParachuteSpec(
                            parachute_id="chute_single",
                            role="single",
                            family="hemispherical",
                            cd=1.5,
                            cd_source="manual_override",
                            target_descent_velocity_mps=6.0,
                        )
                    ],
                    analysis_results=None,
                    warnings=[
                        Warning(
                            code="MANUAL_CD_OVERRIDE_ACTIVE",
                            severity="info",
                            title="Manual Cd override active",
                            message="The default Cd value has been overridden.",
                            source_field="parachutes[0].cd",
                            triggered_rule="cd_source == manual_override",
                        )
                    ],
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "project.json"
            save_project(project, path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            reloaded = load_project(path)

        configuration_data = payload["configurations"][0]
        self.assertEqual(payload["schema_version"], "1.0.0")
        self.assertIsNone(payload["description"])
        self.assertIsNone(configuration_data["analysis_results"])
        self.assertIn("apogee_altitude_m", configuration_data["altitude_inputs"])
        self.assertIsNone(configuration_data["altitude_inputs"]["apogee_altitude_m"])
        self.assertEqual(reloaded.to_dict(), project.to_dict())


if __name__ == "__main__":
    unittest.main()
