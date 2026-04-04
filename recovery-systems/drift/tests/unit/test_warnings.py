"""Warning engine tests for DRIFT."""

from __future__ import annotations

import unittest

from drift.models import (
    AltitudeInputs,
    AtmosphereSettings,
    CatalogueItem,
    Configuration,
    ParachuteSpec,
    WindSettings,
)
from drift.services.analysis import analyze_configuration


def make_catalogue_items() -> list[CatalogueItem]:
    return [
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
    ]


def make_single_configuration() -> Configuration:
    return Configuration(
        configuration_id="cfg_single",
        configuration_name="Single",
        recovery_mode="single",
        rocket_mass_kg=10.0,
        safety_margin_fraction=0.21,
        display_unit_system="si",
        atmosphere_settings=AtmosphereSettings(
            mode="manual_density",
            manual_density_kg_per_m3=1.2,
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
                parachute_id="single",
                role="single",
                family="hemispherical",
                cd=1.5,
                cd_source="preset",
                target_descent_velocity_mps=6.0,
            )
        ],
    )


def make_dual_configuration() -> Configuration:
    return Configuration(
        configuration_id="cfg_dual",
        configuration_name="Dual",
        recovery_mode="dual",
        rocket_mass_kg=18.0,
        safety_margin_fraction=0.2,
        display_unit_system="si",
        atmosphere_settings=AtmosphereSettings(
            mode="standard_atmosphere",
            manual_density_kg_per_m3=None,
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
                parachute_id="drogue",
                role="drogue",
                family="ribbon",
                cd=0.7,
                cd_source="preset",
                target_descent_velocity_mps=20.0,
            ),
            ParachuteSpec(
                parachute_id="main",
                role="main",
                family="hemispherical",
                cd=1.5,
                cd_source="preset",
                target_descent_velocity_mps=6.0,
            ),
        ],
    )


class WarningEngineTests(unittest.TestCase):
    def test_manual_density_override_warning_is_deterministic(self) -> None:
        analyzed = analyze_configuration(make_single_configuration(), make_catalogue_items())
        warnings = analyzed.warnings

        self.assertEqual(warnings[0].code, "MANUAL_DENSITY_OVERRIDE_ACTIVE")
        self.assertEqual(warnings[0].severity, "info")
        self.assertEqual(
            warnings[0].source_field,
            "atmosphere_settings.manual_density_kg_per_m3",
        )

    def test_manual_cd_override_warning_is_deterministic(self) -> None:
        configuration = make_single_configuration()
        configuration.parachutes[0].cd_source = "manual_override"

        analyzed = analyze_configuration(configuration, make_catalogue_items())
        codes = [warning.code for warning in analyzed.warnings]

        self.assertIn("MANUAL_CD_OVERRIDE_ACTIVE", codes)

    def test_catalogue_minimum_fallback_warning_triggers(self) -> None:
        configuration = make_single_configuration()
        configuration.safety_margin_fraction = 0.0
        configuration.parachutes[0].target_descent_velocity_mps = 20.0

        analyzed = analyze_configuration(configuration, make_catalogue_items())
        parachute = analyzed.parachutes[0]
        out_of_range_warnings = [
            warning for warning in analyzed.warnings if warning.code == "CATALOGUE_OUT_OF_RANGE"
        ]

        self.assertEqual(parachute.selected_catalogue_item_id, "hemi_1_8")
        self.assertEqual(len(out_of_range_warnings), 1)
        self.assertIn("below the available catalogue range", out_of_range_warnings[0].message)

    def test_catalogue_maximum_fallback_warning_triggers(self) -> None:
        configuration = make_single_configuration()
        configuration.rocket_mass_kg = 50.0
        configuration.parachutes[0].target_descent_velocity_mps = 4.0

        analyzed = analyze_configuration(configuration, make_catalogue_items())
        parachute = analyzed.parachutes[0]
        out_of_range_warnings = [
            warning for warning in analyzed.warnings if warning.code == "CATALOGUE_OUT_OF_RANGE"
        ]

        self.assertEqual(parachute.selected_catalogue_item_id, "hemi_3_0")
        self.assertEqual(len(out_of_range_warnings), 1)
        self.assertIn("above the available catalogue range", out_of_range_warnings[0].message)

    def test_main_descent_velocity_warning_triggers_only_above_threshold(self) -> None:
        low_configuration = make_dual_configuration()
        low_configuration.parachutes[1].target_descent_velocity_mps = 6.0
        low_analyzed = analyze_configuration(low_configuration, make_catalogue_items())
        self.assertNotIn(
            "MAIN_DESCENT_VELOCITY_HIGH",
            [warning.code for warning in low_analyzed.warnings],
        )

        high_configuration = make_dual_configuration()
        high_configuration.parachutes[1].target_descent_velocity_mps = 9.0
        high_analyzed = analyze_configuration(high_configuration, make_catalogue_items())
        self.assertIn(
            "MAIN_DESCENT_VELOCITY_HIGH",
            [warning.code for warning in high_analyzed.warnings],
        )

    def test_drogue_descent_velocity_warning_triggers_only_above_threshold(self) -> None:
        low_configuration = make_dual_configuration()
        low_configuration.parachutes[0].target_descent_velocity_mps = 20.0
        low_analyzed = analyze_configuration(low_configuration, make_catalogue_items())
        self.assertNotIn(
            "DROGUE_DESCENT_VELOCITY_HIGH",
            [warning.code for warning in low_analyzed.warnings],
        )

        high_configuration = make_dual_configuration()
        high_configuration.rocket_mass_kg = 25.0
        high_configuration.parachutes[0].target_descent_velocity_mps = 35.0
        high_analyzed = analyze_configuration(high_configuration, make_catalogue_items())
        self.assertIn(
            "DROGUE_DESCENT_VELOCITY_HIGH",
            [warning.code for warning in high_analyzed.warnings],
        )

    def test_high_drift_warning_triggers_only_above_threshold(self) -> None:
        high_drift = analyze_configuration(make_single_configuration(), make_catalogue_items())
        self.assertIn(
            "DRIFT_ESTIMATE_HIGH",
            [warning.code for warning in high_drift.warnings],
        )

        low_drift_configuration = make_single_configuration()
        low_drift_configuration.wind_settings.constant_wind_mps = 1.0
        low_drift = analyze_configuration(low_drift_configuration, make_catalogue_items())
        self.assertNotIn(
            "DRIFT_ESTIMATE_HIGH",
            [warning.code for warning in low_drift.warnings],
        )


if __name__ == "__main__":
    unittest.main()
