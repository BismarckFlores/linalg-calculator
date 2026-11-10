"""Gráfica Qt para inspeccionar la función antes de resolver."""

import math
import sys

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
        self.setMinimumHeight(300)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.function: RealFunction | None = None
        self.result: BracketResult | None = None
        self.dark = False
        self._view = (-10.0, 10.0, -1.0, 1.0)
        self._y_scale = 1.0
        self._drag: tuple[QPointF, tuple[float, float, float, float]] | None = None
        self._samples: tuple[tuple[float, float | None], ...] = ()

    def set_function(self, function: RealFunction) -> None:
        self.function = function
        self.result = None
        self.reset()

    @property
    def _range(self) -> tuple[float, float]:
        return self._view[:2]

    def reset(self) -> None:
        if self.function is None:
            return
        a, b = (self.result.initial_a, self.result.initial_b) if self.result else (-10.0, 10.0)
        self._samples = sample_function(self.function, a, b)
        values = [value for _, value in self._samples if value is not None]
        low, high = min([0.0, *values]), max([0.0, *values])
        self._y_scale = max(abs(low), abs(high)) or 1.0
        low, high = low / self._y_scale, high / self._y_scale
        margin = max(0.1, (high - low) * 0.1)
        limit = sys.float_info.max / self._y_scale
        self._view = a, b, max(-limit, low - margin), min(limit, high + margin)
        self.update()

    def show_result(self, result: BracketResult) -> None:
        self.result = result
        self.update()

    def controls(self, text: str, callback) -> QHBoxLayout:
        controls = QHBoxLayout()
        for name, action in (
            ("+  Acercar", lambda: self.zoom(0.8)),
            ("−  Alejar", lambda: self.zoom(1.25)),
            ("Restablecer", self.reset),
        ):
            button = link(name)
            button.clicked.connect(action)
            controls.addWidget(button)
        controls.addStretch()
        button = link(text)
        button.clicked.connect(callback)
        controls.addWidget(button)
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
        expanded._y_scale = self._y_scale
        expanded._view = self._view
        expanded._samples = self._samples
        layout.addLayout(expanded.controls("Cerrar", dialog.accept))
        layout.addWidget(expanded, 1)
        dialog.exec()
        self._y_scale = expanded._y_scale
        self._view = expanded._view
        self._samples = expanded._samples
        self.update()

    def _plot_rect(self) -> QRectF:
        return QRectF(64, 18, self.width() - 84, self.height() - 52)

    def zoom(self, factor: float, anchor: QPointF | None = None) -> None:
        rect = self._plot_rect()
        if rect.isEmpty():
            return
        fx = 0.5 if anchor is None else min(1.0, max(0.0, (anchor.x() - rect.left()) / rect.width()))
        fy = 0.5 if anchor is None else min(1.0, max(0.0, (rect.bottom() - anchor.y()) / rect.height()))
        x0, x1, y0, y1 = self._view
        dx, dy = (x1 - x0) * (1 - factor), (y1 - y0) * (1 - factor)
        self._set_view(x0 + fx * dx, x1 - (1 - fx) * dx, y0 + fy * dy, y1 - (1 - fy) * dy)

    def _set_view(self, x0: float, x1: float, y0: float, y1: float) -> None:
        if self.function is None or not (x0 < x1 and y0 < y1):
            return
        if not all(map(math.isfinite, (x0, x1, x1 - x0, y0, y1, y1 - y0,
                                       y0 * self._y_scale, y1 * self._y_scale))):
            return
        if not (x0 < x0 + (x1 - x0) / 2 < x1 and y0 < y0 + (y1 - y0) / 2 < y1):
            return
        if (x0, x1) != self._range:
            self._samples = sample_function(self.function, x0, x1)
        self._view = x0, x1, y0, y1
        self.update()

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y() or event.pixelDelta().y()
        if delta:
            self.zoom(0.8 if delta > 0 else 1.25, event.position())
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._plot_rect().contains(event.position()):
            self._drag = event.position(), self._view
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:
        if self._drag is not None:
            origin, (x0, x1, y0, y1) = self._drag
            rect = self._plot_rect()
            if not rect.isEmpty():
                delta = event.position() - origin
                dx = delta.x() / rect.width() * (x1 - x0)
                dy = delta.y() / rect.height() * (y1 - y0)
                self._set_view(x0 - dx, x1 - dx, y0 + dy, y1 + dy)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def paintEvent(self, event) -> None:
        if not self._samples:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self._plot_rect()
        if rect.isEmpty():
            return
        low, high, bottom, top = self._view

        def position(x: float, y: float) -> QPointF:
            return QPointF(
                rect.left() + (x - low) / (high - low) * rect.width(),
                rect.bottom() - (y - bottom) / (top - bottom) * rect.height(),
            )

        mode = int(self.dark)
        painter.fillRect(self.rect(), QColor(theme.CARD[mode]))
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
            painter.drawText(QPointF(2, point.y() + 4), f"{y * self._y_scale:.4g}")

        painter.setPen(ink)
        painter.drawText(QPointF(rect.left(), 13), "f(x)")
        painter.drawText(QPointF(rect.right(), self.height() - 4), "x")
        if bottom <= 0 <= top:
            painter.drawLine(position(low, 0), position(high, 0))
        if low <= 0 <= high:
            painter.drawLine(position(0, bottom), position(0, top))
        painter.setClipRect(rect)
        painter.setPen(QPen(QColor(theme.ACCENT), 2))
        previous = None
        for x, value in self._samples:
            scaled = value / self._y_scale if value is not None else None
            if scaled is None:
                previous = None
                continue
            # El recorte de Qt dibuja los cruces de borde. Acotar coordenadas
            # lejanas evita desbordar el pintor al pasar por una asíntota.
            ratio = (scaled - bottom) / (top - bottom)
            point = QPointF(position(x, bottom).x(), rect.bottom() - min(4, max(-3, ratio)) * rect.height())
            if previous is not None:
                last_x, last_y, last_point = previous
                crosses_view = min(last_y, scaled) < bottom and max(last_y, scaled) > top
                if not crosses_view or self._continuous_crossing(last_x, x, last_y / 2 + scaled / 2, top - bottom):
                    painter.drawLine(last_point, point)
            previous = x, scaled, point
        if self.result is not None:
            for x, name in ((self.result.initial_a, "a"), (self.result.initial_b, "b"), (self.result.root, "c")):
                if low <= x <= high:
                    painter.setPen(QPen(QColor(theme.ORANGE), 1, Qt.PenStyle.DashLine))
                    painter.drawLine(position(x, bottom), position(x, top))
                    point = position(x, top)
                    label_width = painter.fontMetrics().horizontalAdvance(name)
                    text_x = min(point.x() + 4, rect.right() - label_width - 4)
                    painter.drawText(QPointF(text_x, point.y() + 14), name)

    def _continuous_crossing(self, left: float, right: float, expected: float, span: float) -> bool:
        if self.function is None:
            return False
        try:
            value = self.function(left + (right - left) / 2) / self._y_scale
        except ValueError:
            return False
        return math.isclose(value, expected, abs_tol=span, rel_tol=1e-5)
