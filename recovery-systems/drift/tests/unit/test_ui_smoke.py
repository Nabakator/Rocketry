"""Light UI smoke checks for the DRIFT desktop shell."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtWidgets
    from drift import APP_WINDOW_NAME
    from drift.services.persistence import load_project
    from drift.ui import MainWindow

    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 is not installed in this environment.")
class MainWindowSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_project_name_is_used_for_default_file_stems(self) -> None:
        self.assertEqual(
            MainWindow._slugify_file_stem("Test project", fallback="untitled-project"),
            "test-project",
        )
        self.assertEqual(
            MainWindow._slugify_file_stem("  ", fallback="untitled-project"),
            "untitled-project",
        )

    def test_main_window_bootstraps_three_panel_shell(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)

        self.app.processEvents()
        self.assertEqual(window.main_splitter.count(), 3)
        self.assertIsNotNone(window.current_project())
        self.assertIsNotNone(window.current_configuration())
        self.assertEqual(window.windowTitle(), f"Untitled project - {APP_WINDOW_NAME}")
        self.assertEqual(window.top_bar.project_button.text(), "Untitled project")
        self.assertEqual(window.top_bar.state_badge.state_text(), "VALID")
        self.assertEqual(window.input_panel.objectName(), "leftPanel")
        self.assertEqual(window.results_panel.objectName(), "centrePanel")
        self.assertEqual(window.visuals_panel.objectName(), "rightPanel")
        self.assertIn("QWidget#leftPanel", self.app.styleSheet())
        self.assertIn("QWidget#topBar", self.app.styleSheet())

    def test_main_window_can_analyze_and_save_project(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)

        window.analyze_current_configuration()
        self.app.processEvents()
        current_configuration = window.current_configuration()
        self.assertIsNotNone(current_configuration)
        self.assertIsNotNone(current_configuration.analysis_results)
        self.assertEqual(window.top_bar.state_badge.state_text(), "ANALYSED")

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "drift-project.json"
            window.save_project_to_path(path)
            reloaded = load_project(path)

        self.assertEqual(reloaded.schema_version, "1.0.0")
        self.assertIsNotNone(reloaded.configurations[0].analysis_results)

    def test_top_bar_state_moves_to_draft_after_edit(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)

        window.analyze_current_configuration()
        self.app.processEvents()
        self.assertEqual(window.top_bar.state_badge.state_text(), "ANALYSED")

        window.input_panel.mass_spin.setValue(window.input_panel.mass_spin.value() + 1.0)
        self.app.processEvents()
        self.assertEqual(window.top_bar.state_badge.state_text(), "DRAFT")
        self.assertTrue(window.top_bar.reset_button.isEnabled())

    def test_results_and_visuals_remain_visible_while_draft_is_dirty(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)

        window.analyze_current_configuration()
        self.app.processEvents()

        analysed_total_time = window.results_panel.metric_cards["total_time"].value.text()
        analysed_phase_rows = window.results_panel.phase_table.rowCount()
        analysed_timeline_rows = len(window.visuals_panel.timeline_event_widgets)

        window.input_panel.mass_spin.setValue(window.input_panel.mass_spin.value() + 1.0)
        self.app.processEvents()

        self.assertEqual(window.top_bar.state_badge.state_text(), "DRAFT")
        self.assertEqual(
            window.results_panel.status_label.text(),
            "Draft edits are pending. Results below are from the last analysis.",
        )
        self.assertEqual(window.results_panel.metric_cards["total_time"].value.text(), analysed_total_time)
        self.assertEqual(window.results_panel.phase_table.rowCount(), analysed_phase_rows)
        self.assertGreater(analysed_phase_rows, 0)
        self.assertEqual(len(window.visuals_panel.timeline_event_widgets), analysed_timeline_rows)
        self.assertGreater(analysed_timeline_rows, 0)

    def test_left_panel_shows_configuration_tabs_and_deployment_helper(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)

        self.assertEqual(len(window.input_panel.configuration_tab_buttons), 1)
        self.assertEqual(
            window.input_panel.deployment_helper_label.text(),
            "Single parachute deploys at apogee. No staging.",
        )
        self.assertEqual(window.input_panel.altitude_stack.currentIndex(), 0)

        window.create_configuration()
        self.app.processEvents()
        self.assertEqual(len(window.input_panel.configuration_tab_buttons), 2)

        window.input_panel.dual_mode_button.click()
        self.app.processEvents()
        self.assertEqual(
            window.input_panel.deployment_helper_label.text(),
            "Drogue deploys at apogee, main deploys at a set altitude.",
        )
        self.assertEqual(window.input_panel.altitude_stack.currentIndex(), 1)

    def test_centre_panel_shows_results_tabs_and_metric_cards(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)

        self.assertEqual(window.results_panel.tab_widget.count(), 2)
        self.assertEqual(window.results_panel.tab_widget.tabText(0), "Results")
        self.assertEqual(window.results_panel.tab_widget.tabText(1), "Compare")
        self.assertEqual(
            window.results_panel.comparison_note.text(),
            "Create a second configuration to compare results.",
        )

        window.analyze_current_configuration()
        self.app.processEvents()

        self.assertIn("s", window.results_panel.metric_cards["total_time"].value.text())
        self.assertIn("m", window.results_panel.metric_cards["total_drift"].value.text())
        self.assertGreater(window.results_panel.phase_table.rowCount(), 0)

    def test_right_panel_shows_schematic_timeline_and_assumptions(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)

        self.assertEqual(len(window.visuals_panel.assumption_labels), 4)
        self.assertIn("Vertical descent only.", window.visuals_panel.assumption_labels[0].text())

        window.analyze_current_configuration()
        self.app.processEvents()

        self.assertEqual(window.visuals_panel.schematic_widget.objectName(), "recoverySchematicWidget")
        self.assertGreater(len(window.visuals_panel.timeline_event_widgets), 0)
        self.assertIn("Total descent time", window.visuals_panel.timeline_summary_label.text())
