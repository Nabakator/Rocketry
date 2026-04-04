"""Recovery visualization-model tests for DRIFT."""

from __future__ import annotations

import unittest

from drift.services.analysis import analyze_configuration
from drift.services.visualization import build_recovery_visual_model

from tests.acceptance.fixtures import (
    catalogue_items,
    make_dual_configuration,
    make_single_configuration,
)


class VisualizationModelTests(unittest.TestCase):
    @staticmethod
    def _segment_slope(segment) -> float:
        return abs(
            (segment.start_altitude_m - segment.end_altitude_m)
            / (segment.end_x_fraction - segment.start_x_fraction)
        )

    def test_single_visual_model_contains_separate_ascent_and_sloped_descent(self) -> None:
        configuration = analyze_configuration(make_single_configuration(), catalogue_items())
        model = build_recovery_visual_model(configuration)

        marker_labels = [marker.label for marker in model.markers]
        timeline_labels = [event.label for event in model.timeline_events]
        segment_kinds = [segment.kind for segment in model.segments]
        segment_by_kind = {segment.kind: segment for segment in model.segments}

        self.assertIn("Apogee", marker_labels)
        self.assertIn("Single deployment", marker_labels)
        self.assertIn("Ground", marker_labels)
        self.assertEqual(segment_kinds, ["ascent", "transition", "single"])
        self.assertEqual(timeline_labels[0], "Recovery basis starts at apogee")
        self.assertEqual(timeline_labels[-1], "Landing")

        ascent = segment_by_kind["ascent"]
        single = segment_by_kind["single"]
        transition = segment_by_kind["transition"]

        self.assertLess(ascent.start_x_fraction, ascent.end_x_fraction)
        self.assertLess(ascent.end_x_fraction, single.start_x_fraction)
        self.assertLess(single.start_x_fraction, single.end_x_fraction)
        self.assertEqual(single.start_altitude_m, 400.0)
        self.assertEqual(transition.show_label, False)
        self.assertGreater(self._segment_slope(transition), self._segment_slope(single))

    def test_dual_visual_model_contains_distinct_drogue_and_main_paths(self) -> None:
        configuration = analyze_configuration(make_dual_configuration(), catalogue_items())
        model = build_recovery_visual_model(configuration)

        marker_labels = [marker.label for marker in model.markers]
        timeline_labels = [event.label for event in model.timeline_events]
        segment_kinds = [segment.kind for segment in model.segments]
        segment_by_kind = {segment.kind: segment for segment in model.segments}

        self.assertIn("Apogee", marker_labels)
        self.assertIn("Drogue deployment", marker_labels)
        self.assertIn("Main deployment", marker_labels)
        self.assertIn("Ground", marker_labels)
        self.assertEqual(segment_kinds, ["ascent", "transition", "drogue", "main"])
        self.assertEqual(timeline_labels[0], "Recovery basis starts at apogee")
        self.assertIn("Drogue deployment / drogue descent begins", timeline_labels)
        self.assertIn("Main deployment / main descent begins", timeline_labels)
        self.assertEqual(timeline_labels[-1], "Landing")

        ascent = segment_by_kind["ascent"]
        transition = segment_by_kind["transition"]
        drogue = segment_by_kind["drogue"]
        main = segment_by_kind["main"]

        self.assertLess(ascent.end_x_fraction, drogue.start_x_fraction)
        self.assertLess(drogue.start_x_fraction, drogue.end_x_fraction)
        self.assertLess(main.start_x_fraction, main.end_x_fraction)
        self.assertAlmostEqual(drogue.end_x_fraction, main.start_x_fraction, places=9)
        self.assertEqual(drogue.start_altitude_m, 2800.0)
        self.assertEqual(main.start_altitude_m, 500.0)

        freefall_slope = self._segment_slope(transition)
        drogue_slope = self._segment_slope(drogue)
        main_slope = self._segment_slope(main)

        self.assertGreater(freefall_slope, drogue_slope)
        self.assertLess(main_slope, drogue_slope)
