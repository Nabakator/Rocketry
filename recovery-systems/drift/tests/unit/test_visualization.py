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
    def test_single_visual_model_contains_apogee_deployment_and_landing(self) -> None:
        configuration = analyze_configuration(make_single_configuration(), catalogue_items())
        model = build_recovery_visual_model(configuration)

        marker_labels = [marker.label for marker in model.markers]
        timeline_labels = [event.label for event in model.timeline_events]

        self.assertIn("Apogee", marker_labels)
        self.assertIn("Single deployment", marker_labels)
        self.assertEqual(model.segments[0].kind, "ascent")
        self.assertEqual(model.segments[1].kind, "single")
        self.assertEqual(timeline_labels[0], "Recovery basis starts at apogee")
        self.assertEqual(timeline_labels[-1], "Landing")

    def test_dual_visual_model_contains_drogue_and_main_structure(self) -> None:
        configuration = analyze_configuration(make_dual_configuration(), catalogue_items())
        model = build_recovery_visual_model(configuration)

        marker_labels = [marker.label for marker in model.markers]
        timeline_labels = [event.label for event in model.timeline_events]
        segment_kinds = [segment.kind for segment in model.segments]

        self.assertIn("Apogee", marker_labels)
        self.assertIn("Drogue deployment", marker_labels)
        self.assertIn("Main deployment", marker_labels)
        self.assertEqual(segment_kinds, ["ascent", "drogue", "main"])
        self.assertEqual(timeline_labels[0], "Recovery basis starts at apogee")
        self.assertIn("Drogue deployment / drogue descent begins", timeline_labels)
        self.assertIn("Main deployment / main descent begins", timeline_labels)
        self.assertEqual(timeline_labels[-1], "Landing")
