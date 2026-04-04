"""Custom top bar and state badge for the DRIFT desktop shell."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6 import QtCore, QtGui, QtWidgets

from drift import APP_NAME, APP_VERSION
from drift.ui.theme import (
    Colours,
    SPACING,
    configure_box_layout,
    mono_font,
    rgba,
    ui_font,
)


@dataclass(frozen=True)
class StateBadgePresentation:
    """Visual description for the current configuration state."""

    key: str
    label: str
    colour: str


class StateBadgeWidget(QtWidgets.QFrame):
    """Compact semantic state badge shown in the top bar."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("stateBadge")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        layout = QtWidgets.QHBoxLayout(self)
        configure_box_layout(
            layout,
            margins=(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs),
            spacing=SPACING.xs + 2,
        )

        self.dot = QtWidgets.QLabel()
        self.dot.setFixedSize(6, 6)
        self.dot.setStyleSheet("border-radius: 3px;")
        layout.addWidget(self.dot, 0, QtCore.Qt.AlignVCenter)

        self.label = QtWidgets.QLabel()
        label_font = mono_font(point_size=10, weight=QtGui.QFont.Medium)
        label_font.setCapitalization(QtGui.QFont.AllUppercase)
        self.label.setFont(label_font)
        layout.addWidget(self.label, 0, QtCore.Qt.AlignVCenter)

        self.set_state(StateBadgePresentation("draft", "Draft", Colours.STATE_DRAFT))

    def set_state(self, presentation: StateBadgePresentation) -> None:
        """Apply the current semantic badge presentation."""

        self.label.setText(presentation.label.upper())
        background = rgba(presentation.colour, 0.18)
        border = rgba(presentation.colour, 0.32)
        self.setStyleSheet(
            f"""
QFrame#stateBadge {{
    background-color: {background};
    border: 1px solid {border};
    border-radius: 11px;
}}
"""
        )
        self.dot.setStyleSheet(
            f"background-color: {presentation.colour}; border-radius: 3px; min-width: 6px;"
        )

    def state_text(self) -> str:
        """Return the current badge text for smoke tests."""

        return self.label.text()


