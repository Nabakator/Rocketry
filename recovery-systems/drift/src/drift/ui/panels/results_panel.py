"""Centre-panel analysis, warnings, and comparison views for DRIFT."""

from __future__ import annotations

from typing import Sequence

from PySide6 import QtCore, QtGui, QtWidgets

from drift.formatting import format_length, format_time, format_velocity
from drift.models import CatalogueItem, Configuration, Project, Warning
from drift.services.comparison import build_comparison_rows
from drift.services.validation import ValidationIssue
from drift.ui.theme import Colours, SPACING, configure_box_layout, configure_grid_layout


def _refresh_style(widget: QtWidgets.QWidget) -> None:
    """Re-apply QSS when a dynamic property changes."""

    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def _phase_colour_key(name: str) -> str:
    lowered = name.casefold()
    if lowered == "drogue":
        return "drogue"
    if lowered in {"main", "single"}:
        return "main"
    if lowered == "freefall":
        return "freefall"
    return "ascent"


def _phase_colour(name: str) -> QtGui.QColor:
    mapping = {
        "ascent": Colours.PHASE_ASCENT,
        "freefall": Colours.PHASE_FREEFALL,
        "drogue": Colours.PHASE_DROGUE,
        "main": Colours.PHASE_MAIN,
    }
    return QtGui.QColor(mapping.get(_phase_colour_key(name), Colours.FOREGROUND))


def _humanise_identifier(value: str) -> str:
    return value.replace("_", " ").strip().title()


class MetricCard(QtWidgets.QFrame):
    """Compact engineering card for one headline metric."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("resultCard")

        layout = QtWidgets.QVBoxLayout(self)
        configure_box_layout(layout, margins=(SPACING.md, SPACING.md, SPACING.md, SPACING.md))
        layout.setSpacing(SPACING.xs)

        self.label = QtWidgets.QLabel()
        self.label.setObjectName("metricCardLabel")
        layout.addWidget(self.label)

        self.value = QtWidgets.QLabel("N/A")
        self.value.setObjectName("metricCardValue")
        self.value.setProperty("role", "metricValue")
        layout.addWidget(self.value)

        self.sublabel = QtWidgets.QLabel()
        self.sublabel.setObjectName("metricCardSubLabel")
        self.sublabel.setWordWrap(True)
        layout.addWidget(self.sublabel)

        layout.addStretch(1)

    def set_metric(
        self,
        *,
        label: str,
        value: str,
        sublabel: str,
        alert: bool = False,
    ) -> None:
        self.label.setText(label)
        self.value.setText(value)
        self.sublabel.setText(sublabel)
        self.setProperty("alert", alert)
        _refresh_style(self)


class IssueCard(QtWidgets.QFrame):
    """Severity-coded card for warnings and validation issues."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("warningCard")

        layout = QtWidgets.QVBoxLayout(self)
        configure_box_layout(layout, margins=(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm))
        layout.setSpacing(SPACING.xs)

        header_row = QtWidgets.QHBoxLayout()
        header_row.setSpacing(SPACING.sm)
        layout.addLayout(header_row)

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setObjectName("warningCardIcon")
        header_row.addWidget(self.icon_label, 0, QtCore.Qt.AlignTop)

        text_column = QtWidgets.QVBoxLayout()
        text_column.setSpacing(2)
        header_row.addLayout(text_column, 1)

        self.title_label = QtWidgets.QLabel()
        self.title_label.setObjectName("warningCardTitle")
        text_column.addWidget(self.title_label)

        self.message_label = QtWidgets.QLabel()
        self.message_label.setObjectName("warningCardMessage")
        self.message_label.setWordWrap(True)
        text_column.addWidget(self.message_label)

        self.meta_label = QtWidgets.QLabel()
        self.meta_label.setObjectName("warningCardMeta")
        self.meta_label.setProperty("role", "helper")
        self.meta_label.setWordWrap(True)
        text_column.addWidget(self.meta_label)

    def set_issue(
        self,
        *,
        severity: str,
        title: str,
        message: str,
        meta: str,
    ) -> None:
        icon = {"error": "⚠", "warning": "⚠", "info": "ℹ"}.get(severity, "•")
        self.icon_label.setText(icon)
        self.title_label.setText(title)
        self.message_label.setText(message)
        self.meta_label.setText(meta)
        self.meta_label.setVisible(bool(meta))
        self.setProperty("severity", severity)
        _refresh_style(self)


