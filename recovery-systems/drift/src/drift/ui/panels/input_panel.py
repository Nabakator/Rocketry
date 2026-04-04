"""Left-panel project and configuration inputs for the DRIFT desktop shell."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from drift.models import (
    AltitudeInputs,
    AtmosphereSettings,
    Configuration,
    ParachuteSpec,
    Project,
    WindSettings,
)

from drift.ui.display_units import (
    density_from_si,
    density_to_si,
    density_unit_label,
    length_from_si,
    length_to_si,
    length_unit_label,
    mass_from_si,
    mass_to_si,
    mass_unit_label,
    velocity_from_si,
    velocity_to_si,
    velocity_unit_label,
)
from drift.ui.theme import SPACING, configure_box_layout, configure_form_layout, configure_grid_layout

RECOVERY_MODE_ITEMS = [("single", "Single"), ("dual", "Dual")]
UNIT_SYSTEM_ITEMS = [("si", "SI"), ("imperial", "Imperial")]
ATMOSPHERE_MODE_ITEMS = [
    ("standard_atmosphere", "Standard atmosphere"),
    ("manual_density", "Manual density override"),
]
WIND_MODE_ITEMS = [("constant", "Constant wind"), ("two_layer", "Two-layer wind")]
CD_SOURCE_ITEMS = [("preset", "Preset"), ("manual_override", "Manual override")]
PARACHUTE_FAMILY_ITEMS = [
    ("flat_circular", "Flat Circular"),
    ("hemispherical", "Hemispherical"),
    ("toroidal", "Toroidal"),
    ("cruciform", "Cruciform / Cross"),
    ("ribbon", "Ribbon"),
    ("streamer", "Streamer"),
]


class InputPanel(QtWidgets.QWidget):
    """Editable project and configuration input panel."""

    new_project_requested = QtCore.Signal()
    open_project_requested = QtCore.Signal()
    save_project_requested = QtCore.Signal()
    new_configuration_requested = QtCore.Signal()
    configuration_selected = QtCore.Signal(str)
    analyze_requested = QtCore.Signal()
    draft_changed = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._loading = False
        self._unit_system = "si"
        self._build_ui()
        self._connect_signals()
        self._update_recovery_mode_ui(self.recovery_mode_combo.currentData())
        self._update_atmosphere_mode_ui(self.atmosphere_mode_combo.currentData())
        self._update_wind_mode_ui(self.wind_mode_combo.currentData())
        self._apply_unit_suffixes(self._unit_system)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        configure_box_layout(layout, margins=(0, 0, 0, 0), spacing=0)

        self.project_actions_widget = QtWidgets.QWidget()
        self.project_actions_widget.hide()
        button_row = QtWidgets.QHBoxLayout(self.project_actions_widget)
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(SPACING.sm)
        self.new_project_button = QtWidgets.QPushButton("New")
        self.open_project_button = QtWidgets.QPushButton("Open")
        self.save_project_button = QtWidgets.QPushButton("Save")
        button_row.addWidget(self.new_project_button)
        button_row.addWidget(self.open_project_button)
        button_row.addWidget(self.save_project_button)
        layout.addWidget(self.project_actions_widget)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        layout.addWidget(scroll_area, 1)

        content = QtWidgets.QWidget()
        scroll_area.setWidget(content)
        content_layout = QtWidgets.QVBoxLayout(content)
        configure_box_layout(content_layout, margins=(SPACING.lg, SPACING.md, SPACING.lg, SPACING.lg))

        project_box = QtWidgets.QGroupBox("PROJECT")
        project_form = QtWidgets.QFormLayout(project_box)
        configure_form_layout(project_form)
        self.project_name_edit = QtWidgets.QLineEdit()
        project_form.addRow("Project name", self.project_name_edit)
        content_layout.addWidget(project_box)

        configuration_box = QtWidgets.QGroupBox("CONFIGURATION")
        configuration_layout = QtWidgets.QVBoxLayout(configuration_box)
        configure_box_layout(configuration_layout)
        self.configuration_combo = QtWidgets.QComboBox()
        self.configuration_combo.hide()
        self.configuration_button_group = QtWidgets.QButtonGroup(self)
        self.configuration_button_group.setExclusive(True)
        self.configuration_tab_buttons: dict[str, QtWidgets.QPushButton] = {}
        self.configuration_tabs_widget = QtWidgets.QWidget()
        self.configuration_tabs_layout = QtWidgets.QHBoxLayout(self.configuration_tabs_widget)
        self.configuration_tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.configuration_tabs_layout.setSpacing(SPACING.xs)
        configuration_layout.addWidget(self.configuration_tabs_widget)

        configuration_form = QtWidgets.QFormLayout()
        configure_form_layout(configuration_form, margins=(0, 0, 0, 0))
        self.new_configuration_button = QtWidgets.QPushButton("+")
        self.new_configuration_button.setObjectName("configAddButton")
        self.configuration_name_edit = QtWidgets.QLineEdit()
        self.display_unit_combo = QtWidgets.QComboBox()
        for value, label in UNIT_SYSTEM_ITEMS:
            self.display_unit_combo.addItem(label, value)
        configuration_form.addRow("Name", self.configuration_name_edit)
        configuration_form.addRow("Units", self.display_unit_combo)
        configuration_layout.addLayout(configuration_form)
        content_layout.addWidget(configuration_box)

        deployment_box = QtWidgets.QGroupBox("DEPLOYMENT TYPE")
        deployment_layout = QtWidgets.QVBoxLayout(deployment_box)
        configure_box_layout(deployment_layout)
        self.recovery_mode_combo = QtWidgets.QComboBox()
        self.recovery_mode_combo.hide()
        for value, label in RECOVERY_MODE_ITEMS:
            self.recovery_mode_combo.addItem(label, value)
        segmented_widget = QtWidgets.QWidget()
        segmented_widget.setObjectName("segmentedControl")
        segmented_layout = QtWidgets.QHBoxLayout(segmented_widget)
        segmented_layout.setContentsMargins(2, 2, 2, 2)
        segmented_layout.setSpacing(2)
        self.single_mode_button = QtWidgets.QPushButton("Single")
        self.single_mode_button.setObjectName("modeToggleButton")
        self.single_mode_button.setCheckable(True)
        self.dual_mode_button = QtWidgets.QPushButton("Dual")
        self.dual_mode_button.setObjectName("modeToggleButton")
        self.dual_mode_button.setCheckable(True)
        self.recovery_mode_button_group = QtWidgets.QButtonGroup(self)
        self.recovery_mode_button_group.setExclusive(True)
        self.recovery_mode_button_group.addButton(self.single_mode_button)
        self.recovery_mode_button_group.addButton(self.dual_mode_button)
        segmented_layout.addWidget(self.single_mode_button)
        segmented_layout.addWidget(self.dual_mode_button)
        deployment_layout.addWidget(segmented_widget)
        self.deployment_helper_label = QtWidgets.QLabel()
        self.deployment_helper_label.setObjectName("deploymentHelper")
        self.deployment_helper_label.setWordWrap(True)
        deployment_layout.addWidget(self.deployment_helper_label)
        content_layout.addWidget(deployment_box)

        general_box = QtWidgets.QGroupBox("ROCKET")
        general_form = QtWidgets.QFormLayout(general_box)
        configure_form_layout(general_form)
        self.mass_spin = self._double_spin(0.001, 100000.0, 3, 0.5)
        self.safety_margin_spin = self._double_spin(0.0, 10.0, 3, 0.05)
        general_form.addRow("Mass", self.mass_spin)
        general_form.addRow("Safety margin", self.safety_margin_spin)
        content_layout.addWidget(general_box)

        altitude_box = QtWidgets.QGroupBox("RECOVERY ALTITUDES")
        altitude_layout = QtWidgets.QVBoxLayout(altitude_box)
        configure_box_layout(altitude_layout)
        self.altitude_stack = QtWidgets.QStackedWidget()
        altitude_layout.addWidget(self.altitude_stack)

        single_altitudes = QtWidgets.QWidget()
        single_form = QtWidgets.QFormLayout(single_altitudes)
        configure_form_layout(single_form)
        self.single_deployment_altitude_spin = self._double_spin(0.0, 100000.0, 2, 10.0)
        self.single_apogee_checkbox = QtWidgets.QCheckBox("Apogee known")
        self.single_apogee_spin = self._double_spin(0.0, 100000.0, 2, 10.0)
        single_form.addRow("Deployment altitude", self.single_deployment_altitude_spin)
        single_form.addRow(self.single_apogee_checkbox, self.single_apogee_spin)
        self.altitude_stack.addWidget(single_altitudes)

        dual_altitudes = QtWidgets.QWidget()
        dual_form = QtWidgets.QFormLayout(dual_altitudes)
        configure_form_layout(dual_form)
        self.dual_apogee_checkbox = QtWidgets.QCheckBox("Apogee known")
        self.dual_apogee_spin = self._double_spin(0.0, 100000.0, 2, 10.0)
        self.dual_drogue_altitude_spin = self._double_spin(0.0, 100000.0, 2, 10.0)
        self.dual_main_altitude_spin = self._double_spin(0.0, 100000.0, 2, 10.0)
        dual_form.addRow(self.dual_apogee_checkbox, self.dual_apogee_spin)
        dual_form.addRow("Drogue deployment altitude", self.dual_drogue_altitude_spin)
        dual_form.addRow("Main deployment altitude", self.dual_main_altitude_spin)
        self.altitude_stack.addWidget(dual_altitudes)
        content_layout.addWidget(altitude_box)

        self.parachute_stack = QtWidgets.QStackedWidget()
        self.single_parachute_group = self._build_parachute_group("MAIN")
        self.dual_parachute_page = QtWidgets.QWidget()
        dual_page_layout = QtWidgets.QVBoxLayout(self.dual_parachute_page)
        configure_box_layout(dual_page_layout, margins=(0, 0, 0, 0))
        self.drogue_parachute_group = self._build_parachute_group("DROGUE")
        self.main_parachute_group = self._build_parachute_group("MAIN")
        dual_page_layout.addWidget(self.drogue_parachute_group["box"])
        dual_page_layout.addWidget(self.main_parachute_group["box"])
        dual_page_layout.addStretch(1)
        self.parachute_stack.addWidget(self.single_parachute_group["box"])
        self.parachute_stack.addWidget(self.dual_parachute_page)
        content_layout.addWidget(self.parachute_stack)

        atmosphere_box = QtWidgets.QGroupBox("ATMOSPHERE")
        atmosphere_layout = QtWidgets.QVBoxLayout(atmosphere_box)
        configure_box_layout(atmosphere_layout)
        atmosphere_form = QtWidgets.QFormLayout()
        configure_form_layout(atmosphere_form, margins=(0, 0, 0, 0))
        self.atmosphere_mode_combo = QtWidgets.QComboBox()
        for value, label in ATMOSPHERE_MODE_ITEMS:
            self.atmosphere_mode_combo.addItem(label, value)
        self.manual_density_spin = self._double_spin(0.0001, 100.0, 4, 0.01)
        atmosphere_form.addRow("Mode", self.atmosphere_mode_combo)
        atmosphere_form.addRow("Manual density", self.manual_density_spin)
        atmosphere_layout.addLayout(atmosphere_form)
        self.atmosphere_helper_label = QtWidgets.QLabel(
            "Air density is taken from the ISA model unless a manual override is active."
        )
        self.atmosphere_helper_label.setObjectName("atmosphereHelper")
        self.atmosphere_helper_label.setWordWrap(True)
        atmosphere_layout.addWidget(self.atmosphere_helper_label)
        content_layout.addWidget(atmosphere_box)

        wind_box = QtWidgets.QGroupBox("WIND / DRIFT ESTIMATE")
        wind_layout = QtWidgets.QVBoxLayout(wind_box)
        configure_box_layout(wind_layout)
        wind_form = QtWidgets.QFormLayout()
        configure_form_layout(wind_form, margins=(0, 0, 0, 0))
        self.wind_mode_combo = QtWidgets.QComboBox()
        for value, label in WIND_MODE_ITEMS:
            self.wind_mode_combo.addItem(label, value)
        self.constant_wind_spin = self._double_spin(0.0, 1000.0, 3, 0.5)
        self.aloft_wind_spin = self._double_spin(0.0, 1000.0, 3, 0.5)
        self.ground_wind_spin = self._double_spin(0.0, 1000.0, 3, 0.5)
        wind_form.addRow("Mode", self.wind_mode_combo)
        wind_form.addRow("Constant wind", self.constant_wind_spin)
        wind_form.addRow("Aloft wind", self.aloft_wind_spin)
        wind_form.addRow("Ground wind", self.ground_wind_spin)
        wind_layout.addLayout(wind_form)
        self.wind_helper_label = QtWidgets.QLabel(
            "Drift is a first-order estimate based on wind speed and vertical descent only."
        )
        self.wind_helper_label.setObjectName("windHelper")
        self.wind_helper_label.setWordWrap(True)
        wind_layout.addWidget(self.wind_helper_label)
        content_layout.addWidget(wind_box)

        self.note_label = QtWidgets.QLabel(
            "Values are edited in the desktop shell and stored internally in SI units."
        )
        self.note_label.setProperty("role", "helper")
        self.note_label.setWordWrap(True)
        content_layout.addWidget(self.note_label)
        content_layout.addStretch(1)

        self.footer_widget = QtWidgets.QWidget()
        self.footer_widget.setObjectName("leftPanelFooter")
        footer_layout = QtWidgets.QVBoxLayout(self.footer_widget)
        configure_box_layout(footer_layout, margins=(SPACING.lg, SPACING.md, SPACING.lg, SPACING.lg))
        self.panel_state_label = QtWidgets.QLabel("Inputs are valid. Analyse to update the results.")
        self.panel_state_label.setObjectName("panelStateLabel")
        self.panel_state_label.setProperty("state", "valid")
        self.panel_state_label.setWordWrap(True)
        footer_layout.addWidget(self.panel_state_label)
        self.analyze_button = QtWidgets.QPushButton("Analyse")
        self.analyze_button.setObjectName("analyseButton")
        self.analyze_button.setDefault(True)
        footer_layout.addWidget(self.analyze_button)
        layout.addWidget(self.footer_widget)

    def _connect_signals(self) -> None:
        self.new_project_button.clicked.connect(self.new_project_requested)
        self.open_project_button.clicked.connect(self.open_project_requested)
        self.save_project_button.clicked.connect(self.save_project_requested)
        self.new_configuration_button.clicked.connect(self.new_configuration_requested)
        self.analyze_button.clicked.connect(self.analyze_requested)
        self.configuration_combo.currentIndexChanged.connect(self._emit_configuration_selected)
        self.single_mode_button.clicked.connect(lambda: self._set_recovery_mode("single"))
        self.dual_mode_button.clicked.connect(lambda: self._set_recovery_mode("dual"))
        self.recovery_mode_combo.currentIndexChanged.connect(self._on_recovery_mode_changed)
        self.atmosphere_mode_combo.currentIndexChanged.connect(self._on_atmosphere_mode_changed)
        self.wind_mode_combo.currentIndexChanged.connect(self._on_wind_mode_changed)
        self.display_unit_combo.currentIndexChanged.connect(self._on_display_unit_changed)

        draft_widgets = [
            self.project_name_edit,
            self.configuration_name_edit,
            self.mass_spin,
            self.safety_margin_spin,
            self.manual_density_spin,
            self.constant_wind_spin,
            self.aloft_wind_spin,
            self.ground_wind_spin,
            self.single_deployment_altitude_spin,
            self.single_apogee_spin,
            self.dual_apogee_spin,
            self.dual_drogue_altitude_spin,
            self.dual_main_altitude_spin,
            self.single_apogee_checkbox,
            self.dual_apogee_checkbox,
            self.display_unit_combo,
            self.recovery_mode_combo,
            self.atmosphere_mode_combo,
            self.wind_mode_combo,
            self.single_parachute_group["family"],
            self.single_parachute_group["cd_source"],
            self.single_parachute_group["cd"],
            self.single_parachute_group["target_velocity"],
            self.drogue_parachute_group["family"],
            self.drogue_parachute_group["cd_source"],
            self.drogue_parachute_group["cd"],
            self.drogue_parachute_group["target_velocity"],
            self.main_parachute_group["family"],
            self.main_parachute_group["cd_source"],
            self.main_parachute_group["cd"],
            self.main_parachute_group["target_velocity"],
        ]
        for widget in draft_widgets:
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.textEdited.connect(self._emit_draft_changed)
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.toggled.connect(self._emit_draft_changed)
                widget.toggled.connect(self._sync_optional_state)
            elif isinstance(widget, QtWidgets.QComboBox):
                widget.currentIndexChanged.connect(self._emit_draft_changed)
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                widget.valueChanged.connect(self._emit_draft_changed)

    def _double_spin(
        self,
        minimum: float,
        maximum: float,
        decimals: int,
        step: float,
    ) -> QtWidgets.QDoubleSpinBox:
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setSingleStep(step)
        spin.setAlignment(QtCore.Qt.AlignRight)
        spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        spin.setMinimumWidth(132)
        return spin

    def _build_parachute_group(self, title: str) -> dict[str, object]:
        box = QtWidgets.QGroupBox(title)
        form = QtWidgets.QFormLayout(box)
        configure_form_layout(form)
        family_combo = QtWidgets.QComboBox()
        for value, label in PARACHUTE_FAMILY_ITEMS:
            family_combo.addItem(label, value)
        cd_source_combo = QtWidgets.QComboBox()
        for value, label in CD_SOURCE_ITEMS:
            cd_source_combo.addItem(label, value)
        cd_spin = self._double_spin(0.001, 20.0, 3, 0.05)
        target_velocity_spin = self._double_spin(0.001, 1000.0, 3, 0.5)
        form.addRow("Family", family_combo)
        form.addRow("Cd source", cd_source_combo)
        form.addRow("Cd", cd_spin)
        form.addRow("Target descent rate", target_velocity_spin)
        return {
            "box": box,
            "family": family_combo,
            "cd_source": cd_source_combo,
            "cd": cd_spin,
            "target_velocity": target_velocity_spin,
        }

    def set_project(self, project: Project) -> None:
        self._loading = True
        try:
            self.project_name_edit.setText(project.project_name)
            self.configuration_combo.clear()
            for configuration in project.configurations:
                self.configuration_combo.addItem(
                    configuration.configuration_name,
                    configuration.configuration_id,
                )
            active_id = project.active_configuration_id
            active_index = 0
            if active_id is not None:
                for index in range(self.configuration_combo.count()):
                    if self.configuration_combo.itemData(index) == active_id:
                        active_index = index
                        break
            self.configuration_combo.setCurrentIndex(active_index)
            self._rebuild_configuration_tabs()
        finally:
            self._loading = False

    def load_configuration(self, configuration: Configuration) -> None:
        self._loading = True
        try:
            self.configuration_name_edit.setText(configuration.configuration_name)
            self._set_combo_data(self.display_unit_combo, configuration.display_unit_system)
            self._unit_system = configuration.display_unit_system
            self._apply_unit_suffixes(self._unit_system)
            self._set_combo_data(self.recovery_mode_combo, configuration.recovery_mode)
            self.mass_spin.setValue(mass_from_si(configuration.rocket_mass_kg, self._unit_system))
            self.safety_margin_spin.setValue(configuration.safety_margin_fraction)

            self._set_combo_data(
                self.atmosphere_mode_combo,
                configuration.atmosphere_settings.mode,
            )
            density_value = configuration.atmosphere_settings.manual_density_kg_per_m3
            self.manual_density_spin.setValue(
                0.0 if density_value is None else density_from_si(density_value, self._unit_system)
            )

            self._set_combo_data(self.wind_mode_combo, configuration.wind_settings.mode)
            self.constant_wind_spin.setValue(
                0.0
                if configuration.wind_settings.constant_wind_mps is None
                else velocity_from_si(configuration.wind_settings.constant_wind_mps, self._unit_system)
            )
            self.aloft_wind_spin.setValue(
                0.0
                if configuration.wind_settings.aloft_wind_mps is None
                else velocity_from_si(configuration.wind_settings.aloft_wind_mps, self._unit_system)
            )
            self.ground_wind_spin.setValue(
                0.0
                if configuration.wind_settings.ground_wind_mps is None
                else velocity_from_si(configuration.wind_settings.ground_wind_mps, self._unit_system)
            )

            self.single_deployment_altitude_spin.setValue(
                0.0
                if configuration.altitude_inputs.deployment_altitude_m is None
                else length_from_si(configuration.altitude_inputs.deployment_altitude_m, self._unit_system)
            )
            self.single_apogee_checkbox.setChecked(
                configuration.altitude_inputs.apogee_altitude_m is not None
                and configuration.recovery_mode == "single"
            )
            self.single_apogee_spin.setValue(
                0.0
                if configuration.altitude_inputs.apogee_altitude_m is None
                else length_from_si(configuration.altitude_inputs.apogee_altitude_m, self._unit_system)
            )

            self.dual_apogee_checkbox.setChecked(
                configuration.altitude_inputs.apogee_altitude_m is not None
                and configuration.recovery_mode == "dual"
            )
            self.dual_apogee_spin.setValue(
                0.0
                if configuration.altitude_inputs.apogee_altitude_m is None
                else length_from_si(configuration.altitude_inputs.apogee_altitude_m, self._unit_system)
            )
            self.dual_drogue_altitude_spin.setValue(
                0.0
                if configuration.altitude_inputs.drogue_deployment_altitude_m is None
                else length_from_si(configuration.altitude_inputs.drogue_deployment_altitude_m, self._unit_system)
            )
            self.dual_main_altitude_spin.setValue(
                0.0
                if configuration.altitude_inputs.main_deployment_altitude_m is None
                else length_from_si(configuration.altitude_inputs.main_deployment_altitude_m, self._unit_system)
            )

            parachute_lookup = {parachute.role: parachute for parachute in configuration.parachutes}
            self._load_parachute_group(self.single_parachute_group, parachute_lookup.get("single"))
            self._load_parachute_group(self.drogue_parachute_group, parachute_lookup.get("drogue"))
            self._load_parachute_group(self.main_parachute_group, parachute_lookup.get("main"))

            self._update_recovery_mode_ui(configuration.recovery_mode)
            self._update_atmosphere_mode_ui(configuration.atmosphere_settings.mode)
            self._update_wind_mode_ui(configuration.wind_settings.mode)
            self._sync_optional_state()
            self._rebuild_configuration_tabs()
        finally:
            self._loading = False

    def build_configuration(
        self,
        existing_configuration: Configuration | None,
    ) -> Configuration:
        unit_system = self.display_unit_combo.currentData()
        configuration_id = (
            existing_configuration.configuration_id
            if existing_configuration is not None
            else "cfg_001"
        )
        recovery_mode = self.recovery_mode_combo.currentData()
        atmosphere_mode = self.atmosphere_mode_combo.currentData()
        wind_mode = self.wind_mode_combo.currentData()

        apogee_altitude_single = (
            length_to_si(self.single_apogee_spin.value(), unit_system)
            if self.single_apogee_checkbox.isChecked()
            else None
        )
        apogee_altitude_dual = (
            length_to_si(self.dual_apogee_spin.value(), unit_system)
            if self.dual_apogee_checkbox.isChecked()
            else None
        )
        altitude_inputs = AltitudeInputs(
            deployment_altitude_m=(
                length_to_si(self.single_deployment_altitude_spin.value(), unit_system)
                if recovery_mode == "single"
                else None
            ),
            apogee_altitude_m=(
                apogee_altitude_single if recovery_mode == "single" else apogee_altitude_dual
            ),
            drogue_deployment_altitude_m=(
                length_to_si(self.dual_drogue_altitude_spin.value(), unit_system)
                if recovery_mode == "dual"
                else None
            ),
            main_deployment_altitude_m=(
                length_to_si(self.dual_main_altitude_spin.value(), unit_system)
                if recovery_mode == "dual"
                else None
            ),
        )

        parachutes: list[ParachuteSpec] = []
        if recovery_mode == "single":
            parachutes.append(
                self._build_parachute_spec(
                    self.single_parachute_group,
                    existing_configuration,
                    role="single",
                    configuration_id=configuration_id,
                    unit_system=unit_system,
                )
            )
        else:
            parachutes.append(
                self._build_parachute_spec(
                    self.drogue_parachute_group,
                    existing_configuration,
                    role="drogue",
                    configuration_id=configuration_id,
                    unit_system=unit_system,
                )
            )
            parachutes.append(
                self._build_parachute_spec(
                    self.main_parachute_group,
                    existing_configuration,
                    role="main",
                    configuration_id=configuration_id,
                    unit_system=unit_system,
                )
            )

        manual_density = (
            density_to_si(self.manual_density_spin.value(), unit_system)
            if atmosphere_mode == "manual_density"
            else None
        )
        wind_settings = WindSettings(
            mode=wind_mode,
            constant_wind_mps=(
                velocity_to_si(self.constant_wind_spin.value(), unit_system)
                if wind_mode == "constant"
                else None
            ),
            aloft_wind_mps=(
                velocity_to_si(self.aloft_wind_spin.value(), unit_system)
                if wind_mode == "two_layer"
                else None
            ),
            ground_wind_mps=(
                velocity_to_si(self.ground_wind_spin.value(), unit_system)
                if wind_mode == "two_layer"
                else None
            ),
        )
        return Configuration(
            configuration_id=configuration_id,
            configuration_name=self.configuration_name_edit.text().strip() or configuration_id,
            recovery_mode=recovery_mode,
            rocket_mass_kg=mass_to_si(self.mass_spin.value(), unit_system),
            safety_margin_fraction=self.safety_margin_spin.value(),
            display_unit_system=unit_system,
            atmosphere_settings=AtmosphereSettings(
                mode=atmosphere_mode,
                manual_density_kg_per_m3=manual_density,
            ),
            wind_settings=wind_settings,
            altitude_inputs=altitude_inputs,
            parachutes=parachutes,
            analysis_results=None,
            warnings=[],
        )

    def project_name(self) -> str:
        return self.project_name_edit.text().strip() or "Untitled project"

    def set_state_hint(self, state_key: str, message: str) -> None:
        """Update the footer state hint using existing shell state."""

        self.panel_state_label.setText(message)
        self.panel_state_label.setProperty("state", state_key)
        self.style().unpolish(self.panel_state_label)
        self.style().polish(self.panel_state_label)

    def _build_parachute_spec(
        self,
        group: dict[str, object],
        existing_configuration: Configuration | None,
        *,
        role: str,
        configuration_id: str,
        unit_system: str,
    ) -> ParachuteSpec:
        existing_id = None
        if existing_configuration is not None:
            for parachute in existing_configuration.parachutes:
                if parachute.role == role:
                    existing_id = parachute.parachute_id
                    break
        parachute_id = existing_id or f"{configuration_id}_{role}"
        return ParachuteSpec(
            parachute_id=parachute_id,
            role=role,
            family=group["family"].currentData(),
            cd=group["cd"].value(),
            cd_source=group["cd_source"].currentData(),
            target_descent_velocity_mps=velocity_to_si(
                group["target_velocity"].value(),
                unit_system,
            ),
        )

    def _load_parachute_group(
        self,
        group: dict[str, object],
        parachute: ParachuteSpec | None,
    ) -> None:
        if parachute is None:
            self._set_combo_data(group["family"], "hemispherical")
            self._set_combo_data(group["cd_source"], "preset")
            group["cd"].setValue(1.5)
            group["target_velocity"].setValue(velocity_from_si(6.0, self._unit_system))
            return

        self._set_combo_data(group["family"], parachute.family)
        self._set_combo_data(group["cd_source"], parachute.cd_source)
        group["cd"].setValue(parachute.cd)
        group["target_velocity"].setValue(
            velocity_from_si(parachute.target_descent_velocity_mps, self._unit_system)
        )

    def _set_combo_data(self, combo: QtWidgets.QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _rebuild_configuration_tabs(self) -> None:
        for button in self.configuration_button_group.buttons():
            self.configuration_button_group.removeButton(button)
        while self.configuration_tabs_layout.count():
            item = self.configuration_tabs_layout.takeAt(0)
            widget = item.widget()
            if widget is not None and widget is not self.new_configuration_button:
                widget.deleteLater()

        self.configuration_tab_buttons.clear()
        checked_id = self.configuration_combo.currentData()
        for index in range(self.configuration_combo.count()):
            configuration_name = self.configuration_combo.itemText(index)
            configuration_id = self.configuration_combo.itemData(index)
            button = QtWidgets.QPushButton(configuration_name)
            button.setObjectName("configTabButton")
            button.setCheckable(True)
            button.setChecked(configuration_id == checked_id)
            button.clicked.connect(
                lambda _checked=False, config_id=configuration_id: self._activate_configuration_tab(
                    config_id
                )
            )
            self.configuration_tabs_layout.addWidget(button, 1)
            self.configuration_button_group.addButton(button)
            self.configuration_tab_buttons[configuration_id] = button

        self.configuration_tabs_layout.addWidget(self.new_configuration_button, 0)

    def _activate_configuration_tab(self, configuration_id: str) -> None:
        if self._loading:
            return
        index = self.configuration_combo.findData(configuration_id)
        if index >= 0 and index != self.configuration_combo.currentIndex():
            self.configuration_combo.setCurrentIndex(index)

    def _set_recovery_mode(self, mode: str) -> None:
        self._set_combo_data(self.recovery_mode_combo, mode)

    def _emit_configuration_selected(self) -> None:
        if self._loading:
            return
        config_id = self.configuration_combo.currentData()
        if config_id is not None:
            self.configuration_selected.emit(config_id)

    def _emit_draft_changed(self) -> None:
        if self._loading:
            return
        current_button = self.configuration_tab_buttons.get(self.configuration_combo.currentData())
        if current_button is not None:
            current_button.setText(
                self.configuration_name_edit.text().strip() or self.configuration_combo.currentText()
            )
        self.draft_changed.emit()

    def _on_recovery_mode_changed(self) -> None:
        mode = self.recovery_mode_combo.currentData()
        self._update_recovery_mode_ui(mode)
        self._emit_draft_changed()

    def _update_recovery_mode_ui(self, mode: str) -> None:
        self.single_mode_button.setChecked(mode == "single")
        self.dual_mode_button.setChecked(mode == "dual")
        if mode == "dual":
            self.deployment_helper_label.setText(
                "Drogue deploys at apogee, main deploys at a set altitude."
            )
        else:
            self.deployment_helper_label.setText(
                "Single parachute deploys at apogee. No staging."
            )
        if mode == "dual":
            self.altitude_stack.setCurrentIndex(1)
            self.parachute_stack.setCurrentIndex(1)
        else:
            self.altitude_stack.setCurrentIndex(0)
            self.parachute_stack.setCurrentIndex(0)

    def _on_atmosphere_mode_changed(self) -> None:
        mode = self.atmosphere_mode_combo.currentData()
        self._update_atmosphere_mode_ui(mode)
        self._emit_draft_changed()

    def _update_atmosphere_mode_ui(self, mode: str) -> None:
        self.manual_density_spin.setEnabled(mode == "manual_density")

    def _on_wind_mode_changed(self) -> None:
        mode = self.wind_mode_combo.currentData()
        self._update_wind_mode_ui(mode)
        self._emit_draft_changed()

    def _update_wind_mode_ui(self, mode: str) -> None:
        self.constant_wind_spin.setEnabled(mode == "constant")
        self.aloft_wind_spin.setEnabled(mode == "two_layer")
        self.ground_wind_spin.setEnabled(mode == "two_layer")

    def _sync_optional_state(self) -> None:
        self.single_apogee_spin.setEnabled(self.single_apogee_checkbox.isChecked())
        self.dual_apogee_spin.setEnabled(self.dual_apogee_checkbox.isChecked())

    def _on_display_unit_changed(self) -> None:
        new_unit_system = self.display_unit_combo.currentData()
        if self._loading or new_unit_system == self._unit_system:
            self._unit_system = new_unit_system
            self._apply_unit_suffixes(new_unit_system)
            return

        self._convert_numeric_inputs(self._unit_system, new_unit_system)
        self._unit_system = new_unit_system
        self._apply_unit_suffixes(new_unit_system)
        self._emit_draft_changed()

    def _convert_numeric_inputs(self, old_unit_system: str, new_unit_system: str) -> None:
        self.mass_spin.setValue(
            mass_from_si(mass_to_si(self.mass_spin.value(), old_unit_system), new_unit_system)
        )
        self.manual_density_spin.setValue(
            density_from_si(
                density_to_si(self.manual_density_spin.value(), old_unit_system),
                new_unit_system,
            )
        )
        for spin in (
            self.constant_wind_spin,
            self.aloft_wind_spin,
            self.ground_wind_spin,
            self.single_parachute_group["target_velocity"],
            self.drogue_parachute_group["target_velocity"],
            self.main_parachute_group["target_velocity"],
        ):
            spin.setValue(
                velocity_from_si(
                    velocity_to_si(spin.value(), old_unit_system),
                    new_unit_system,
                )
            )
        for spin in (
            self.single_deployment_altitude_spin,
            self.single_apogee_spin,
            self.dual_apogee_spin,
            self.dual_drogue_altitude_spin,
            self.dual_main_altitude_spin,
        ):
            spin.setValue(
                length_from_si(
                    length_to_si(spin.value(), old_unit_system),
                    new_unit_system,
                )
            )

    def _apply_unit_suffixes(self, unit_system: str) -> None:
        self.mass_spin.setSuffix(f" {mass_unit_label(unit_system)}")
        self.manual_density_spin.setSuffix(f" {density_unit_label(unit_system)}")
        self.constant_wind_spin.setSuffix(f" {velocity_unit_label(unit_system)}")
        self.aloft_wind_spin.setSuffix(f" {velocity_unit_label(unit_system)}")
        self.ground_wind_spin.setSuffix(f" {velocity_unit_label(unit_system)}")
        self.single_deployment_altitude_spin.setSuffix(f" {length_unit_label(unit_system)}")
        self.single_apogee_spin.setSuffix(f" {length_unit_label(unit_system)}")
        self.dual_apogee_spin.setSuffix(f" {length_unit_label(unit_system)}")
        self.dual_drogue_altitude_spin.setSuffix(f" {length_unit_label(unit_system)}")
        self.dual_main_altitude_spin.setSuffix(f" {length_unit_label(unit_system)}")
        self.single_parachute_group["target_velocity"].setSuffix(
            f" {velocity_unit_label(unit_system)}"
        )
        self.drogue_parachute_group["target_velocity"].setSuffix(
            f" {velocity_unit_label(unit_system)}"
        )
        self.main_parachute_group["target_velocity"].setSuffix(
            f" {velocity_unit_label(unit_system)}"
        )
