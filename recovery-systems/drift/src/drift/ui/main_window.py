"""Main desktop shell for DRIFT."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from drift import APP_FULL_NAME, APP_WINDOW_NAME
from drift.models import (
    AltitudeInputs,
    AtmosphereSettings,
    Configuration,
    ParachuteSpec,
    Project,
    WindSettings,
)
from drift.services import AnalysisError, analyze_configuration, validate_configuration
from drift.services.export import save_configuration_markdown
from drift.services.persistence import load_catalogue, load_project, save_project
from drift.ui.panels import InputPanel, ResultsPanel
from drift.ui.theme import apply_theme
from drift.ui.visuals import VisualsPanel


class MainWindow(QtWidgets.QMainWindow):
    """Thin desktop shell that binds DRIFT models to the service layer."""

    def __init__(
        self,
        *,
        catalogue_path: str | Path | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        apply_theme(QtWidgets.QApplication.instance())
        self._catalogue_path = (
            Path(catalogue_path)
            if catalogue_path is not None
            else self.default_catalogue_path()
        )
        self._catalogue_items = []
        self._project: Project | None = None
        self._project_path: Path | None = None
        self._dirty = False

        self.setObjectName("mainWindow")
        self.setWindowTitle(APP_FULL_NAME)
        self.resize(1680, 940)

        self._build_ui()
        self._connect_signals()
        self._load_catalogue_items()
        self.new_project()

    @staticmethod
    def default_catalogue_path() -> Path:
        """Return the default catalogue path bundled with the repository."""

        return Path(__file__).resolve().parents[3] / "data" / "parachute_catalogue.json"

    def current_project(self) -> Project | None:
        """Return the current in-memory project."""

        return self._project

    def current_configuration(self) -> Configuration | None:
        """Return the currently active configuration, if one exists."""

        project = self._project
        if project is None or not project.configurations:
            return None

        active_id = project.active_configuration_id
        if active_id is not None:
            for configuration in project.configurations:
                if configuration.configuration_id == active_id:
                    return configuration

        project.active_configuration_id = project.configurations[0].configuration_id
        return project.configurations[0]

    def new_project(self) -> None:
        """Create a fresh in-memory DRIFT project."""

        timestamp = self._utc_timestamp()
        configuration = self._make_default_configuration("cfg_001", "Configuration 1")
        self._project = Project(
            project_id="proj_001",
            project_name="Untitled Project",
            description=None,
            created_at=timestamp,
            updated_at=timestamp,
            default_unit_system=configuration.display_unit_system,
            configurations=[configuration],
            active_configuration_id=configuration.configuration_id,
        )
        self._project_path = None
        self._dirty = False
        self._reload_ui_from_model()
        self.statusBar().showMessage("New DRIFT project created.", 3000)

    def open_project(self) -> None:
        """Open a project using a native file dialog."""

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open DRIFT Project",
            str(self._project_path.parent if self._project_path is not None else Path.cwd()),
            "DRIFT Project (*.json)",
        )
        if not file_path:
            return
        self.open_project_from_path(file_path)

    def open_project_from_path(self, path: str | Path) -> None:
        """Load a project from disk and refresh the shell."""

        project = load_project(path)
        self._project = project
        self._project_path = Path(path)
        self._ensure_active_configuration()
        self._dirty = False
        self._reload_ui_from_model()
        self.statusBar().showMessage(
            f"Loaded project from {self._project_path.name}.",
            3000,
        )

    def save_project_file(self) -> None:
        """Save the current project, prompting for a path if needed."""

        if self._project is None:
            return

        if self._project_path is None:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save DRIFT Project",
                str(Path.cwd() / "drift-project.json"),
                "DRIFT Project (*.json)",
            )
            if not file_path:
                return
            self.save_project_to_path(file_path)
            return

        self.save_project_to_path(self._project_path)

    def save_project_to_path(self, path: str | Path) -> Path:
        """Persist the current project to disk."""

        if self._project is None:
            raise RuntimeError("No project is loaded.")

        self._commit_dirty_draft()
        self._sync_project_metadata_from_panel(touch_updated_at=True)
        saved_path = save_project(self._project, path)
        self._project_path = saved_path
        self._dirty = False
        self._reload_ui_from_model()
        self.statusBar().showMessage(f"Saved project to {saved_path.name}.", 3000)
        return saved_path

    def create_configuration(self) -> None:
        """Append a new configuration to the current project."""

        project = self._project
        if project is None:
            self.new_project()
            return

        self._commit_dirty_draft()
        index = len(project.configurations) + 1
        configuration = self._make_default_configuration(
            f"cfg_{index:03d}",
            f"Configuration {index}",
            unit_system=project.default_unit_system,
        )
        project.configurations.append(configuration)
        project.active_configuration_id = configuration.configuration_id
        project.updated_at = self._utc_timestamp()
        self._dirty = False
        self._reload_ui_from_model()
        self.statusBar().showMessage(
            f"Created {configuration.configuration_name}.",
            3000,
        )

    def export_markdown_file(self) -> None:
        """Export the current configuration as a Markdown engineering summary."""

        project = self._project
        current = self.current_configuration()
        if project is None or current is None:
            return

        configuration = self.input_panel.build_configuration(current) if self._dirty else current
        project_name = self.input_panel.project_name() if self._dirty else project.project_name
        default_name = (
            f"{project_name.strip().replace(' ', '-').lower()}-"
            f"{configuration.configuration_name.strip().replace(' ', '-').lower()}.md"
        )
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export DRIFT Markdown Summary",
            str(Path.cwd() / default_name),
            "Markdown (*.md)",
        )
        if not file_path:
            return

        saved_path = save_configuration_markdown(
            project_name=project_name,
            configuration=configuration,
            catalogue_items=self._catalogue_items,
            path=file_path,
        )
        self.statusBar().showMessage(
            f"Exported Markdown summary to {saved_path.name}.",
            3000,
        )

    def analyze_current_configuration(self) -> None:
        """Validate and analyze the active configuration through the service layer."""

        project = self._project
        current = self.current_configuration()
        if project is None or current is None:
            return

        candidate = self.input_panel.build_configuration(current)
        validation_result = validate_configuration(candidate)
        if not validation_result.is_valid:
            self._replace_current_configuration(candidate)
            self._sync_project_metadata_from_panel(touch_updated_at=True)
            self._dirty = False
            self._reload_ui_from_model()
            self.statusBar().showMessage(
                f"Analysis blocked by {len(validation_result.issues)} validation issue(s).",
                5000,
            )
            return

        try:
            analyzed = analyze_configuration(candidate, self._catalogue_items)
        except AnalysisError as error:
            self._replace_current_configuration(candidate)
            self._sync_project_metadata_from_panel(touch_updated_at=True)
            self._dirty = False
            self._reload_ui_from_model()
            QtWidgets.QMessageBox.critical(self, "DRIFT Analysis Error", str(error))
            self.statusBar().showMessage(str(error), 5000)
            return

        self._replace_current_configuration(analyzed)
        self._sync_project_metadata_from_panel(touch_updated_at=True)
        self._dirty = False
        self._reload_ui_from_model()
        self.statusBar().showMessage("Analysis completed.", 3000)

    def _build_ui(self) -> None:
        self.input_panel = InputPanel(self)
        self.input_panel.setObjectName("leftPanel")
        self.input_panel.setMinimumWidth(300)
        self.results_panel = ResultsPanel(self)
        self.results_panel.setObjectName("centrePanel")
        self.results_panel.setMinimumWidth(400)
        self.visuals_panel = VisualsPanel(self)
        self.visuals_panel.setObjectName("rightPanel")
        self.visuals_panel.setMinimumWidth(260)

        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.addWidget(self.input_panel)
        self.main_splitter.addWidget(self.results_panel)
        self.main_splitter.addWidget(self.visuals_panel)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 0)
        self.main_splitter.setSizes([320, 840, 280])
        self.setCentralWidget(self.main_splitter)

        menu_bar = self.menuBar()
        menu_bar.setObjectName("topBar")
        menu_bar.setNativeMenuBar(False)
        file_menu = menu_bar.addMenu("&File")
        new_action = file_menu.addAction("New Project")
        open_action = file_menu.addAction("Open Project...")
        save_action = file_menu.addAction("Save Project")
        export_action = file_menu.addAction("Export Markdown...")
        file_menu.addSeparator()
        close_action = file_menu.addAction("Close Window")

        run_menu = menu_bar.addMenu("&Run")
        analyze_action = run_menu.addAction("Analyse")

        new_action.triggered.connect(self.new_project)
        open_action.triggered.connect(self.open_project)
        save_action.triggered.connect(self.save_project_file)
        export_action.triggered.connect(self.export_markdown_file)
        close_action.triggered.connect(self.close)
        analyze_action.triggered.connect(self.analyze_current_configuration)

        self.statusBar().setObjectName("statusBar")
        self.statusBar().showMessage("DRIFT desktop shell ready.")

    def _connect_signals(self) -> None:
        self.input_panel.new_project_requested.connect(self.new_project)
        self.input_panel.open_project_requested.connect(self.open_project)
        self.input_panel.save_project_requested.connect(self.save_project_file)
        self.input_panel.new_configuration_requested.connect(self.create_configuration)
        self.input_panel.configuration_selected.connect(self._on_configuration_selected)
        self.input_panel.analyze_requested.connect(self.analyze_current_configuration)
        self.input_panel.draft_changed.connect(self._on_draft_changed)

    def _load_catalogue_items(self) -> None:
        self._catalogue_items = load_catalogue(self._catalogue_path)
        self.results_panel.set_catalogue_items(self._catalogue_items)

    def _reload_ui_from_model(self) -> None:
        project = self._project
        current = self.current_configuration()

        if project is not None:
            self.input_panel.set_project(project)
            if current is not None:
                self.input_panel.load_configuration(current)

        self._refresh_output_panels()
        self._update_window_title()

    def _refresh_output_panels(self) -> None:
        project = self._project
        current = self.current_configuration()

        if self._dirty and current is not None:
            display_configuration = self.input_panel.build_configuration(current)
            validation_issues = []
        else:
            display_configuration = current
            validation_issues = self._validation_issues_for_configuration(current)

        unit_system = (
            display_configuration.display_unit_system
            if display_configuration is not None
            else (project.default_unit_system if project is not None else "si")
        )
        self.results_panel.set_catalogue_items(self._catalogue_items)
        self.results_panel.set_project(project, unit_system=unit_system)
        self.results_panel.show_configuration(
            display_configuration,
            validation_issues=validation_issues,
            dirty=self._dirty,
        )
        self.visuals_panel.show_configuration(
            display_configuration,
            validation_issues=validation_issues,
            dirty=self._dirty,
        )

    def _update_window_title(self) -> None:
        if self._project is None:
            self.setWindowTitle(APP_WINDOW_NAME)
            return

        title_parts = [self._project.project_name or "Untitled Project"]
        if self._project_path is not None:
            title_parts.append(self._project_path.name)
        title_parts.append(APP_WINDOW_NAME)
        title = " - ".join(title_parts)
        if self._dirty:
            title = f"{title} *"
        self.setWindowTitle(title)

    def _on_configuration_selected(self, configuration_id: str) -> None:
        project = self._project
        if project is None:
            return

        self._commit_dirty_draft()
        project.active_configuration_id = configuration_id
        self._reload_ui_from_model()

    def _on_draft_changed(self) -> None:
        self._dirty = True
        self._refresh_output_panels()
        self._update_window_title()

    def _commit_dirty_draft(self) -> None:
        current = self.current_configuration()
        if not self._dirty or current is None:
            self._sync_project_metadata_from_panel()
            return

        draft = self.input_panel.build_configuration(current)
        self._replace_current_configuration(draft)
        self._sync_project_metadata_from_panel(touch_updated_at=True)
        self._dirty = False

    def _replace_current_configuration(self, configuration: Configuration) -> None:
        project = self._project
        if project is None:
            return

        for index, existing in enumerate(project.configurations):
            if existing.configuration_id == configuration.configuration_id:
                project.configurations[index] = configuration
                break
        else:
            project.configurations.append(configuration)
        project.active_configuration_id = configuration.configuration_id

    def _sync_project_metadata_from_panel(self, *, touch_updated_at: bool = False) -> None:
        project = self._project
        if project is None:
            return

        project.project_name = self.input_panel.project_name()
        current = self.current_configuration()
        if current is not None:
            project.default_unit_system = current.display_unit_system
        if touch_updated_at:
            project.updated_at = self._utc_timestamp()

    def _ensure_active_configuration(self) -> None:
        project = self._project
        if project is None:
            return

        active_id = project.active_configuration_id
        if active_id is not None:
            for configuration in project.configurations:
                if configuration.configuration_id == active_id:
                    return

        project.active_configuration_id = (
            project.configurations[0].configuration_id if project.configurations else None
        )

    def _validation_issues_for_configuration(self, configuration: Configuration | None):
        if configuration is None:
            return []
        return validate_configuration(configuration).issues

    def _make_default_configuration(
        self,
        configuration_id: str,
        configuration_name: str,
        *,
        unit_system: str = "si",
    ) -> Configuration:
        return Configuration(
            configuration_id=configuration_id,
            configuration_name=configuration_name,
            recovery_mode="single",
            rocket_mass_kg=10.0,
            safety_margin_fraction=0.1,
            display_unit_system=unit_system,
            atmosphere_settings=AtmosphereSettings(mode="standard_atmosphere"),
            wind_settings=WindSettings(mode="constant", constant_wind_mps=5.0),
            altitude_inputs=AltitudeInputs(
                deployment_altitude_m=500.0,
                apogee_altitude_m=1200.0,
            ),
            parachutes=[
                ParachuteSpec(
                    parachute_id=f"{configuration_id}_single",
                    role="single",
                    family="hemispherical",
                    cd=1.5,
                    cd_source="preset",
                    target_descent_velocity_mps=6.0,
                )
            ],
            analysis_results=None,
            warnings=[],
        )

    @staticmethod
    def _utc_timestamp() -> str:
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )


def main() -> int:
    """Run the DRIFT desktop shell."""

    app = QtWidgets.QApplication.instance()
    owns_application = app is None
    if app is None:
        app = QtWidgets.QApplication([])
        apply_theme(app)
        app.setApplicationDisplayName(APP_FULL_NAME)
        app.setWindowIcon(QtGui.QIcon())

    window = MainWindow()
    window.show()
    if owns_application:
        return app.exec()
    return 0


__all__ = ["MainWindow", "main"]
