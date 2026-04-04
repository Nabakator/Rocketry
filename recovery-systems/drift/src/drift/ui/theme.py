"""Shared visual foundation for the DRIFT desktop shell."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from PySide6 import QtCore, QtGui, QtWidgets


class Colours:
    """Centralised colour tokens derived from the DRIFT design spec."""

    SURFACE_0 = "#16191d"
    SURFACE_1 = "#1d2025"
    SURFACE_2 = "#24282f"
    SURFACE_3 = "#2c3038"

    FOREGROUND = "#dce1e8"
    MUTED_FOREGROUND = "#7a8494"

    PRIMARY = "#4a9be8"
    PRIMARY_HOVER = "#3f8bd4"
    PRIMARY_FOREGROUND = "#f7fbff"

    WARNING = "#f5a623"
    DESTRUCTIVE = "#d44a4a"
    SUCCESS = "#47a05c"
    INFO = "#4a9be8"

    STATE_DRAFT = "#5f6673"
    STATE_VALID = PRIMARY
    STATE_ANALYSED = SUCCESS
    STATE_INVALID = DESTRUCTIVE

    PHASE_ASCENT = "#d45d5d"
    PHASE_FREEFALL = "#e8912a"
    PHASE_DROGUE = "#3a9fd4"
    PHASE_MAIN = "#3d997a"

    BORDER = "#333a45"
    PANEL_BORDER = "#282d35"
    INPUT_BG = "#1c2027"


@dataclass(frozen=True)
class SpacingScale:
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24


SPACING = SpacingScale()


def configure_box_layout(
    layout: QtWidgets.QBoxLayout,
    *,
    margins: tuple[int, int, int, int] = (SPACING.lg, SPACING.md, SPACING.lg, SPACING.md),
    spacing: int = SPACING.md,
) -> None:
    """Apply the shared spacing system to a box layout."""

    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)


def configure_form_layout(
    layout: QtWidgets.QFormLayout,
    *,
    margins: tuple[int, int, int, int] = (SPACING.lg, SPACING.md, SPACING.lg, SPACING.md),
) -> None:
    """Apply the shared spacing system to a form layout."""

    layout.setContentsMargins(*margins)
    layout.setHorizontalSpacing(SPACING.lg)
    layout.setVerticalSpacing(SPACING.sm)
    layout.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    layout.setFormAlignment(QtCore.Qt.AlignTop)


def configure_grid_layout(
    layout: QtWidgets.QGridLayout,
    *,
    margins: tuple[int, int, int, int] = (SPACING.lg, SPACING.md, SPACING.lg, SPACING.md),
) -> None:
    """Apply the shared spacing system to a grid layout."""

    layout.setContentsMargins(*margins)
    layout.setHorizontalSpacing(SPACING.sm)
    layout.setVerticalSpacing(SPACING.sm)


@lru_cache(maxsize=1)
def font_families() -> tuple[str, str]:
    """Resolve the preferred UI and monospace font families available locally."""

    installed = {family.casefold(): family for family in QtGui.QFontDatabase.families()}

    def resolve(candidates: tuple[str, ...]) -> str:
        for candidate in candidates:
            matched = installed.get(candidate.casefold())
            if matched is not None:
                return matched
        return candidates[-1]

    ui_family = resolve(("Inter", "SF Pro Text", "Segoe UI", "Helvetica Neue", "Arial"))
    mono_family = resolve(
        ("JetBrains Mono", "SF Mono", "Menlo", "Consolas", "Monaco", "Courier New")
    )
    return ui_family, mono_family


def ui_font(*, point_size: int = 12, weight: int = QtGui.QFont.Normal) -> QtGui.QFont:
    """Return the shared UI font."""

    family, _ = font_families()
    return QtGui.QFont(family, point_size, weight)


def mono_font(*, point_size: int = 12, weight: int = QtGui.QFont.Normal) -> QtGui.QFont:
    """Return the shared monospace font."""

    _, family = font_families()
    font = QtGui.QFont(family, point_size, weight)
    font.setStyleHint(QtGui.QFont.Monospace)
    return font


def qcolor(value: str) -> QtGui.QColor:
    """Convert a hex colour token into a ``QColor``."""

    return QtGui.QColor(value)


def rgba(value: str, alpha: float) -> str:
    """Convert a hex colour token into an rgba() CSS value."""

    color = QtGui.QColor(value)
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha:.3f})"


def build_palette() -> QtGui.QPalette:
    """Create the shared DRIFT palette."""

    palette = QtGui.QPalette()
    disabled_text = qcolor(Colours.MUTED_FOREGROUND)
    disabled_text.setAlphaF(0.55)

    palette.setColor(QtGui.QPalette.Window, qcolor(Colours.SURFACE_0))
    palette.setColor(QtGui.QPalette.WindowText, qcolor(Colours.FOREGROUND))
    palette.setColor(QtGui.QPalette.Base, qcolor(Colours.SURFACE_1))
    palette.setColor(QtGui.QPalette.AlternateBase, qcolor(Colours.SURFACE_2))
    palette.setColor(QtGui.QPalette.ToolTipBase, qcolor(Colours.SURFACE_2))
    palette.setColor(QtGui.QPalette.ToolTipText, qcolor(Colours.FOREGROUND))
    palette.setColor(QtGui.QPalette.Text, qcolor(Colours.FOREGROUND))
    palette.setColor(QtGui.QPalette.Button, qcolor(Colours.SURFACE_2))
    palette.setColor(QtGui.QPalette.ButtonText, qcolor(Colours.FOREGROUND))
    palette.setColor(QtGui.QPalette.BrightText, qcolor(Colours.PRIMARY_FOREGROUND))
    palette.setColor(QtGui.QPalette.Highlight, qcolor(Colours.PRIMARY))
    palette.setColor(QtGui.QPalette.HighlightedText, qcolor(Colours.PRIMARY_FOREGROUND))
    palette.setColor(QtGui.QPalette.PlaceholderText, qcolor(Colours.MUTED_FOREGROUND))

    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, disabled_text)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, disabled_text)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, disabled_text)
    return palette


def build_stylesheet() -> str:
    """Build the shared QSS foundation for the DRIFT shell."""

    ui_family, mono_family = font_families()
    return f"""