class TopBarWidget(QtWidgets.QWidget):
    """Engineering-style top bar that binds shell actions and state."""

    new_project_requested = QtCore.Signal()
    load_requested = QtCore.Signal()
    save_requested = QtCore.Signal()
    export_requested = QtCore.Signal()
    reset_requested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(40)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QHBoxLayout(self)
        configure_box_layout(
            layout,
            margins=(SPACING.lg, SPACING.xs, SPACING.lg, SPACING.xs),
            spacing=SPACING.sm,
        )

        self.brand_label = QtWidgets.QLabel(APP_NAME)
        self.brand_label.setObjectName("brandLabel")
        self.brand_label.setFont(mono_font(point_size=13, weight=QtGui.QFont.DemiBold))
        layout.addWidget(self.brand_label, 0, QtCore.Qt.AlignVCenter)

        self.version_label = QtWidgets.QLabel(f"v{APP_VERSION}")
        self.version_label.setObjectName("versionLabel")
        self.version_label.setFont(mono_font(point_size=10))
        layout.addWidget(self.version_label, 0, QtCore.Qt.AlignVCenter)

        layout.addWidget(self._divider(), 0, QtCore.Qt.AlignVCenter)

        self.project_button = QtWidgets.QToolButton()
        self.project_button.setObjectName("projectSelectorButton")
        self.project_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.project_button.setText("Untitled Project")
        self.project_menu = QtWidgets.QMenu(self.project_button)
        self.current_project_action = self.project_menu.addAction("Untitled Project")
        self.current_project_action.setEnabled(False)
        self.project_menu.addSeparator()
        self.new_project_action = self.project_menu.addAction("New project")
        self.project_button.setMenu(self.project_menu)
        self.new_project_action.triggered.connect(self.new_project_requested)
        layout.addWidget(self.project_button, 0, QtCore.Qt.AlignVCenter)

        layout.addWidget(self._divider(), 0, QtCore.Qt.AlignVCenter)

        self.save_button = self._make_action_button(
            tooltip="Save project",
            theme_icon="document-save-as",
            fallback_icon=QtWidgets.QStyle.SP_DialogSaveButton,
            fallback_text="S",
        )
        self.load_button = self._make_action_button(
            tooltip="Import project",
            theme_icon="document-save",
            fallback_icon=QtWidgets.QStyle.SP_DialogOpenButton,
            fallback_text="I",
        )
        self.export_button = self._make_action_button(
            tooltip="Export Markdown summary",
            theme_icon="document-export",
            fallback_icon=None,
            fallback_text="MD",
        )
        self.reset_button = self._make_action_button(
            tooltip="Reset draft edits",
            theme_icon="view-refresh",
            fallback_icon=QtWidgets.QStyle.SP_BrowserReload,
            fallback_text="R",
        )

        self.save_button.clicked.connect(self.save_requested)
        self.load_button.clicked.connect(self.load_requested)
        self.export_button.clicked.connect(self.export_requested)
        self.reset_button.clicked.connect(self.reset_requested)

        layout.addWidget(self.save_button, 0, QtCore.Qt.AlignVCenter)
        layout.addWidget(self.load_button, 0, QtCore.Qt.AlignVCenter)
        layout.addWidget(self.export_button, 0, QtCore.Qt.AlignVCenter)
        layout.addWidget(self.reset_button, 0, QtCore.Qt.AlignVCenter)
        layout.addStretch(1)

        self.state_badge = StateBadgeWidget(self)
        layout.addWidget(self.state_badge, 0, QtCore.Qt.AlignVCenter)

    def _divider(self) -> QtWidgets.QFrame:
        divider = QtWidgets.QFrame()
        divider.setObjectName("topBarDivider")
        divider.setFrameShape(QtWidgets.QFrame.VLine)
        divider.setFixedHeight(20)
        return divider

    def _make_action_button(
        self,
        *,
        tooltip: str,
        theme_icon: str,
        fallback_icon: QtWidgets.QStyle.StandardPixmap | None,
        fallback_text: str,
    ) -> QtWidgets.QToolButton:
        button = QtWidgets.QToolButton()
        button.setObjectName("topBarActionButton")
        button.setToolTip(tooltip)
        button.setAutoRaise(False)
        button.setFont(ui_font(point_size=11, weight=QtGui.QFont.DemiBold))
        icon = QtGui.QIcon.fromTheme(theme_icon)
        if icon.isNull() and fallback_icon is not None:
            icon = self.style().standardIcon(fallback_icon)
        if icon.isNull():
            button.setText(fallback_text)
        else:
            button.setIcon(icon)
            button.setIconSize(QtCore.QSize(16, 16))
        return button

    def set_project_context(self, project_name: str, *, file_name: str | None = None) -> None:
        """Update the displayed project label and tooltip."""

        project_name = project_name or "Untitled Project"
        self.project_button.setText(project_name)
        self.current_project_action.setText(project_name)
        tooltip = project_name if file_name is None else f"{project_name}\n{file_name}"
        self.project_button.setToolTip(tooltip)

    def set_state(self, presentation: StateBadgePresentation) -> None:
        """Update the semantic state badge."""

        self.state_badge.set_state(presentation)

    def set_action_state(
        self,
        *,
        has_project: bool,
        has_configuration: bool,
        can_reset: bool,
    ) -> None:
        """Enable or disable the top-bar actions based on shell state."""

        self.save_button.setEnabled(has_project)
        self.load_button.setEnabled(True)
        self.export_button.setEnabled(has_configuration)
        self.reset_button.setEnabled(can_reset)


__all__ = ["StateBadgePresentation", "StateBadgeWidget", "TopBarWidget"]
