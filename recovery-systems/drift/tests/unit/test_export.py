"""Markdown export tests for DRIFT."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from drift.services.analysis import analyze_configuration
from drift.services.export import render_configuration_markdown, save_configuration_markdown

from tests.acceptance.fixtures import catalogue_items, make_single_configuration


class MarkdownExportTests(unittest.TestCase):
    def test_markdown_export_contains_required_sections(self) -> None:
        configuration = analyze_configuration(make_single_configuration(), catalogue_items())

        markdown = render_configuration_markdown(
            project_name="Export Project",
            configuration=configuration,
            catalogue_items=catalogue_items(),
        )

        self.assertIn("# Export Project", markdown)
        self.assertIn("## Configuration", markdown)
        self.assertIn("## Assumptions", markdown)
        self.assertIn("## Parachutes", markdown)
        self.assertIn("## Phase Summaries", markdown)
        self.assertIn("## Totals", markdown)
        self.assertIn("## Warnings", markdown)
        self.assertIn("Basis label: from_apogee", markdown)
        self.assertIn("Atmosphere mode: standard_atmosphere", markdown)
        self.assertIn("single | hemispherical | 1.500 | preset", markdown)

    def test_markdown_export_is_deterministic_and_saves_md_files(self) -> None:
        configuration = analyze_configuration(make_single_configuration(), catalogue_items())
        first = render_configuration_markdown(
            project_name="Export Project",
            configuration=configuration,
            catalogue_items=catalogue_items(),
        )
        second = render_configuration_markdown(
            project_name="Export Project",
            configuration=configuration,
            catalogue_items=catalogue_items(),
        )

        self.assertEqual(first, second)

        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "summary"
            saved = save_configuration_markdown(
                project_name="Export Project",
                configuration=configuration,
                catalogue_items=catalogue_items(),
                path=target,
            )

            self.assertEqual(saved.suffix, ".md")
            self.assertEqual(saved.read_text(encoding="utf-8"), first)
