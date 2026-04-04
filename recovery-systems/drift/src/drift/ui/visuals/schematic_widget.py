"""Painted recovery schematic widget for DRIFT."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from drift.formatting import format_length
from drift.services.visualization import RecoveryVisualModel
from drift.ui.theme import Colours, mono_font, qcolor, ui_font

SEGMENT_COLORS = {
    "ascent": qcolor(Colours.PHASE_ASCENT),
    "transition": qcolor(Colours.PHASE_FREEFALL),
    "single": qcolor(Colours.PHASE_MAIN),
    "drogue": qcolor(Colours.PHASE_DROGUE),
    "main": qcolor(Colours.PHASE_MAIN),
}


class RecoverySchematicWidget(QtWidgets.QWidget):
    """Simple engineering schematic driven by the visual model."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._message = "Analyse a configuration to render the recovery schematic."
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
        painter.fillRect(self.rect(), qcolor(Colours.SURFACE_1))

        if self._model is None:
            painter.setFont(ui_font(point_size=11))
            painter.setPen(qcolor(Colours.MUTED_FOREGROUND))
            painter.drawText(
                self.rect().adjusted(20, 20, -20, -20),
                QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap,
                self._message,
            )
            return

        rect = self.rect().adjusted(24, 24, -24, -24)
        header_rect = QtCore.QRect(rect.left(), rect.top(), rect.width(), 24)
        painter.setFont(ui_font(point_size=10, weight=QtGui.QFont.DemiBold))
        painter.setPen(qcolor(Colours.MUTED_FOREGROUND))
        painter.drawText(
            header_rect,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            f"Schematic, not to scale. Basis: {self._model.basis_label}",
        )

        body_top = header_rect.bottom() + 12
        body_bottom = rect.bottom() - 12

        painter.setPen(QtGui.QPen(qcolor(Colours.PANEL_BORDER), 2))
        painter.drawLine(rect.left() + 16, body_bottom, rect.right() - 16, body_bottom)

        max_altitude_m = max(self._model.max_altitude_m, 1.0)

        def altitude_to_y(altitude_m: float) -> int:
            ratio = altitude_m / max_altitude_m
            return int(body_bottom - ratio * (body_bottom - body_top))

        def x_fraction_to_x(x_fraction: float) -> int:
            return int(rect.left() + x_fraction * rect.width())

        for segment in self._model.segments:
            x_start = x_fraction_to_x(segment.start_x_fraction)
            x_end = x_fraction_to_x(segment.end_x_fraction)
            y_start = altitude_to_y(segment.start_altitude_m)
            y_end = altitude_to_y(segment.end_altitude_m)
            color = SEGMENT_COLORS.get(segment.kind, QtGui.QColor("#1f2937"))
            pen = QtGui.QPen(color, 4)
            if segment.kind in {"ascent", "transition"}:
                pen.setStyle(QtCore.Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(x_start, y_start, x_end, y_end)

            if segment.show_label:
                self._draw_segment_label(
                    painter,
                    rect,
                    x_start,
                    y_start,
                    x_end,
                    y_end,
                    segment.label,
                    segment.kind,
                    color,
                )

        label_positions = self._layout_marker_labels(rect, altitude_to_y)
        for marker, (label_rect, alignment) in zip(self._model.markers, label_positions, strict=True):
            x = x_fraction_to_x(marker.x_fraction)
            y = altitude_to_y(marker.altitude_m)
            color = qcolor(Colours.MUTED_FOREGROUND)
            if marker.kind == "apogee":
                color = qcolor(Colours.PHASE_FREEFALL)
            elif marker.kind == "deployment":
                color = qcolor(Colours.PRIMARY)
            painter.setPen(QtGui.QPen(color, 2))
            painter.setBrush(color)
            painter.drawEllipse(QtCore.QPoint(x, y), 4, 4)
            if label_rect.center().x() < x:
                painter.drawLine(label_rect.right() + 4, label_rect.center().y(), x - 6, y)
            elif label_rect.center().x() > x:
                leader_y = label_rect.center().y()
                painter.drawLine(x + 6, y, label_rect.left() - 4, leader_y)
            painter.setFont(mono_font(point_size=9))
            painter.drawText(
                label_rect,
                alignment,
                f"{marker.label} ({format_length(marker.altitude_m, self._unit_system)})",
            )

        painter.end()

    def _draw_segment_label(
        self,
        painter: QtGui.QPainter,
        rect: QtCore.QRect,
        x_start: int,
        y_start: int,
        x_end: int,
        y_end: int,
        label: str,
        kind: str,
        color: QtGui.QColor,
    ) -> None:
        mid_x = int((x_start + x_end) / 2)
        mid_y = int((y_start + y_end) / 2)
        painter.setFont(mono_font(point_size=9))
        painter.setPen(color)

        if kind == "ascent":
            label_rect = QtCore.QRect(
                max(rect.left() + 8, mid_x - 170),
                max(rect.top() + 30, mid_y - 24),
                150,
                20,
            )
            alignment = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        else:
            label_rect = QtCore.QRect(
                min(rect.right() - 180, mid_x + 12),
                max(rect.top() + 30, mid_y - 10),
                170,
                20,
            )
            alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter

        painter.drawText(label_rect, alignment, label)

    def _layout_marker_labels(
        self,
        rect: QtCore.QRect,
        altitude_to_y,
    ) -> list[tuple[QtCore.QRect, QtCore.Qt.AlignmentFlag]]:
        label_rects: list[tuple[QtCore.QRect, QtCore.Qt.AlignmentFlag]] = []
        label_width = min(220, int(rect.width() * 0.34))
        left_x = rect.left() + 12
        right_x = rect.left() + int(rect.width() * 0.58)
        min_top = rect.top() + 34
        max_bottom = rect.bottom() - 8
        previous_bottom = {"left": min_top - 6, "right": min_top - 6}

        for marker in self._model.markers:
            y = altitude_to_y(marker.altitude_m)
            top = y - 12
            if marker.kind == "apogee":
                top -= 10
            elif marker.kind == "ground":
                top -= 14

            top = max(top, min_top)
            side = self._marker_label_side(marker)
            if top <= previous_bottom[side]:
                top = previous_bottom[side] + 6
            if top + 24 > max_bottom:
                top = max(min_top, max_bottom - 24)
            previous_bottom[side] = top + 24
            if side == "left":
                label_rects.append(
                    (
                        QtCore.QRect(left_x, top, label_width, 24),
                        QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
                    )
                )
            else:
                label_rects.append(
                    (
                        QtCore.QRect(right_x, top, rect.right() - right_x - 8, 24),
                        QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                    )
                )

        return label_rects

    @staticmethod
    def _marker_label_side(marker) -> str:
        if marker.kind == "ground":
            return "left"
        if marker.kind == "apogee":
            return "right"
        if marker.x_fraction >= 0.72:
            return "left"
        return "right"


__all__ = ["RecoverySchematicWidget"]
