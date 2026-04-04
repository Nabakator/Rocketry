"""Comparison service tests for DRIFT."""

from __future__ import annotations

import unittest

from drift.services.analysis import analyze_configuration
from drift.services.comparison import build_comparison_rows

from tests.acceptance.fixtures import (
    catalogue_items,
    make_dual_configuration,
    make_single_configuration,
)


class ComparisonServiceTests(unittest.TestCase):
    def test_comparison_rows_cover_required_fields(self) -> None:
        single = analyze_configuration(make_single_configuration(), catalogue_items())
        dual = analyze_configuration(make_dual_configuration(), catalogue_items())

        rows = build_comparison_rows(
            single,
            dual,
            catalogue_items(),
            unit_system="si",
        )
        metrics = [row.metric for row in rows]

        self.assertEqual(
            metrics,
            [
                "Recovery mode",
                "Parachute family",
                "Theoretical diameter",
                "Recommended diameter",
                "Selected catalogue item",
                "Selected nominal diameter",
                "Resulting descent velocity",
                "Total descent time",
                "Total estimated drift",
                "Warnings",
            ],
        )
        family_row = rows[1]
        self.assertIn("single: hemispherical", family_row.value_a)
        self.assertIn("drogue: ribbon", family_row.value_b)
        self.assertIn("main: hemispherical", family_row.value_b)

    def test_comparison_rows_mark_draft_configurations_clearly(self) -> None:
        analyzed = analyze_configuration(make_single_configuration(), catalogue_items())
        draft = make_single_configuration(configuration_id="cfg_draft", configuration_name="Draft")

        rows = build_comparison_rows(analyzed, draft, catalogue_items(), unit_system="si")
        total_time_row = next(row for row in rows if row.metric == "Total descent time")
        warnings_row = next(row for row in rows if row.metric == "Warnings")

        self.assertEqual(total_time_row.value_b, "Draft / not analyzed")
        self.assertEqual(warnings_row.value_b, "None")
