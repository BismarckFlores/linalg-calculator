"""Gráfica Qt para inspeccionar la función antes de resolver."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QWidget

from core.real_function import RealFunction, sample_function
from core.root_bracket import BracketResult
from ui import theme_tokens as theme

from .widgets import link


class FunctionPlot(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(245)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.function: RealFunction | None = None
        self.result: BracketResult | None = None
        self.dark = False
        self._range = (-4.0, 4.0)
        self._drag: QPointF | None = None
        self._samples: tuple[tuple[float, float | None], ...] = ()

    def set_function(self, function: RealFunction) -> None:
        self.function = function
        self.result = None
        self.reset()

    def reset(self) -> None:
        self._set_range(-4.0, 4.0)

    def show_result(self, result: BracketResult) -> None:
        self.result = result
        low, high = self._range
        if result.initial_a < low or result.initial_b > high:
            self._set_range(result.initial_a, result.initial_b)
        self.update()

    def controls(self, text: str, callback) -> QHBoxLayout:
        controls = QHBoxLayout()
        for name, action in (
            ("+  Acercar", lambda: self.zoom(0.8)),
            ("−  Alejar", lambda: self.zoom(1.25)),
            ("Restablecer", self.reset),
            (text, callback),
        ):
            button = link(name)
            button.clicked.connect(action)
            controls.addWidget(button)
        controls.addStretch()
        return controls

    def expand(self) -> None:
        if self.function is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Gráfica de la función")
        dialog.resize(900, 600)
        layout = QVBoxLayout(dialog)
        expanded = FunctionPlot()
        expanded.dark = self.dark
        expanded.function = self.function
        expanded.result = self.result
        expanded._set_range(*self._range)
        layout.addLayout(expanded.controls("Cerrar", dialog.accept))
        layout.addWidget(expanded, 1)
        dialog.exec()
        self._set_range(*expanded._range)

    def zoom(self, factor: float) -> None:
        low, high = self._range
        span = high - low
        middle = low + span / 2
        self._set_range(middle - span * factor / 2, middle + span * factor / 2)

    def _set_range(self, low: float, high: float) -> None:
        if not math.isfinite(high - low) or not low < high or self.function is None:
            return
        self._range = low, high
        self._samples = sample_function(self.function, low, high)
        self.update()

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y() or event.pixelDelta().y()
        if delta:
            self.zoom(0.8 if delta > 0 else 1.25)
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:
        if self._drag is not None:
            low, high = self._range
            delta = (self._drag.x() - event.position().x()) / max(1, self.width() - 66) * (high - low)
            self._drag = event.position()
            self._set_range(low + delta, high + delta)

    def mouseReleaseEvent(self, event) -> None:
        self._drag = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def paintEvent(self, event) -> None:
        if not self._samples:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(52, 10, self.width() - 66, self.height() - 39)
        if rect.isEmpty():
            return
        low, high = self._range
        ordinates = [value for _x, value in self._samples if value is not None]
        scale = max((abs(value) for value in ordinates), default=0.0) or 1.0
        bottom = min([0.0, *(value / scale for value in ordinates)])
        top = max([0.0, *(value / scale for value in ordinates)])
        margin = max(0.05, (top - bottom) / 10)
        bottom, top = bottom - margin, top + margin

        def position(x: float, y: float) -> QPointF:
            return QPointF(
                rect.left() + (x - low) / (high - low) * rect.width(),
                rect.bottom() - (y - bottom) / (top - bottom) * rect.height(),
            )

        mode = int(self.dark)
        grid = QColor(theme.BORDER[mode])
        ink = QColor(theme.MUTED[mode])
        for index in range(5):
            x = low + (high - low) * (index / 4)
            y = bottom + (top - bottom) * index / 4
            point = position(x, y)
            painter.setPen(grid)
            painter.drawLine(QPointF(point.x(), rect.top()), QPointF(point.x(), rect.bottom()))
            painter.drawLine(QPointF(rect.left(), point.y()), QPointF(rect.right(), point.y()))
            painter.setPen(ink)
            painter.drawText(QRectF(point.x() - 25, rect.bottom(), 50, 24), Qt.AlignmentFlag.AlignCenter, f"{x:.4g}")
            painter.drawText(QPointF(2, point.y() + 4), f"{y * scale:.3g}")

        painter.setPen(ink)
        painter.drawLine(position(low, 0), position(high, 0))
        if low <= 0 <= high:
            painter.drawLine(position(0, bottom), position(0, top))
        painter.setClipRect(rect)
        painter.setPen(QPen(QColor(theme.ACCENT), 2))
        previous = None
        for x, value in self._samples:
            point = position(x, value / scale) if value is not None else None
            if previous is not None and point is not None and abs(point.y() - previous.y()) < rect.height() * 0.8:
                painter.drawLine(previous, point)
            previous = point
        if self.result is not None:
            for x, name in ((self.result.initial_a, "a"), (self.result.initial_b, "b"), (self.result.root, "c")):
                if low <= x <= high:
                    painter.setPen(QPen(QColor(theme.ORANGE), 1, Qt.PenStyle.DashLine))
                    painter.drawLine(position(x, bottom), position(x, top))
                    point = position(x, top)
                    label_width = painter.fontMetrics().horizontalAdvance(name)
                    text_x = min(point.x() + 4, rect.right() - label_width - 4)
                    painter.drawText(QPointF(text_x, point.y() + 14), name)