class ParachuteSummaryCard(QtWidgets.QFrame):
    """Summary block for one parachute role."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("summaryCard")

        layout = QtWidgets.QVBoxLayout(self)
        configure_box_layout(layout, margins=(SPACING.md, SPACING.md, SPACING.md, SPACING.md))
        layout.setSpacing(SPACING.sm)

        header_row = QtWidgets.QHBoxLayout()
        header_row.setSpacing(SPACING.sm)
        layout.addLayout(header_row)

        self.phase_dot = QtWidgets.QLabel("●")
        self.phase_dot.setObjectName("summaryPhaseDot")
        header_row.addWidget(self.phase_dot, 0, QtCore.Qt.AlignVCenter)

        title_column = QtWidgets.QVBoxLayout()
        title_column.setSpacing(2)
        header_row.addLayout(title_column, 1)

        self.title_label = QtWidgets.QLabel()
        self.title_label.setObjectName("summaryCardTitle")
        title_column.addWidget(self.title_label)

        self.subtitle_label = QtWidgets.QLabel()
        self.subtitle_label.setObjectName("summaryCardSubLabel")
        self.subtitle_label.setProperty("role", "helper")
        title_column.addWidget(self.subtitle_label)

        self.data_layout = QtWidgets.QGridLayout()
        configure_grid_layout(self.data_layout, margins=(0, SPACING.sm, 0, 0))
        self.data_layout.setColumnStretch(0, 0)
        self.data_layout.setColumnStretch(1, 1)
        layout.addLayout(self.data_layout)

        self._value_labels: dict[str, QtWidgets.QLabel] = {}
        for row, label in enumerate(
            (
                "Cd",
                "Target descent rate",
                "Theoretical diameter",
                "Recommended diameter",
                "Selected catalogue item",
                "Selected nominal diameter",
                "Resulting descent rate",
            )
        ):
            key = label.casefold()
            field_label = QtWidgets.QLabel(label)
            field_label.setObjectName("summaryFieldLabel")
            value_label = QtWidgets.QLabel("N/A")
            value_label.setObjectName("summaryFieldValue")
            value_label.setProperty("role", "mono")
            value_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.data_layout.addWidget(field_label, row, 0)
            self.data_layout.addWidget(value_label, row, 1, 1, 1, QtCore.Qt.AlignRight)
            self._value_labels[key] = value_label

    def set_parachute(
        self,
        *,
        role: str,
        family: str,
        cd: float,
        target_velocity: str,
        theoretical_diameter: str,
        recommended_diameter: str,
        selected_item: str,
        selected_diameter: str,
        resulting_velocity: str,
    ) -> None:
        role_key = _phase_colour_key(role)
        self.phase_dot.setProperty("phase", role_key)
        self.title_label.setText(_humanise_identifier(role))
        self.subtitle_label.setText(_humanise_identifier(family))
        self._value_labels["cd"].setText(f"{cd:.3f}")
        self._value_labels["target descent rate"].setText(target_velocity)
        self._value_labels["theoretical diameter"].setText(theoretical_diameter)
        self._value_labels["recommended diameter"].setText(recommended_diameter)
        self._value_labels["selected catalogue item"].setText(selected_item)
        self._value_labels["selected nominal diameter"].setText(selected_diameter)
        self._value_labels["resulting descent rate"].setText(resulting_velocity)
        _refresh_style(self.phase_dot)


class ResultsPanel(QtWidgets.QWidget):
    """Displays analysis outputs, warnings, and comparison data."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._unit_system = "si"
        self._project: Project | None = None
        self._catalogue_by_id: dict[str, CatalogueItem] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        configure_box_layout(layout, margins=(0, 0, 0, 0), spacing=0)

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setObjectName("centreTabs")
        layout.addWidget(self.tab_widget, 1)

        self._build_results_tab()
        self._build_compare_tab()
        self._update_table_headers()

    def _build_results_tab(self) -> None:
        tab = QtWidgets.QWidget()
        tab_layout = QtWidgets.QVBoxLayout(tab)
        configure_box_layout(tab_layout, margins=(0, 0, 0, 0), spacing=0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        tab_layout.addWidget(scroll)

        content = QtWidgets.QWidget()
        scroll.setWidget(content)

        content_layout = QtWidgets.QVBoxLayout(content)
        configure_box_layout(content_layout, margins=(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg))
        content_layout.setSpacing(SPACING.md)

        self.status_label = QtWidgets.QLabel("Analyse the current configuration to populate the results.")
        self.status_label.setObjectName("statusBanner")
        self.status_label.setWordWrap(True)
        content_layout.addWidget(self.status_label)

        self.basis_label = QtWidgets.QLabel("Basis: N/A")
        self.basis_label.setObjectName("basisLabel")
        self.basis_label.setProperty("role", "helper")
        content_layout.addWidget(self.basis_label)

        self.warning_section, warning_body = self._create_section("Validation and warnings")
        self.warning_cards_layout = QtWidgets.QVBoxLayout()
        self.warning_cards_layout.setSpacing(SPACING.sm)
        warning_body.addLayout(self.warning_cards_layout)
        self.warning_empty_label = self._create_empty_state_label(
            "No validation issues or engineering warnings."
        )
        warning_body.addWidget(self.warning_empty_label)
        content_layout.addWidget(self.warning_section)

        self.metrics_section, metrics_body = self._create_section("Key metrics")
        self.metrics_grid = QtWidgets.QGridLayout()
        configure_grid_layout(self.metrics_grid, margins=(0, 0, 0, 0))
        metrics_body.addLayout(self.metrics_grid)
        self.metric_cards = {
            "total_time": MetricCard(),
            "total_drift": MetricCard(),
            "landing_rate": MetricCard(),
            "drogue_rate": MetricCard(),
        }
        positions = (("total_time", 0, 0), ("total_drift", 0, 1), ("landing_rate", 1, 0), ("drogue_rate", 1, 1))
        for key, row, column in positions:
            self.metrics_grid.addWidget(self.metric_cards[key], row, column)
        content_layout.addWidget(self.metrics_section)

        self.parachute_section, parachute_body = self._create_section("Parachute sizing")
        self.parachute_cards_row = QtWidgets.QHBoxLayout()
        self.parachute_cards_row.setSpacing(SPACING.md)
        parachute_body.addLayout(self.parachute_cards_row)
        self.parachute_empty_label = self._create_empty_state_label(
            "Analyse the current configuration to populate parachute sizing."
        )
        parachute_body.addWidget(self.parachute_empty_label)
        content_layout.addWidget(self.parachute_section)

        self.phase_section, phase_body = self._create_section("Phase breakdown")
        self.phase_table = QtWidgets.QTableWidget(0, 6)
        self.phase_table.setObjectName("phaseTable")
        self.phase_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.phase_table.verticalHeader().setVisible(False)
        self.phase_table.verticalHeader().setDefaultSectionSize(28)
        self.phase_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.phase_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.phase_table.setFocusPolicy(QtCore.Qt.NoFocus)
        phase_body.addWidget(self.phase_table)
        self.phase_empty_label = self._create_empty_state_label(
            "No analysed phase data are available."
        )
        phase_body.addWidget(self.phase_empty_label)
        content_layout.addWidget(self.phase_section)
        content_layout.addStretch(1)

        self.tab_widget.addTab(tab, "Results")

    def _build_compare_tab(self) -> None:
        tab = QtWidgets.QWidget()
        tab_layout = QtWidgets.QVBoxLayout(tab)
        configure_box_layout(tab_layout, margins=(0, 0, 0, 0), spacing=0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        tab_layout.addWidget(scroll)

        content = QtWidgets.QWidget()
        scroll.setWidget(content)

        content_layout = QtWidgets.QVBoxLayout(content)
        configure_box_layout(content_layout, margins=(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg))
        content_layout.setSpacing(SPACING.md)

        selector_section, selector_body = self._create_section("Compare configurations")
        selector_row = QtWidgets.QHBoxLayout()
        selector_row.setSpacing(SPACING.sm)
        selector_body.addLayout(selector_row)

        selector_row.addWidget(self._build_compare_field("Configuration A", "compareACombo"), 1)
        selector_row.addWidget(self._build_compare_field("Configuration B", "compareBCombo"), 1)
        content_layout.addWidget(selector_section)

        self.comparison_note = self._create_empty_state_label(
            "Create a second configuration to compare results."
        )
        content_layout.addWidget(self.comparison_note)

        self.comparison_section, comparison_body = self._create_section("Comparison")
        header_row = QtWidgets.QHBoxLayout()
        header_row.setSpacing(SPACING.sm)
        self.comparison_a_heading = QtWidgets.QLabel("Configuration A")
        self.comparison_a_heading.setObjectName("comparisonColumnTitle")
        self.comparison_b_heading = QtWidgets.QLabel("Configuration B")
        self.comparison_b_heading.setObjectName("comparisonColumnTitle")
        header_row.addWidget(QtWidgets.QLabel(""), 1)
        header_row.addWidget(self.comparison_a_heading, 1)
        header_row.addWidget(self.comparison_b_heading, 1)
        comparison_body.addLayout(header_row)

        self.comparison_matrix = QtWidgets.QFrame()
        self.comparison_matrix.setObjectName("comparisonMatrix")
        self.comparison_grid = QtWidgets.QGridLayout(self.comparison_matrix)
        configure_grid_layout(self.comparison_grid, margins=(SPACING.md, SPACING.md, SPACING.md, SPACING.md))
        self.comparison_grid.setColumnStretch(0, 0)
        self.comparison_grid.setColumnStretch(1, 1)
        self.comparison_grid.setColumnStretch(2, 1)
        comparison_body.addWidget(self.comparison_matrix)
        content_layout.addWidget(self.comparison_section)
        content_layout.addStretch(1)

        self.tab_widget.addTab(tab, "Compare")

        self.compare_a_combo.currentIndexChanged.connect(self._refresh_comparison)
        self.compare_b_combo.currentIndexChanged.connect(self._refresh_comparison)

    def _create_section(self, heading: str) -> tuple[QtWidgets.QFrame, QtWidgets.QVBoxLayout]:
        frame = QtWidgets.QFrame()
        frame.setObjectName("resultsSection")
        layout = QtWidgets.QVBoxLayout(frame)
        configure_box_layout(layout, margins=(SPACING.md, SPACING.md, SPACING.md, SPACING.md))
        layout.setSpacing(SPACING.sm)

        heading_label = QtWidgets.QLabel(heading.upper())
        heading_label.setObjectName("sectionHeader")
        layout.addWidget(heading_label)

        body = QtWidgets.QVBoxLayout()
        body.setSpacing(SPACING.sm)
        layout.addLayout(body)
        return frame, body

    def _create_empty_state_label(self, text: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(text)
        label.setObjectName("emptyStateLabel")
        label.setWordWrap(True)
        return label

    def _build_compare_field(self, label: str, combo_name: str) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        configure_box_layout(layout, margins=(0, 0, 0, 0), spacing=SPACING.xs)

        caption = QtWidgets.QLabel(label)
        caption.setObjectName("comparisonFieldLabel")
        layout.addWidget(caption)

        combo = QtWidgets.QComboBox()
        combo.setObjectName(combo_name)
        layout.addWidget(combo)

        if combo_name == "compareACombo":
            self.compare_a_combo = combo
        else:
            self.compare_b_combo = combo
        return container

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
        issues = list(validation_issues or [])
        self._populate_validation_cards(issues, configuration.warnings if configuration is not None else [])

        if configuration is None:
            self._clear_all()
            self.status_label.setText("No configuration selected.")
            return

        self._unit_system = configuration.display_unit_system
        self._update_table_headers()

        if issues:
            self.status_label.setText(
                "Analysis is blocked by validation issues. Fix the inputs or save the draft."
            )
            self.basis_label.setText("Basis: N/A")
            self._clear_analysis_tables()
            return

        if dirty:
            if configuration.analysis_results is None:
                self.status_label.setText(
                    "Draft edits are pending. Analyse to generate results."
                )
                self.basis_label.setText("Basis: N/A")
                self._clear_analysis_tables()
                return

            self.status_label.setText(
                "Draft edits are pending. Results below are from the last analysis."
            )
        elif configuration.analysis_results is None:
            self.status_label.setText(
                "This configuration has not been analysed."
            )
            self.basis_label.setText("Basis: N/A")
            self._clear_analysis_tables()
            return
        else:
            self.status_label.setText("Results reflect the current configuration state.")
        self.basis_label.setText(
            f"Basis: {_humanise_identifier(configuration.analysis_results.recovery_basis_label)}"
        )
        self._populate_metric_cards(configuration)
        self._populate_parachute_summaries(configuration)
        self._populate_phase_table(configuration)

    def _populate_validation_cards(
        self,
        issues: Sequence[ValidationIssue],
        warnings: Sequence[Warning],
    ) -> None:
        self._clear_layout(self.warning_cards_layout)
        total_cards = 0

        for issue in issues:
            card = IssueCard()
            card.set_issue(
                severity="error",
                title="Validation issue",
                message=issue.message,
                meta=f"{issue.code} • {issue.field_path}",
            )
            self.warning_cards_layout.addWidget(card)
            total_cards += 1

        for warning in warnings:
            meta_parts = [warning.code]
            if warning.source_field:
                meta_parts.append(warning.source_field)
            card = IssueCard()
            card.set_issue(
                severity=warning.severity,
                title=warning.title,
                message=warning.message,
                meta=" • ".join(meta_parts),
            )
            self.warning_cards_layout.addWidget(card)
            total_cards += 1

        self.warning_empty_label.setVisible(total_cards == 0)
        self.warning_section.setVisible(True)

    def _populate_metric_cards(self, configuration: Configuration) -> None:
        analysis = configuration.analysis_results
        if analysis is None:
            self._reset_metric_cards()
            return

        warnings_by_code = {warning.code for warning in configuration.warnings}
        landing_parachute = self._find_parachute(configuration, ("main", "single"))
        drogue_parachute = self._find_parachute(configuration, ("drogue",))

        landing_label = "Main descent rate" if configuration.recovery_mode == "dual" else "Single descent rate"
        landing_sublabel = "At landing"
        drogue_sublabel = "Before main deploy"

        self.metric_cards["total_time"].set_metric(
            label="Total descent time",
            value=format_time(analysis.total_descent_time_s),
            sublabel="Apogee to ground" if analysis.recovery_basis_label == "from_apogee" else "Basis to ground",
        )
        self.metric_cards["total_drift"].set_metric(
            label="Estimated drift",
            value=format_length(analysis.total_estimated_drift_m, self._unit_system),
            sublabel="Downwind from launch pad",
            alert="DRIFT_ESTIMATE_HIGH" in warnings_by_code,
        )
        self.metric_cards["landing_rate"].set_metric(
            label=landing_label,
            value=format_velocity(
                landing_parachute.resulting_descent_velocity_mps if landing_parachute is not None else None,
                self._unit_system,
            ),
            sublabel=landing_sublabel,
            alert="MAIN_DESCENT_VELOCITY_HIGH" in warnings_by_code,
        )
        self.metric_cards["drogue_rate"].set_metric(
            label="Drogue descent rate",
            value=format_velocity(
                drogue_parachute.resulting_descent_velocity_mps if drogue_parachute is not None else None,
                self._unit_system,
            ),
            sublabel=drogue_sublabel if drogue_parachute is not None else "Not used in single deployment",
            alert="DROGUE_DESCENT_VELOCITY_HIGH" in warnings_by_code,
        )

    def _populate_parachute_summaries(self, configuration: Configuration) -> None:
        self._clear_layout(self.parachute_cards_row)
        if not configuration.parachutes or configuration.analysis_results is None:
            self.parachute_empty_label.setVisible(True)
            return

        self.parachute_empty_label.setVisible(False)
        for parachute in configuration.parachutes:
            card = ParachuteSummaryCard()
            selected_item = self._catalogue_by_id.get(parachute.selected_catalogue_item_id or "")
            card.set_parachute(
                role=parachute.role,
                family=parachute.family,
                cd=parachute.cd,
                target_velocity=format_velocity(parachute.target_descent_velocity_mps, self._unit_system),
                theoretical_diameter=format_length(parachute.theoretical_diameter_m, self._unit_system),
                recommended_diameter=format_length(parachute.recommended_diameter_m, self._unit_system),
                selected_item=selected_item.product_name if selected_item is not None else "N/A",
                selected_diameter=format_length(parachute.selected_nominal_diameter_m, self._unit_system),
                resulting_velocity=format_velocity(
                    parachute.resulting_descent_velocity_mps,
                    self._unit_system,
                ),
            )
            self.parachute_cards_row.addWidget(card, 1)
        self.parachute_cards_row.addStretch(1)

    def _populate_phase_table(self, configuration: Configuration) -> None:
        analysis = configuration.analysis_results
        if analysis is None:
            self.phase_table.setRowCount(0)
            self.phase_table.setVisible(False)
            self.phase_empty_label.setVisible(True)
            return

        phase_summaries = analysis.phase_summaries
        self.phase_table.setRowCount(len(phase_summaries))
        for row, phase in enumerate(phase_summaries):
            phase_item = QtWidgets.QTableWidgetItem(f"● {_humanise_identifier(phase.phase_name)}")
            phase_item.setForeground(QtGui.QBrush(_phase_colour(phase.phase_name)))
            phase_item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.phase_table.setItem(row, 0, phase_item)

            self._set_table_item(
                self.phase_table,
                row,
                1,
                format_length(phase.start_altitude_m, self._unit_system),
                alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
            )
            self._set_table_item(
                self.phase_table,
                row,
                2,
                format_length(phase.end_altitude_m, self._unit_system),
                alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
            )
            self._set_table_item(
                self.phase_table,
                row,
                3,
                format_time(phase.estimated_duration_s),
                alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
            )
            self._set_table_item(
                self.phase_table,
                row,
                4,
                format_velocity(phase.nominal_descent_velocity_mps, self._unit_system),
                alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
            )
            self._set_table_item(
                self.phase_table,
                row,
                5,
                format_length(phase.estimated_drift_m, self._unit_system),
                alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
            )

        self.phase_table.setVisible(bool(phase_summaries))
        self.phase_empty_label.setVisible(not phase_summaries)

    def _clear_all(self) -> None:
        self._clear_analysis_tables()

    def _clear_analysis_tables(self) -> None:
        self.basis_label.setText("Basis: N/A")
        self._reset_metric_cards()
        self._clear_layout(self.parachute_cards_row)
        self.parachute_empty_label.setVisible(True)
        self.phase_table.setRowCount(0)
        self.phase_table.setVisible(False)
        self.phase_empty_label.setVisible(True)

    def _reset_metric_cards(self) -> None:
        self.metric_cards["total_time"].set_metric(
            label="Total descent time",
            value="N/A",
            sublabel="Apogee to ground",
        )
        self.metric_cards["total_drift"].set_metric(
            label="Estimated drift",
            value="N/A",
            sublabel="Downwind from launch pad",
        )
        self.metric_cards["landing_rate"].set_metric(
            label="Main descent rate",
            value="N/A",
            sublabel="At landing",
        )
        self.metric_cards["drogue_rate"].set_metric(
            label="Drogue descent rate",
            value="N/A",
            sublabel="Before main deploy",
        )

    def _update_table_headers(self) -> None:
        length_unit = "ft" if self._unit_system == "imperial" else "m"
        velocity_unit = "ft/s" if self._unit_system == "imperial" else "m/s"
        self.phase_table.setHorizontalHeaderLabels(
            [
                "Phase",
                f"Alt. start [{length_unit}]",
                f"Alt. end [{length_unit}]",
                "Duration [s]",
                f"Avg. rate [{velocity_unit}]",
                f"Drift [{length_unit}]",
            ]
        )

    def _refresh_comparison(self) -> None:
        project = self._project
        self._clear_grid(self.comparison_grid)

        if project is None or len(project.configurations) < 2:
            self.comparison_note.setVisible(True)
            self.comparison_section.setVisible(False)
            return

        config_a = self._find_configuration(self.compare_a_combo.currentData())
        config_b = self._find_configuration(self.compare_b_combo.currentData())
        if config_a is None or config_b is None:
            self.comparison_note.setVisible(True)
            self.comparison_section.setVisible(False)
            return

        self.comparison_note.setVisible(False)
        self.comparison_section.setVisible(True)
        self.comparison_a_heading.setText(self.compare_a_combo.currentText() or "Configuration A")
        self.comparison_b_heading.setText(self.compare_b_combo.currentText() or "Configuration B")

        rows = build_comparison_rows(
            config_a,
            config_b,
            tuple(self._catalogue_by_id.values()),
            unit_system=self._unit_system,
        )
        for row_index, comparison_row in enumerate(rows):
            metric_label = QtWidgets.QLabel(comparison_row.metric)
            metric_label.setObjectName("comparisonMetricLabel")
            self.comparison_grid.addWidget(metric_label, row_index, 0)

            changed = comparison_row.value_a != comparison_row.value_b
            value_a = QtWidgets.QLabel(comparison_row.value_a)
            value_a.setObjectName("comparisonValue")
            value_a.setProperty("changed", changed)
            value_a.setWordWrap(True)
            value_a.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            _refresh_style(value_a)

            value_b = QtWidgets.QLabel(comparison_row.value_b)
            value_b.setObjectName("comparisonValue")
            value_b.setProperty("changed", changed)
            value_b.setWordWrap(True)
            value_b.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            _refresh_style(value_b)

            self.comparison_grid.addWidget(value_a, row_index, 1)
            self.comparison_grid.addWidget(value_b, row_index, 2)

    def _find_configuration(self, configuration_id: str | None) -> Configuration | None:
        if self._project is None or configuration_id is None:
            return None
        for configuration in self._project.configurations:
            if configuration.configuration_id == configuration_id:
                return configuration
        return None

    def _find_parachute(
        self,
        configuration: Configuration,
        roles: Sequence[str],
    ):
        for role in roles:
            for parachute in configuration.parachutes:
                if parachute.role == role:
                    return parachute
        return None

    def _set_table_item(
        self,
        table: QtWidgets.QTableWidget,
        row: int,
        column: int,
        text: str,
        *,
        alignment: QtCore.Qt.AlignmentFlag = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
    ) -> None:
        item = QtWidgets.QTableWidgetItem(text)
        item.setTextAlignment(alignment)
        table.setItem(row, column, item)

    def _clear_layout(self, layout: QtWidgets.QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout(child_layout)

    def _clear_grid(self, layout: QtWidgets.QGridLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