QWidget {{
    color: {Colours.FOREGROUND};
    font-family: "{ui_family}";
    font-size: 12px;
}}

QMainWindow {{
    background-color: {Colours.SURFACE_0};
}}

QLabel {{
    background: transparent;
}}

QWidget#leftPanel,
QWidget#rightPanel {{
    background-color: {Colours.SURFACE_1};
}}

QWidget#centrePanel {{
    background-color: {Colours.SURFACE_0};
}}

QTabWidget#centreTabs {{
    background-color: {Colours.SURFACE_0};
}}

QWidget#topBar {{
    background-color: {Colours.SURFACE_0};
    border-bottom: 1px solid {Colours.PANEL_BORDER};
}}

QWidget#leftPanel {{
    border-right: 1px solid {Colours.PANEL_BORDER};
}}

QWidget#rightPanel {{
    border-left: 1px solid {Colours.PANEL_BORDER};
}}

QSplitter::handle {{
    background-color: {Colours.PANEL_BORDER};
}}

QSplitter::handle:hover {{
    background-color: {Colours.BORDER};
}}

QScrollArea,
QAbstractScrollArea {{
    border: none;
    background: transparent;
}}

QGroupBox {{
    background-color: {Colours.SURFACE_1};
    border: 1px solid {Colours.PANEL_BORDER};
    border-radius: 4px;
    margin-top: 10px;
    padding-top: {SPACING.sm}px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: {SPACING.md}px;
    padding: 0 {SPACING.xs}px;
    color: {Colours.MUTED_FOREGROUND};
    font-size: 11px;
    font-weight: 600;
}}

QLabel#brandLabel {{
    color: {Colours.PRIMARY};
    font-family: "{mono_family}";
    font-size: 13px;
    font-weight: 600;
}}

QLabel#versionLabel {{
    color: {Colours.MUTED_FOREGROUND};
    font-family: "{mono_family}";
    font-size: 10px;
}}

QToolButton#projectSelectorButton {{
    background-color: {Colours.SURFACE_1};
    border: 1px solid {Colours.BORDER};
    border-radius: 3px;
    padding: 5px 10px;
    min-height: 26px;
    color: {Colours.FOREGROUND};
}}

QToolButton#projectSelectorButton::menu-indicator {{
    subcontrol-origin: padding;
    subcontrol-position: right center;
}}

QToolButton#topBarActionButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    padding: 0;
}}

QToolButton#topBarActionButton:hover {{
    background-color: {Colours.SURFACE_2};
    border: 1px solid {Colours.BORDER};
}}

QToolButton#topBarActionButton:disabled {{
    color: {rgba(Colours.FOREGROUND, 0.4)};
}}

