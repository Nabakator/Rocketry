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

    def test_main_window_bootstraps_three_panel_shell(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)

        self.assertEqual(window.main_splitter.count(), 3)
        self.assertIsNotNone(window.current_project())
        self.assertIsNotNone(window.current_configuration())
        self.assertEqual(window.windowTitle(), f"Untitled Project - {APP_WINDOW_NAME}")

    def test_main_window_can_analyze_and_save_project(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)

        window.analyze_current_configuration()
        current_configuration = window.current_configuration()
        self.assertIsNotNone(current_configuration)
        self.assertIsNotNone(current_configuration.analysis_results)

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "drift-project.json"
            window.save_project_to_path(path)
            reloaded = load_project(path)

        self.assertEqual(reloaded.schema_version, "1.0.0")
        self.assertIsNotNone(reloaded.configurations[0].analysis_results)
