"""Engineering core and analysis service tests for DRIFT."""

from __future__ import annotations

import math
import unittest

from drift.core.atmosphere import isa_density_kg_per_m3, resolve_density_kg_per_m3
from drift.models import (
    AltitudeInputs,
    AtmosphereSettings,
    CatalogueItem,
    Configuration,
    ParachuteSpec,
    WindSettings,
)
from drift.services.analysis import AnalysisError, analyze_configuration, match_catalogue_item

G0 = 9.80665
PI = math.pi


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
            mode="manual_density",
            manual_density_kg_per_m3=1.2,
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


def theoretical_diameter(mass_kg: float, density: float, cd: float, velocity: float) -> float:
    area = 2.0 * G0 * mass_kg / (density * cd * velocity * velocity)
    return math.sqrt((4.0 * area) / PI)


def resulting_velocity(mass_kg: float, density: float, cd: float, diameter_m: float) -> float:
    area = PI * diameter_m * diameter_m / 4.0
    return math.sqrt(2.0 * G0 * mass_kg / (density * cd * area))


class CoreAndAnalysisTests(unittest.TestCase):
    def test_isa_density_and_manual_override(self) -> None:
        sea_level_density = isa_density_kg_per_m3(0.0)
        density_at_1000 = isa_density_kg_per_m3(1000.0)

        self.assertAlmostEqual(sea_level_density, 1.225, places=3)
        self.assertLess(density_at_1000, sea_level_density)
        self.assertEqual(resolve_density_kg_per_m3(2000.0, 1.05), 1.05)

    def test_catalogue_matching_policy(self) -> None:
        items = make_catalogue_items()

        self.assertEqual(
            match_catalogue_item("hemispherical", 1.95, items).nominal_diameter_m,
            2.0,
        )
        self.assertEqual(
            match_catalogue_item("hemispherical", 0.75, items).nominal_diameter_m,
            1.8,
        )
        self.assertEqual(
            match_catalogue_item("hemispherical", 4.0, items).nominal_diameter_m,
            3.0,
        )

    def test_single_analysis_constant_wind_populates_results(self) -> None:
        configuration = make_single_configuration()
        analyzed = analyze_configuration(configuration, make_catalogue_items())
        parachute = analyzed.parachutes[0]

        expected_theoretical = theoretical_diameter(10.0, 1.2, 1.5, 6.0)
        expected_recommended = expected_theoretical * math.sqrt(1.21)
        expected_velocity = resulting_velocity(10.0, 1.2, 1.5, 2.2)
        expected_duration = 1200.0 / expected_velocity
        expected_drift = expected_duration * 5.0

        self.assertAlmostEqual(parachute.theoretical_diameter_m, expected_theoretical, places=9)
        self.assertAlmostEqual(parachute.recommended_diameter_m, expected_recommended, places=9)
        self.assertEqual(parachute.selected_catalogue_item_id, "hemi_2_2")
        self.assertAlmostEqual(parachute.selected_nominal_diameter_m, 2.2, places=9)
        self.assertAlmostEqual(parachute.resulting_descent_velocity_mps, expected_velocity, places=9)

        result = analyzed.analysis_results
        self.assertIsNotNone(result)
        self.assertEqual(result.recovery_basis_label, "from_apogee")
        self.assertEqual(len(result.phase_summaries), 1)
        self.assertAlmostEqual(result.total_descent_time_s, expected_duration, places=9)
        self.assertAlmostEqual(result.total_estimated_drift_m, expected_drift, places=9)
        self.assertEqual(result.display_metrics["sizing_available"], True)

    def test_single_analysis_two_layer_drift_splits_above_and_below_deployment(self) -> None:
        configuration = make_single_configuration()
        configuration.wind_settings = WindSettings(
            mode="two_layer",
            aloft_wind_mps=10.0,
            ground_wind_mps=4.0,
        )

        analyzed = analyze_configuration(configuration, make_catalogue_items())
        velocity = analyzed.parachutes[0].resulting_descent_velocity_mps
        self.assertIsNotNone(velocity)
        expected_drift = ((1200.0 - 500.0) / velocity * 10.0) + (500.0 / velocity * 4.0)

        self.assertAlmostEqual(
            analyzed.analysis_results.total_estimated_drift_m,
            expected_drift,
            places=9,
        )
        self.assertEqual(len(analyzed.analysis_results.phase_summaries), 1)

    def test_dual_analysis_two_layer_populates_phase_summaries(self) -> None:
        analyzed = analyze_configuration(make_dual_configuration(), make_catalogue_items())
        result = analyzed.analysis_results
        self.assertIsNotNone(result)
        self.assertEqual(result.recovery_basis_label, "from_apogee")
        self.assertEqual(len(result.phase_summaries), 2)

        drogue = next(parachute for parachute in analyzed.parachutes if parachute.role == "drogue")
        main = next(parachute for parachute in analyzed.parachutes if parachute.role == "main")

        expected_drogue_velocity = resulting_velocity(18.0, 1.2, 0.7, 1.5)
        expected_main_velocity = resulting_velocity(18.0, 1.2, 1.5, 3.0)
        expected_drogue_duration = (3200.0 - 500.0) / expected_drogue_velocity
        expected_main_duration = 500.0 / expected_main_velocity
        expected_drogue_drift = expected_drogue_duration * 12.0
        expected_main_drift = expected_main_duration * 4.0

        self.assertEqual(drogue.selected_catalogue_item_id, "ribbon_1_5")
        self.assertEqual(main.selected_catalogue_item_id, "hemi_3_0")
        self.assertAlmostEqual(drogue.resulting_descent_velocity_mps, expected_drogue_velocity, places=9)
        self.assertAlmostEqual(main.resulting_descent_velocity_mps, expected_main_velocity, places=9)
        self.assertAlmostEqual(result.phase_summaries[0].estimated_duration_s, expected_drogue_duration, places=9)
        self.assertAlmostEqual(result.phase_summaries[0].estimated_drift_m, expected_drogue_drift, places=9)
        self.assertAlmostEqual(result.phase_summaries[1].estimated_duration_s, expected_main_duration, places=9)
        self.assertAlmostEqual(result.phase_summaries[1].estimated_drift_m, expected_main_drift, places=9)
        self.assertAlmostEqual(
            result.total_descent_time_s,
            expected_drogue_duration + expected_main_duration,
            places=9,
        )
        self.assertAlmostEqual(
            result.total_estimated_drift_m,
            expected_drogue_drift + expected_main_drift,
            places=9,
        )

    def test_analysis_rejects_invalid_configuration(self) -> None:
        configuration = make_single_configuration()
        configuration.altitude_inputs.deployment_altitude_m = None

        with self.assertRaises(AnalysisError):
            analyze_configuration(configuration, make_catalogue_items())


if __name__ == "__main__":
    unittest.main()