QFrame#topBarDivider {{
    background-color: {Colours.PANEL_BORDER};
    min-width: 1px;
    max-width: 1px;
}}

QWidget#leftPanelFooter {{
    background-color: {Colours.SURFACE_1};
    border-top: 1px solid {Colours.PANEL_BORDER};
}}

QWidget#segmentedControl {{
    background-color: {Colours.SURFACE_2};
    border: 1px solid {Colours.BORDER};
    border-radius: 4px;
}}

QPushButton#configTabButton,
QPushButton#modeToggleButton,
QPushButton#configAddButton {{
    background-color: {Colours.SURFACE_2};
    color: {Colours.MUTED_FOREGROUND};
    border: 1px solid {Colours.PANEL_BORDER};
    border-radius: 3px;
    min-height: 28px;
}}

QPushButton#configTabButton {{
    padding: 4px 10px;
}}

QPushButton#configAddButton {{
    max-width: 32px;
    min-width: 32px;
    padding: 0;
    font-family: "{mono_family}";
    font-weight: 600;
}}

QPushButton#configTabButton:checked,
QPushButton#modeToggleButton:checked {{
    background-color: {rgba(Colours.PRIMARY, 0.16)};
    color: {Colours.PRIMARY};
    border: 1px solid {rgba(Colours.PRIMARY, 0.38)};
}}

QPushButton#configTabButton:hover,
QPushButton#modeToggleButton:hover,
QPushButton#configAddButton:hover {{
    background-color: {Colours.SURFACE_3};
}}

QPushButton#modeToggleButton {{
    min-width: 96px;
    padding: 6px 12px;
}}

QLabel#deploymentHelper,
QLabel#windHelper,
QLabel#atmosphereHelper,
QLabel#panelStateLabel {{
    color: {Colours.MUTED_FOREGROUND};
    font-size: 10px;
}}

QLabel#panelStateLabel[state="draft"] {{
    color: {Colours.WARNING};
}}

QLabel#panelStateLabel[state="valid"] {{
    color: {Colours.PRIMARY};
}}

QLabel#panelStateLabel[state="analysed"] {{
    color: {Colours.SUCCESS};
}}

QLabel#panelStateLabel[state="invalid"] {{
    color: {Colours.DESTRUCTIVE};
}}

QLabel[role="helper"],
QLabel[role="status"],
QLabel[role="muted"] {{
    color: {Colours.MUTED_FOREGROUND};
}}

QLabel[role="helper"] {{
    font-size: 10px;
}}

QLabel#statusBanner {{
    background-color: {Colours.SURFACE_1};
    border: 1px solid {Colours.PANEL_BORDER};
    border-radius: 4px;
    padding: {SPACING.md}px;
    color: {Colours.FOREGROUND};
}}

QLabel#basisLabel {{
    color: {Colours.MUTED_FOREGROUND};
    font-family: "{mono_family}";
    font-size: 10px;
}}

QLabel#sectionHeader {{
    color: {Colours.MUTED_FOREGROUND};
    font-size: 11px;
    font-weight: 600;
}}

QFrame#resultsSection,
QFrame#comparisonMatrix,
QFrame#summaryCard,
QFrame#resultCard {{
    background-color: {Colours.SURFACE_1};
    border: 1px solid {Colours.PANEL_BORDER};
    border-radius: 4px;
}}

QFrame#resultCard[alert="true"] {{
    border: 1px solid {rgba(Colours.WARNING, 0.38)};
}}

QFrame#resultCard[alert="true"] QLabel#metricCardValue {{
    color: {Colours.WARNING};
}}

QLabel#metricCardLabel,
QLabel#summaryFieldLabel,
QLabel#comparisonFieldLabel {{
    color: {Colours.MUTED_FOREGROUND};
    font-size: 10px;
}}

QLabel#metricCardValue {{
    font-family: "{mono_family}";
    font-size: 20px;
    font-weight: 600;
}}

QLabel#metricCardSubLabel,
QLabel#summaryCardSubLabel,
QLabel#warningCardMeta,
QLabel#emptyStateLabel {{
    color: {Colours.MUTED_FOREGROUND};
    font-size: 10px;
}}

QLabel#summaryCardTitle,
QLabel#warningCardTitle,
QLabel#comparisonColumnTitle {{
    color: {Colours.FOREGROUND};
    font-size: 12px;
    font-weight: 600;
}}

QLabel#summaryPhaseDot[phase="drogue"] {{
    color: {Colours.PHASE_DROGUE};
}}

