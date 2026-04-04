"""Centre-panel analysis, warnings, and comparison views for DRIFT."""

from __future__ import annotations

from typing import Sequence

from PySide6 import QtCore, QtWidgets

from drift.formatting import format_length, format_time, format_velocity
from drift.models import CatalogueItem, Configuration, Project
from drift.services.comparison import build_comparison_rows
from drift.services.validation import ValidationIssue


class ResultsPanel(QtWidgets.QWidget):
    """Displays analysis outputs, validation issues, warnings, and comparison data."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._unit_system = "si"
        self._project: Project | None = None
        self._catalogue_by_id: dict[str, CatalogueItem] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        self.status_label = QtWidgets.QLabel("Analyze a configuration to populate results.")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        summary_box = QtWidgets.QGroupBox("Summary")
        summary_form = QtWidgets.QFormLayout(summary_box)
        self.basis_value = QtWidgets.QLabel("N/A")
        self.total_time_value = QtWidgets.QLabel("N/A")
        self.total_drift_value = QtWidgets.QLabel("N/A")
        summary_form.addRow("Basis", self.basis_value)
        summary_form.addRow("Total descent time", self.total_time_value)
        summary_form.addRow("Total drift", self.total_drift_value)
        layout.addWidget(summary_box)

        validation_box = QtWidgets.QGroupBox("Validation Issues")
        validation_layout = QtWidgets.QVBoxLayout(validation_box)
        self.validation_table = QtWidgets.QTableWidget(0, 3)
        self.validation_table.setHorizontalHeaderLabels(["Code", "Field", "Message"])
        self.validation_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.validation_table.verticalHeader().setVisible(False)
        self.validation_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        validation_layout.addWidget(self.validation_table)
        layout.addWidget(validation_box)

        parachute_box = QtWidgets.QGroupBox("Parachute Outputs")
        parachute_layout = QtWidgets.QVBoxLayout(parachute_box)
        self.parachute_table = QtWidgets.QTableWidget(0, 6)
        self.parachute_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.parachute_table.verticalHeader().setVisible(False)
        self.parachute_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        parachute_layout.addWidget(self.parachute_table)
        layout.addWidget(parachute_box)

        phase_box = QtWidgets.QGroupBox("Phase Summaries")
        phase_layout = QtWidgets.QVBoxLayout(phase_box)
        self.phase_table = QtWidgets.QTableWidget(0, 6)
        self.phase_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.phase_table.verticalHeader().setVisible(False)
        self.phase_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        phase_layout.addWidget(self.phase_table)
        layout.addWidget(phase_box)

        warnings_box = QtWidgets.QGroupBox("Warnings")
        warnings_layout = QtWidgets.QVBoxLayout(warnings_box)
        self.warning_table = QtWidgets.QTableWidget(0, 4)
        self.warning_table.setHorizontalHeaderLabels(["Code", "Severity", "Message", "Source"])
        self.warning_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.warning_table.verticalHeader().setVisible(False)
        self.warning_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        warnings_layout.addWidget(self.warning_table)
        layout.addWidget(warnings_box)

        comparison_box = QtWidgets.QGroupBox("Comparison")
        comparison_layout = QtWidgets.QVBoxLayout(comparison_box)
        compare_selectors = QtWidgets.QHBoxLayout()
        self.compare_a_combo = QtWidgets.QComboBox()
        self.compare_b_combo = QtWidgets.QComboBox()
        compare_selectors.addWidget(QtWidgets.QLabel("Configuration A"))
        compare_selectors.addWidget(self.compare_a_combo)
        compare_selectors.addWidget(QtWidgets.QLabel("Configuration B"))
        compare_selectors.addWidget(self.compare_b_combo)
        comparison_layout.addLayout(compare_selectors)
        self.comparison_note = QtWidgets.QLabel(
            "Add at least two saved configurations to compare them."
        )
        self.comparison_note.setWordWrap(True)
        comparison_layout.addWidget(self.comparison_note)
        self.comparison_table = QtWidgets.QTableWidget(0, 3)
        self.comparison_table.setHorizontalHeaderLabels(["Metric", "A", "B"])
        self.comparison_table.verticalHeader().setVisible(False)
        self.comparison_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.comparison_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        comparison_layout.addWidget(self.comparison_table)
        layout.addWidget(comparison_box)
        layout.addStretch(1)

        self.compare_a_combo.currentIndexChanged.connect(self._refresh_comparison)
        self.compare_b_combo.currentIndexChanged.connect(self._refresh_comparison)
        self._update_table_headers()

    def set_catalogue_items(self, catalogue_items: Sequence[CatalogueItem]) -> None:
        self._catalogue_by_id = {item.item_id: item for item in catalogue_items}

    def set_project(self, project: Project | None, *, unit_system: str) -> None:
        self._project = project
        self._unit_system = unit_system
        self._update_table_headers()
        self.compare_a_combo.blockSignals(True)
        self.compare_b_combo.blockSignals(True)
        self.compare_a_combo.clear()
        self.compare_b_combo.clear()
        if project is not None:
            for configuration in project.configurations:
                self.compare_a_combo.addItem(
                    configuration.configuration_name,
                    configuration.configuration_id,
                )
                self.compare_b_combo.addItem(
                    configuration.configuration_name,
                    configuration.configuration_id,
                )
            if self.compare_a_combo.count() >= 1:
                self.compare_a_combo.setCurrentIndex(0)
            if self.compare_b_combo.count() >= 2:
                self.compare_b_combo.setCurrentIndex(1)
            elif self.compare_b_combo.count() >= 1:
                self.compare_b_combo.setCurrentIndex(0)
        self.compare_a_combo.blockSignals(False)
        self.compare_b_combo.blockSignals(False)
        self._refresh_comparison()

    def show_configuration(
        self,
        configuration: Configuration | None,
        *,
        validation_issues: Sequence[ValidationIssue] | None = None,
        dirty: bool = False,
    ) -> None:
        if configuration is None:
            self._clear_all()
            self.status_label.setText("No configuration selected.")
            return

        self._unit_system = configuration.display_unit_system
        self._update_table_headers()
        self._populate_validation_issues(validation_issues or [])

        if validation_issues:
            self.status_label.setText(
                "Analysis blocked by validation issues. Fix the input state or save the draft."
            )
            self._clear_analysis_tables()
            return

        if dirty:
            self.status_label.setText(
                "Draft edits are pending. Run analysis to refresh engineering results."
            )
            self._clear_analysis_tables()
            return

        if configuration.analysis_results is None:
            self.status_label.setText(
                "This configuration is saved as a draft. Run analysis to populate results."
            )
            self._clear_analysis_tables()
            return

        self.status_label.setText("Analysis results loaded from the current configuration state.")
        self.basis_value.setText(configuration.analysis_results.recovery_basis_label)
        self.total_time_value.setText(format_time(configuration.analysis_results.total_descent_time_s))
        self.total_drift_value.setText(
            format_length(configuration.analysis_results.total_estimated_drift_m, self._unit_system)
        )

        self.parachute_table.setRowCount(len(configuration.parachutes))
        for row, parachute in enumerate(configuration.parachutes):
            self._set_table_item(self.parachute_table, row, 0, parachute.role)
            self._set_table_item(
                self.parachute_table,
                row,
                1,
                format_length(parachute.theoretical_diameter_m, self._unit_system),
            )
            self._set_table_item(
                self.parachute_table,
                row,
                2,
                format_length(parachute.recommended_diameter_m, self._unit_system),
            )
            selected_item = self._catalogue_by_id.get(parachute.selected_catalogue_item_id or "")
            self._set_table_item(
                self.parachute_table,
                row,
                3,
                selected_item.product_name if selected_item is not None else "N/A",
            )
            self._set_table_item(
                self.parachute_table,
                row,
                4,
                format_length(parachute.selected_nominal_diameter_m, self._unit_system),
            )
            self._set_table_item(
                self.parachute_table,
                row,
                5,
                format_velocity(parachute.resulting_descent_velocity_mps, self._unit_system),
            )

        phase_summaries = configuration.analysis_results.phase_summaries
        self.phase_table.setRowCount(len(phase_summaries))
        for row, phase in enumerate(phase_summaries):
            self._set_table_item(self.phase_table, row, 0, phase.phase_name)
            self._set_table_item(
                self.phase_table,
                row,
                1,
                format_length(phase.start_altitude_m, self._unit_system),
            )
            self._set_table_item(
                self.phase_table,
                row,
                2,
                format_length(phase.end_altitude_m, self._unit_system),
            )
            self._set_table_item(
                self.phase_table,
                row,
                3,
                format_velocity(phase.nominal_descent_velocity_mps, self._unit_system),
            )
            self._set_table_item(self.phase_table, row, 4, format_time(phase.estimated_duration_s))
            self._set_table_item(
                self.phase_table,
                row,
                5,
                format_length(phase.estimated_drift_m, self._unit_system),
            )

        self.warning_table.setRowCount(len(configuration.warnings))
        for row, warning in enumerate(configuration.warnings):
            self._set_table_item(self.warning_table, row, 0, warning.code)
            self._set_table_item(self.warning_table, row, 1, warning.severity)
            self._set_table_item(self.warning_table, row, 2, warning.message)
            self._set_table_item(self.warning_table, row, 3, warning.source_field or "N/A")

    def _populate_validation_issues(self, issues: Sequence[ValidationIssue]) -> None:
        self.validation_table.setRowCount(len(issues))
        for row, issue in enumerate(issues):
            self._set_table_item(self.validation_table, row, 0, issue.code)
            self._set_table_item(self.validation_table, row, 1, issue.field_path)
            self._set_table_item(self.validation_table, row, 2, issue.message)

    def _clear_all(self) -> None:
        self._populate_validation_issues([])
        self._clear_analysis_tables()

    def _clear_analysis_tables(self) -> None:
        self.basis_value.setText("N/A")
        self.total_time_value.setText("N/A")
        self.total_drift_value.setText("N/A")
        self.parachute_table.setRowCount(0)
        self.phase_table.setRowCount(0)
        self.warning_table.setRowCount(0)

    def _update_table_headers(self) -> None:
        length_unit = "ft" if self._unit_system == "imperial" else "m"
        velocity_unit = "ft/s" if self._unit_system == "imperial" else "m/s"
        self.parachute_table.setHorizontalHeaderLabels(
            [
                "Role",
                f"Theoretical D [{length_unit}]",
                f"Recommended D [{length_unit}]",
                "Catalogue Item",
                f"Selected D [{length_unit}]",
                f"Resulting V [{velocity_unit}]",
            ]
        )
        self.phase_table.setHorizontalHeaderLabels(
            [
                "Phase",
                f"Start [{length_unit}]",
                f"End [{length_unit}]",
                f"Velocity [{velocity_unit}]",
                "Duration [s]",
                f"Drift [{length_unit}]",
            ]
        )

    def _refresh_comparison(self) -> None:
        project = self._project
        if project is None or len(project.configurations) < 2:
            self.comparison_note.setVisible(True)
            self.comparison_table.setRowCount(0)
            return

        config_a = self._find_configuration(self.compare_a_combo.currentData())
        config_b = self._find_configuration(self.compare_b_combo.currentData())
        if config_a is None or config_b is None:
            self.comparison_note.setVisible(True)
            self.comparison_table.setRowCount(0)
            return

        self.comparison_note.setVisible(False)
        rows = build_comparison_rows(
            config_a,
            config_b,
            tuple(self._catalogue_by_id.values()),
            unit_system=self._unit_system,
        )
        self.comparison_table.setRowCount(len(rows))
        for row, comparison_row in enumerate(rows):
            self._set_table_item(self.comparison_table, row, 0, comparison_row.metric)
            self._set_table_item(self.comparison_table, row, 1, comparison_row.value_a)
            self._set_table_item(self.comparison_table, row, 2, comparison_row.value_b)

    def _find_configuration(self, configuration_id: str | None) -> Configuration | None:
        if self._project is None or configuration_id is None:
            return None
        for configuration in self._project.configurations:
            if configuration.configuration_id == configuration_id:
                return configuration
        return None

    def _set_table_item(
        self,
        table: QtWidgets.QTableWidget,
        row: int,
        column: int,
        text: str,
    ) -> None:
        item = QtWidgets.QTableWidgetItem(text)
        item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        table.setItem(row, column, item)
