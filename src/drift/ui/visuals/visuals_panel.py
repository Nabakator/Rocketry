"""Right-panel recovery schematic and timeline placeholders for DRIFT."""

from __future__ import annotations

from typing import Sequence

from PySide6 import QtWidgets

from drift.models import Configuration
from drift.services.validation import ValidationIssue
from drift.ui.display_units import format_length, format_time


class VisualsPanel(QtWidgets.QWidget):
    """Textual placeholder visuals wired to the analyzed model state."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        schematic_box = QtWidgets.QGroupBox("Recovery Schematic")
        schematic_layout = QtWidgets.QVBoxLayout(schematic_box)
        self.schematic_text = QtWidgets.QPlainTextEdit()
        self.schematic_text.setReadOnly(True)
        schematic_layout.addWidget(self.schematic_text)
        layout.addWidget(schematic_box)

        timeline_box = QtWidgets.QGroupBox("Event Timeline")
        timeline_layout = QtWidgets.QVBoxLayout(timeline_box)
        self.timeline_text = QtWidgets.QPlainTextEdit()
        self.timeline_text.setReadOnly(True)
        timeline_layout.addWidget(self.timeline_text)
        layout.addWidget(timeline_box)
        layout.addStretch(1)

        self.show_configuration(None)

    def show_configuration(
        self,
        configuration: Configuration | None,
        *,
        validation_issues: Sequence[ValidationIssue] | None = None,
        dirty: bool = False,
    ) -> None:
        issues = list(validation_issues or [])
        if configuration is None:
            self.schematic_text.setPlainText(
                "Recovery schematic placeholder.\n\nSelect or create a configuration to begin."
            )
            self.timeline_text.setPlainText(
                "Timeline placeholder.\n\nAnalyze a configuration to populate this area."
            )
            return

        unit_system = configuration.display_unit_system
        if issues:
            self.schematic_text.setPlainText(
                "Recovery schematic placeholder.\n\n"
                "Analysis is blocked by validation issues. Fix the input state before generating visuals."
            )
            self.timeline_text.setPlainText(
                "Timeline placeholder.\n\n"
                f"Validation issue count: {len(issues)}"
            )
            return

        if dirty:
            self.schematic_text.setPlainText(
                "Recovery schematic placeholder.\n\nDraft edits are pending. Re-run analysis to refresh this view."
            )
            self.timeline_text.setPlainText(
                "Timeline placeholder.\n\nDraft edits are pending."
            )
            return

        if configuration.analysis_results is None:
            self.schematic_text.setPlainText(
                "Recovery schematic placeholder.\n\nThis configuration is saved as a draft."
            )
            self.timeline_text.setPlainText(
                "Timeline placeholder.\n\nRun analysis to populate the event sequence."
            )
            return

        schematic_lines = [
            "Recovery schematic placeholder",
            "",
            f"Basis: {configuration.analysis_results.recovery_basis_label}",
            f"Mode: {configuration.recovery_mode}",
            "",
            "Phase sequence:",
        ]
        for phase in configuration.analysis_results.phase_summaries:
            schematic_lines.append(
                f"- {phase.phase_name}: {format_length(phase.start_altitude_m, unit_system)}"
                f" -> {format_length(phase.end_altitude_m, unit_system)}"
                f" under {phase.parachute_id}"
            )
        self.schematic_text.setPlainText("\n".join(schematic_lines))

        timeline_lines = [
            "Timeline placeholder",
            "",
        ]
        elapsed_s = 0.0
        for phase in configuration.analysis_results.phase_summaries:
            timeline_lines.append(
                f"T+{elapsed_s:.2f} s: start {phase.phase_name}"
                f" at {format_length(phase.start_altitude_m, unit_system)}"
            )
            elapsed_s += phase.estimated_duration_s or 0.0
            timeline_lines.append(
                f"T+{elapsed_s:.2f} s: end {phase.phase_name}"
                f" at {format_length(phase.end_altitude_m, unit_system)}"
            )
        timeline_lines.append("")
        timeline_lines.append(f"Total descent time: {format_time(configuration.analysis_results.total_descent_time_s)}")
        self.timeline_text.setPlainText("\n".join(timeline_lines))
