"""Minimal DRIFT main window scaffold."""

from PySide6.QtWidgets import QLabel, QMainWindow

from drift import APP_FULL_NAME


class MainWindow(QMainWindow):
    """Placeholder main window for the DRIFT desktop application."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_FULL_NAME)
        placeholder = QLabel("DRIFT scaffold")
        placeholder.setMargin(24)
        self.setCentralWidget(placeholder)