QLabel#summaryPhaseDot[phase="main"] {{
    color: {Colours.PHASE_MAIN};
}}

QLabel#summaryPhaseDot[phase="freefall"] {{
    color: {Colours.PHASE_FREEFALL};
}}

QLabel#summaryFieldValue,
QLabel#comparisonValue {{
    font-family: "{mono_family}";
}}

QLabel#comparisonValue {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 6px 8px;
}}

QLabel#comparisonValue[changed="true"] {{
    background-color: {rgba(Colours.PRIMARY, 0.10)};
    border: 1px solid {rgba(Colours.PRIMARY, 0.22)};
}}

QLabel#comparisonMetricLabel {{
    color: {Colours.MUTED_FOREGROUND};
    font-size: 11px;
    padding: 6px 0;
}}

QFrame#warningCard {{
    border-radius: 4px;
    padding: 0;
}}

QFrame#warningCard[severity="error"] {{
    background-color: {rgba(Colours.DESTRUCTIVE, 0.08)};
    border: 1px solid {rgba(Colours.DESTRUCTIVE, 0.30)};
}}

QFrame#warningCard[severity="warning"] {{
    background-color: {rgba(Colours.WARNING, 0.08)};
    border: 1px solid {rgba(Colours.WARNING, 0.30)};
}}

QFrame#warningCard[severity="info"] {{
    background-color: {rgba(Colours.INFO, 0.08)};
    border: 1px solid {rgba(Colours.INFO, 0.22)};
}}

QFrame#warningCard[severity="error"] QLabel#warningCardIcon,
QFrame#warningCard[severity="error"] QLabel#warningCardTitle {{
    color: {Colours.DESTRUCTIVE};
}}

QFrame#warningCard[severity="warning"] QLabel#warningCardIcon,
QFrame#warningCard[severity="warning"] QLabel#warningCardTitle {{
    color: {Colours.WARNING};
}}

QFrame#warningCard[severity="info"] QLabel#warningCardIcon,
QFrame#warningCard[severity="info"] QLabel#warningCardTitle {{
    color: {Colours.INFO};
}}

QLabel#warningCardMessage {{
    color: {Colours.FOREGROUND};
}}

QFrame#sidebarSection {{
    background-color: {Colours.SURFACE_1};
    border: 1px solid {Colours.PANEL_BORDER};
    border-radius: 4px;
}}

QLabel#sidebarSectionTitle {{
    color: {Colours.MUTED_FOREGROUND};
    font-size: 11px;
    font-weight: 600;
}}

QLabel#sidebarSectionNote,
QLabel#timelineSummaryLabel,
QLabel#assumptionText,
QLabel#timelineEventNote {{
    color: {Colours.MUTED_FOREGROUND};
    font-size: 10px;
}}

QWidget#timelineContent,
QWidget#assumptionsList {{
    background: transparent;
}}

QFrame#timelineEvent {{
    background: transparent;
    border: none;
}}

QWidget#timelineRail {{
    background: transparent;
    min-width: 14px;
    max-width: 14px;
}}

QLabel#timelineDot {{
    font-size: 12px;
}}

QLabel#timelineDot[phase="drogue"] {{
    color: {Colours.PHASE_DROGUE};
}}

QLabel#timelineDot[phase="main"] {{
    color: {Colours.PHASE_MAIN};
}}

QLabel#timelineDot[phase="freefall"] {{
    color: {Colours.PHASE_FREEFALL};
}}

QFrame#timelineLine {{
    background-color: {Colours.PANEL_BORDER};
    border: none;
}}

QLabel#timelineMetaLabel {{
    color: {Colours.MUTED_FOREGROUND};
    font-size: 10px;
    font-family: "{mono_family}";
}}

QLabel#timelineEventLabel {{
    color: {Colours.FOREGROUND};
    font-size: 12px;
    font-weight: 600;
}}

QLabel#assumptionBullet {{
    color: {Colours.MUTED_FOREGROUND};
    font-family: "{mono_family}";
}}

QLabel[role="metricValue"],
QLabel[role="mono"] {{
    font-family: "{mono_family}";
}}

QLabel[role="metricValue"] {{
    font-size: 15px;
    font-weight: 600;
}}

QLineEdit,
QAbstractSpinBox {{
    background-color: {Colours.INPUT_BG};
    border: 1px solid {Colours.BORDER};
    border-radius: 3px;
    padding: 4px 6px;
    color: {Colours.FOREGROUND};
    font-family: "{mono_family}";
    font-size: 12px;
    selection-background-color: {rgba(Colours.PRIMARY, 0.22)};
    selection-color: {Colours.PRIMARY_FOREGROUND};
}}

