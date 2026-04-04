"""Right-panel recovery schematic, timeline, and assumptions for DRIFT."""

from __future__ import annotations

from typing import Sequence

from PySide6 import QtCore, QtWidgets

from drift.formatting import format_length, format_time
from drift.models import Configuration
from drift.services.validation import ValidationIssue
from drift.services.visualization import TimelineEvent, build_recovery_visual_model
from drift.ui.theme import SPACING, configure_box_layout

from .schematic_widget import RecoverySchematicWidget


def _event_phase_key(event: TimelineEvent) -> str:
    label = event.label.casefold()
    if "drogue" in label:
        return "drogue"
    if "main" in label or "single" in label or "landing" in label:
        return "main"
    if "apogee" in label:
        return "freefall"
    return "freefall"


class TimelineEventWidget(QtWidgets.QFrame):
    """Compact engineering timeline row."""

    def __init__(
        self,
        event: TimelineEvent,
        *,
        unit_system: str,
        is_last: bool,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("timelineEvent")

        layout = QtWidgets.QHBoxLayout(self)
        configure_box_layout(layout, margins=(0, 0, 0, 0), spacing=SPACING.sm)

        rail = QtWidgets.QWidget()
        rail.setObjectName("timelineRail")
        rail_layout = QtWidgets.QVBoxLayout(rail)
        configure_box_layout(rail_layout, margins=(0, 0, 0, 0), spacing=0)
        rail_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        phase_key = _event_phase_key(event)
        dot = QtWidgets.QLabel("●")
        dot.setObjectName("timelineDot")
        dot.setProperty("phase", phase_key)
        rail_layout.addWidget(dot, 0, QtCore.Qt.AlignHCenter)

        line = QtWidgets.QFrame()
        line.setObjectName("timelineLine")
        line.setVisible(not is_last)
        line.setMinimumWidth(1)
        line.setMaximumWidth(1)
        line.setMinimumHeight(32)
        rail_layout.addWidget(line, 1, QtCore.Qt.AlignHCenter)

        layout.addWidget(rail, 0, QtCore.Qt.AlignTop)

        content = QtWidgets.QVBoxLayout()
        content.setSpacing(2)
        layout.addLayout(content, 1)

        meta_row = QtWidgets.QHBoxLayout()
        meta_row.setSpacing(SPACING.sm)
        content.addLayout(meta_row)

        time_text = "Input" if event.time_s is None else f"T+{event.time_s:.2f} s"
        self.time_label = QtWidgets.QLabel(time_text)
        self.time_label.setObjectName("timelineMetaLabel")
        self.time_label.setProperty("role", "mono")
        meta_row.addWidget(self.time_label, 0, QtCore.Qt.AlignLeft)

        self.altitude_label = QtWidgets.QLabel(format_length(event.altitude_m, unit_system))
        self.altitude_label.setObjectName("timelineMetaLabel")
        self.altitude_label.setProperty("role", "mono")
        meta_row.addWidget(self.altitude_label, 0, QtCore.Qt.AlignLeft)
        meta_row.addStretch(1)

        self.event_label = QtWidgets.QLabel(event.label)
        self.event_label.setObjectName("timelineEventLabel")
        self.event_label.setWordWrap(True)
        content.addWidget(self.event_label)

        self.note_label = QtWidgets.QLabel(event.notes or "")
        self.note_label.setObjectName("timelineEventNote")
        self.note_label.setProperty("role", "helper")
        self.note_label.setWordWrap(True)
        self.note_label.setVisible(bool(event.notes))
        content.addWidget(self.note_label)


class VisualsPanel(QtWidgets.QWidget):
    """Recovery schematic and timeline widgets wired to analysed model state."""

    _ASSUMPTION_LINES = (
        "Vertical descent only.",
        "Constant nominal descent rate is used per phase.",
        "Deployment timing is not modelled separately from phase start.",
        "Drift is estimated from horizontal wind speed and phase duration.",
    )

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.timeline_event_widgets: list[TimelineEventWidget] = []
        self.assumption_labels: list[QtWidgets.QLabel] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QtWidgets.QVBoxLayout(self)
        configure_box_layout(root_layout, margins=(0, 0, 0, 0), spacing=0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        root_layout.addWidget(scroll)

        content = QtWidgets.QWidget()
        scroll.setWidget(content)

        layout = QtWidgets.QVBoxLayout(content)
        configure_box_layout(layout)
        layout.setSpacing(SPACING.md)

        schematic_section, schematic_body = self._create_section(
            "Recovery schematic",
            "Profile view. Not to scale.",
        )
        self.schematic_widget = RecoverySchematicWidget()
        self.schematic_widget.setMinimumHeight(360)
        schematic_body.addWidget(self.schematic_widget)
        layout.addWidget(schematic_section)

        timeline_section, timeline_body = self._create_section(
            "Event timeline",
            "Event order follows the analysed phases and deployment markers.",
        )
        self.timeline_empty_label = QtWidgets.QLabel(
            "Analyse the current configuration to populate the event sequence."
        )
        self.timeline_empty_label.setObjectName("emptyStateLabel")
        self.timeline_empty_label.setWordWrap(True)
        timeline_body.addWidget(self.timeline_empty_label)

        self.timeline_content = QtWidgets.QWidget()
        self.timeline_content.setObjectName("timelineContent")
        self.timeline_events_layout = QtWidgets.QVBoxLayout(self.timeline_content)
        configure_box_layout(
            self.timeline_events_layout,
            margins=(0, 0, 0, 0),
            spacing=SPACING.sm,
        )
        timeline_body.addWidget(self.timeline_content)

        self.timeline_summary_label = QtWidgets.QLabel()
        self.timeline_summary_label.setObjectName("timelineSummaryLabel")
        self.timeline_summary_label.setProperty("role", "helper")
        self.timeline_summary_label.setWordWrap(True)
        timeline_body.addWidget(self.timeline_summary_label)
        layout.addWidget(timeline_section)

        assumptions_section, assumptions_body = self._create_section(
            "Assumptions",
            "Current assumptions used by the recovery model.",
        )
        assumptions_list = QtWidgets.QWidget()
        assumptions_list.setObjectName("assumptionsList")
        assumptions_layout = QtWidgets.QVBoxLayout(assumptions_list)
        configure_box_layout(
            assumptions_layout,
            margins=(0, 0, 0, 0),
            spacing=SPACING.sm,
        )
        for line in self._ASSUMPTION_LINES:
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(SPACING.sm)
            bullet = QtWidgets.QLabel("•")
            bullet.setObjectName("assumptionBullet")
            text = QtWidgets.QLabel(line)
            text.setObjectName("assumptionText")
            text.setWordWrap(True)
            row.addWidget(bullet, 0, QtCore.Qt.AlignTop)
            row.addWidget(text, 1)
            assumptions_layout.addLayout(row)
            self.assumption_labels.append(text)
        assumptions_body.addWidget(assumptions_list)
        layout.addWidget(assumptions_section)
        layout.addStretch(1)

        self.show_configuration(None)

    def _create_section(
        self,
        title: str,
        note: str,
    ) -> tuple[QtWidgets.QFrame, QtWidgets.QVBoxLayout]:
        section = QtWidgets.QFrame()
        section.setObjectName("sidebarSection")
        layout = QtWidgets.QVBoxLayout(section)
        configure_box_layout(layout, margins=(SPACING.md, SPACING.md, SPACING.md, SPACING.md))
        layout.setSpacing(SPACING.sm)

        title_label = QtWidgets.QLabel(title.upper())
        title_label.setObjectName("sidebarSectionTitle")
        layout.addWidget(title_label)

        note_label = QtWidgets.QLabel(note)
        note_label.setObjectName("sidebarSectionNote")
        note_label.setProperty("role", "helper")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        body = QtWidgets.QVBoxLayout()
        body.setSpacing(SPACING.sm)
        layout.addLayout(body)
        return section, body

    def show_configuration(
        self,
        configuration: Configuration | None,
        *,
        validation_issues: Sequence[ValidationIssue] | None = None,
        dirty: bool = False,
    ) -> None:
        issues = list(validation_issues or [])
        if configuration is None:
            self.schematic_widget.show_message(
                "Select or create a configuration to populate the recovery view."
            )
            self._set_timeline_empty("Analyse the current configuration to populate the event sequence.")
            return

        unit_system = configuration.display_unit_system
        if issues:
            self.schematic_widget.show_message(
                "Analysis is blocked by validation issues. Fix the inputs before generating visuals."
            )
            self._set_timeline_empty(
                f"{len(issues)} validation issue(s) currently block the event sequence."
            )
            return

        if dirty:
            self.schematic_widget.show_message(
                "Draft edits are pending. Re-analyse to update the recovery view."
            )
            self._set_timeline_empty("Draft edits are pending.")
            return

        if configuration.analysis_results is None:
            self.schematic_widget.show_message(
                "This configuration has not been analysed."
            )
            self._set_timeline_empty("Analyse the current configuration to populate the event sequence.")
            return

        visual_model = build_recovery_visual_model(configuration)
        self.schematic_widget.set_visual_model(visual_model, unit_system=unit_system)
        self._populate_timeline(
            visual_model.timeline_events,
            unit_system=unit_system,
            total_descent_time_s=configuration.analysis_results.total_descent_time_s,
        )

    def _set_timeline_empty(self, message: str) -> None:
        self._clear_timeline()
        self.timeline_empty_label.setText(message)
        self.timeline_empty_label.setVisible(True)
        self.timeline_content.setVisible(False)
        self.timeline_summary_label.setVisible(False)

    def _populate_timeline(
        self,
        events: Sequence[TimelineEvent],
        *,
        unit_system: str,
        total_descent_time_s: float | None,
    ) -> None:
        self._clear_timeline()
        self.timeline_empty_label.setVisible(False)
        self.timeline_content.setVisible(True)

        for index, event in enumerate(events):
            widget = TimelineEventWidget(
                event,
                unit_system=unit_system,
                is_last=index == len(events) - 1,
            )
            self.timeline_events_layout.addWidget(widget)
            self.timeline_event_widgets.append(widget)

        self.timeline_events_layout.addStretch(1)
        self.timeline_summary_label.setText(
            f"Total descent time: {format_time(total_descent_time_s)}"
        )
        self.timeline_summary_label.setVisible(True)

    def _clear_timeline(self) -> None:
        self.timeline_event_widgets.clear()
        while self.timeline_events_layout.count():
            item = self.timeline_events_layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                while child_layout.count():
                    child_item = child_layout.takeAt(0)
                    child_widget = child_item.widget()
                    if child_widget is not None:
                        child_widget.deleteLater()


__all__ = ["VisualsPanel"]
