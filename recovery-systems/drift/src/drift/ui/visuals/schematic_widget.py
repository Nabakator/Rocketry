"""Painted recovery schematic widget for DRIFT."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from drift.formatting import format_length
from drift.services.visualization import RecoveryVisualModel

SEGMENT_COLORS = {
    "ascent": QtGui.QColor("#6b7280"),
    "single": QtGui.QColor("#1d4ed8"),
    "drogue": QtGui.QColor("#c2410c"),
    "main": QtGui.QColor("#047857"),
}


class RecoverySchematicWidget(QtWidgets.QWidget):
    """Simple engineering schematic driven by the visual model."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._message = "Analyze a configuration to render the recovery schematic."
        self._model: RecoveryVisualModel | None = None
        self._unit_system = "si"
        self.setMinimumHeight(320)

    def show_message(self, message: str) -> None:
        self._message = message
        self._model = None
        self.update()

    def set_visual_model(self, model: RecoveryVisualModel, *, unit_system: str) -> None:
        self._message = ""
        self._model = model
        self._unit_system = unit_system
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # noqa: N802
        del event
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.palette().base())

        if self._model is None:
            painter.setPen(self.palette().color(QtGui.QPalette.WindowText))
            painter.drawText(
                self.rect().adjusted(20, 20, -20, -20),
                QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap,
                self._message,
            )
            return

        rect = self.rect().adjusted(24, 24, -24, -24)
        header_rect = QtCore.QRect(rect.left(), rect.top(), rect.width(), 24)
        painter.setPen(self.palette().color(QtGui.QPalette.WindowText))
        painter.drawText(
            header_rect,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            f"Schematic, not to scale. Basis: {self._model.basis_label}",
        )

        body_top = header_rect.bottom() + 12
        body_bottom = rect.bottom() - 12
        axis_x = rect.left() + 120
        label_x = axis_x + 28

        painter.setPen(QtGui.QPen(QtGui.QColor("#111827"), 2))
        painter.drawLine(axis_x, body_top, axis_x, body_bottom)

        ground_y = body_bottom
        painter.setPen(QtGui.QPen(QtGui.QColor("#111827"), 2))
        painter.drawLine(axis_x - 36, ground_y, rect.right() - 16, ground_y)

        max_altitude_m = max(self._model.max_altitude_m, 1.0)

        def altitude_to_y(altitude_m: float) -> int:
            ratio = altitude_m / max_altitude_m
            return int(body_bottom - ratio * (body_bottom - body_top))

        for segment in self._model.segments:
            y_start = altitude_to_y(segment.start_altitude_m)
            y_end = altitude_to_y(segment.end_altitude_m)
            color = SEGMENT_COLORS.get(segment.kind, QtGui.QColor("#1f2937"))
            pen = QtGui.QPen(color, 4)
            if segment.kind == "ascent":
                pen.setStyle(QtCore.Qt.DashLine)
            painter.setPen(pen)
            x = axis_x - 28 if segment.kind == "ascent" else axis_x
            painter.drawLine(x, y_start, x, y_end)
            painter.setPen(color)
            painter.drawText(
                QtCore.QRect(label_x, min(y_start, y_end) - 10, rect.width() - label_x, 20),
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                segment.label,
            )

        for marker in self._model.markers:
            y = altitude_to_y(marker.altitude_m)
            color = QtGui.QColor("#111827")
            if marker.kind == "apogee":
                color = QtGui.QColor("#7c3aed")
            elif marker.kind == "deployment":
                color = QtGui.QColor("#b91c1c")
            painter.setPen(QtGui.QPen(color, 2))
            painter.setBrush(color)
            painter.drawEllipse(QtCore.QPoint(axis_x, y), 4, 4)
            painter.drawText(
                QtCore.QRect(label_x, y - 12, rect.width() - label_x, 24),
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                f"{marker.label} ({format_length(marker.altitude_m, self._unit_system)})",
            )

        painter.end()


__all__ = ["RecoverySchematicWidget"]