QLineEdit:focus,
QAbstractSpinBox:focus,
QComboBox:focus {{
    border: 1px solid {Colours.PRIMARY};
}}

QLineEdit:disabled,
QAbstractSpinBox:disabled,
QComboBox:disabled {{
    color: {rgba(Colours.FOREGROUND, 0.55)};
    border-color: {rgba(Colours.BORDER, 0.7)};
}}

QComboBox {{
    background-color: {Colours.SURFACE_2};
    border: 1px solid {Colours.BORDER};
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 28px;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {Colours.SURFACE_1};
    border: 1px solid {Colours.BORDER};
    selection-background-color: {rgba(Colours.PRIMARY, 0.22)};
    selection-color: {Colours.FOREGROUND};
}}

QPushButton,
QToolButton {{
    background-color: {Colours.SURFACE_2};
    color: {Colours.FOREGROUND};
    border: 1px solid {Colours.BORDER};
    border-radius: 3px;
    padding: 6px 10px;
    min-height: 28px;
}}

QPushButton:hover,
QToolButton:hover {{
    background-color: {Colours.SURFACE_3};
}}

QPushButton:pressed,
QToolButton:pressed {{
    background-color: {Colours.SURFACE_0};
}}

QPushButton#analyseButton {{
    background-color: {Colours.PRIMARY};
    border: 1px solid {Colours.PRIMARY};
    color: {Colours.PRIMARY_FOREGROUND};
    font-weight: 600;
    min-height: 32px;
}}

QPushButton#analyseButton:hover {{
    background-color: {Colours.PRIMARY_HOVER};
}}

QCheckBox {{
    spacing: {SPACING.sm}px;
}}

QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid {Colours.BORDER};
    background-color: {Colours.INPUT_BG};
}}

QCheckBox::indicator:checked {{
    background-color: {Colours.PRIMARY};
    border-color: {Colours.PRIMARY};
}}

QTableWidget {{
    background-color: {Colours.SURFACE_1};
    border: 1px solid {Colours.BORDER};
    gridline-color: {Colours.PANEL_BORDER};
    color: {Colours.FOREGROUND};
    selection-background-color: {rgba(Colours.PRIMARY, 0.18)};
    selection-color: {Colours.FOREGROUND};
    font-family: "{mono_family}";
}}

QTableCornerButton::section {{
    background-color: {Colours.SURFACE_2};
    border: 1px solid {Colours.PANEL_BORDER};
}}

QTableWidget#phaseTable {{
    border-radius: 4px;
}}

QHeaderView::section {{
    background-color: {Colours.SURFACE_2};
    color: {Colours.MUTED_FOREGROUND};
    border: none;
    border-bottom: 1px solid {Colours.PANEL_BORDER};
    padding: 4px 8px;
    font-family: "{ui_family}";
    font-size: 11px;
    font-weight: 600;
}}

QTabWidget::pane {{
    border-top: 1px solid {Colours.PANEL_BORDER};
    top: -1px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {Colours.MUTED_FOREGROUND};
    padding: 10px 12px;
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:selected {{
    color: {Colours.PRIMARY};
    border-bottom: 2px solid {Colours.PRIMARY};
}}

QMenu {{
    background-color: {Colours.SURFACE_1};
    color: {Colours.FOREGROUND};
    border: 1px solid {Colours.BORDER};
    padding: 6px;
}}

QMenu::item:selected {{
    background-color: {Colours.SURFACE_3};
}}

QStatusBar {{
    background-color: {Colours.SURFACE_1};
    color: {Colours.MUTED_FOREGROUND};
    border-top: 1px solid {Colours.PANEL_BORDER};
}}
"""


def apply_theme(application: QtWidgets.QApplication | None) -> None:
    """Apply the shared DRIFT theme once per application instance."""

    if application is None:
        return
    if application.property("_drift_theme_applied"):
        return

    application.setStyle("Fusion")
    application.setPalette(build_palette())
    application.setFont(ui_font())
    application.setStyleSheet(build_stylesheet())
    application.setProperty("_drift_theme_applied", True)


__all__ = [
    "Colours",
    "SPACING",
    "SpacingScale",
    "apply_theme",
    "build_palette",
    "build_stylesheet",
    "configure_box_layout",
    "configure_form_layout",
    "configure_grid_layout",
    "mono_font",
    "qcolor",
    "rgba",
    "ui_font",
]
