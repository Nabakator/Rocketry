"""Right-panel recovery schematic and timeline rendering for DRIFT."""

from __future__ import annotations

from typing import Sequence

from PySide6 import QtWidgets

from drift.formatting import format_length, format_time
from drift.models import Configuration
from drift.services.validation import ValidationIssue
from drift.services.visualization import build_recovery_visual_model
from drift.ui.theme import configure_box_layout

from .schematic_widget import RecoverySchematicWidget


class VisualsPanel(QtWidgets.QWidget):
    """Recovery schematic and timeline widgets wired to analysed model state."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        configure_box_layout(layout)

        schematic_box = QtWidgets.QGroupBox("Recovery Schematic")
        schematic_layout = QtWidgets.QVBoxLayout(schematic_box)
        configure_box_layout(schematic_layout)
        self.schematic_widget = RecoverySchematicWidget()
        schematic_layout.addWidget(self.schematic_widget)
        layout.addWidget(schematic_box)

        timeline_box = QtWidgets.QGroupBox("Event Timeline")
        timeline_layout = QtWidgets.QVBoxLayout(timeline_box)
        configure_box_layout(timeline_layout)
        self.timeline_table = QtWidgets.QTableWidget(0, 4)
        self.timeline_table.setHorizontalHeaderLabels(["Time", "Event", "Altitude", "Notes"])
        self.timeline_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.timeline_table.verticalHeader().setVisible(False)
        self.timeline_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        timeline_layout.addWidget(self.timeline_table)
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
            self.schematic_widget.show_message("Select or create a configuration to begin.")
            self._set_timeline_message("Analyse a configuration to populate this area.")
            return

        unit_system = configuration.display_unit_system
        if issues:
            self.schematic_widget.show_message(
                "Analysis is blocked by validation issues. Fix the input state before generating visuals."
            )
            self._set_timeline_message(f"Validation issue count: {len(issues)}")
            return

        if dirty:
            self.schematic_widget.show_message(
                "Draft edits are pending. Re-run analysis to refresh this view."
            )
            self._set_timeline_message("Draft edits are pending.")
            return

        if configuration.analysis_results is None:
            self.schematic_widget.show_message("This configuration is saved as a draft.")
            self._set_timeline_message("Run analysis to populate the event sequence.")
            return

        visual_model = build_recovery_visual_model(configuration)
        self.schematic_widget.set_visual_model(visual_model, unit_system=unit_system)
        self.timeline_table.setRowCount(len(visual_model.timeline_events) + 1)
        for row, event in enumerate(visual_model.timeline_events):
            self._set_item(
                row,
                0,
                "N/A" if event.time_s is None else f"T+{event.time_s:.2f} s",
            )
            self._set_item(row, 1, event.label)
            self._set_item(row, 2, format_length(event.altitude_m, unit_system))
            self._set_item(row, 3, event.notes or "")

        total_row = len(visual_model.timeline_events)
        self._set_item(total_row, 0, "")
        self._set_item(total_row, 1, "Total descent time")
        self._set_item(total_row, 2, "")
        self._set_item(
            total_row,
            3,
            format_time(configuration.analysis_results.total_descent_time_s),
        )

    def _set_timeline_message(self, message: str) -> None:
        self.timeline_table.setRowCount(1)
        self._set_item(0, 0, "")
        self._set_item(0, 1, message)
        self._set_item(0, 2, "")
        self._set_item(0, 3, "")

    def _set_item(self, row: int, column: int, text: str) -> None:
        self.timeline_table.setItem(row, column, QtWidgets.QTableWidgetItem(text))


__all__ = ["VisualsPanel"]
