"""Gráfica Qt para inspeccionar la función antes de resolver."""

import math

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from core.numerical_methods.handlers.real_function import RealFunction, sample_function
from core.numerical_methods.handlers.root_bracket import BracketResult
from ui import theme_tokens as theme

from desktop.core.number_display import scientific_notation
from desktop.core.widgets import card, label, link


def _grid_ticks(low: float, high: float, pixels: float):
    """Marcas cartesianas ancladas en cero, con cinco divisiones por marca mayor."""
    target = max(math.ulp(0.0) * 10, (high - low) * min(1, 60 / pixels))
    unit = 10.0 ** math.floor(math.log10(target))
    major = next((unit * factor for factor in (1, 2, 5) if unit * factor >= target), unit * 10)
    step = major / 5
    if not math.isfinite(step):
        return
    for index in range(math.ceil(low / step), math.floor(high / step) + 1):
        yield index * step, index % 5 == 0


class FunctionPlot(QWidget):
    x_selected = Signal(float)

    def __init__(self, *, select_x: bool = False) -> None:
        super().__init__()
        self.setMinimumHeight(300)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.function: RealFunction | None = None
        self.result: BracketResult | None = None
        self.select_x = select_x
        self.markers: tuple[tuple[float, str], ...] = ()
        self.dark = False
        self._view = (-10.0, 10.0, -1.0, 1.0)
        self._drag: tuple[QPointF, tuple[float, float, float, float]] | None = None
        self._panning = False
        self._samples: tuple[tuple[float, float | None], ...] = ()

    def set_function(self, function: RealFunction | None) -> None:
        self.function = function
        self.result = None
        self.markers = ()
        if function is None:
            self._samples = ()
            self.update()
        else:
            self.reset()

    @property
    def _range(self) -> tuple[float, float]:
        return self._view[:2]

    def reset(self) -> None:
        if self.function is None:
            return
        a, b = (self.result.initial_a, self.result.initial_b) if self.result else (-10.0, 10.0)
        self._samples = ()
        self._fit_view(a, b, 0.0)

    def _fit_view(self, left: float, right: float, center_y: float) -> None:
        rect = self._plot_rect()
        if not rect.isEmpty():
            half = (right - left) / 2 * (rect.height() / rect.width())
            self._set_view(left, right, center_y - half, center_y + half)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        left, right, bottom, top = self._view
        self._fit_view(left, right, bottom + (top - bottom) / 2)

    def _sample(self) -> None:
        self._samples = sample_function(self.function, *self._range, count=1201)
        self.update()

    def show_result(self, result: BracketResult) -> None:
        self.result = result
        self.update()

    def set_markers(self, markers: tuple[tuple[float, str], ...]) -> None:
        self.markers = markers
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
        overlay = PlotOverlay(self.window())
        expanded = FunctionPlot(select_x=self.select_x)
        expanded.dark = self.dark
        expanded.function = self.function
        expanded.result = self.result
        expanded.markers = self.markers
        expanded._view = self._view
        expanded._samples = self._samples

        def select(x: float) -> None:
            self.x_selected.emit(x)
            expanded.set_markers(self.markers)

        expanded.x_selected.connect(select)

        def restore_view() -> None:
            left, right, bottom, top = expanded._view
            self._fit_view(left, right, bottom + (top - bottom) / 2)

        overlay.closing.connect(restore_view)
        overlay.panel_layout.addLayout(expanded.controls("Cerrar", overlay.close))
        overlay.panel_layout.addWidget(expanded, 1)
        overlay.show()
        overlay.raise_()
        overlay.setFocus()

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
        if not all(map(math.isfinite, (x0, x1, x1 - x0, y0, y1, y1 - y0))):
            return
        if not (x0 < x0 + (x1 - x0) / 2 < x1 and y0 < y0 + (y1 - y0) / 2 < y1):
            return
        changed_x = (x0, x1) != self._range
        self._view = x0, x1, y0, y1
        if changed_x or not self._samples:
            self._sample()
        else:
            self.update()

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y() or event.pixelDelta().y()
        if delta:
            self.zoom(0.8 if delta > 0 else 1.25, event.position())
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._plot_rect().contains(event.position()):
            self._drag = event.position(), self._view
            self._panning = False
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:
        if self._drag is not None:
            origin, (x0, x1, y0, y1) = self._drag
            rect = self._plot_rect()
            if not rect.isEmpty():
                delta = event.position() - origin
                if self.select_x and not self._panning and delta.manhattanLength() < QApplication.startDragDistance():
                    return
                self._panning = True
                dx = delta.x() / rect.width() * (x1 - x0)
                dy = delta.y() / rect.height() * (y1 - y0)
                self._set_view(x0 - dx, x1 - dx, y0 + dy, y1 + dy)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            drag, self._drag = self._drag, None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            rect = self._plot_rect()
            if (self.select_x and drag is not None and not self._panning and rect.contains(event.position())
                    and (event.position() - drag[0]).manhattanLength() < QApplication.startDragDistance()):
                low, high = self._range
                self.x_selected.emit(low + (event.position().x() - rect.left()) / rect.width() * (high - low))

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
        minor = QColor(grid)
        minor.setAlpha(125)
        for x, major in _grid_ticks(low, high, rect.width()):
            px = position(x, bottom).x()
            painter.setPen(grid if major else minor)
            painter.drawLine(QPointF(px, rect.top()), QPointF(px, rect.bottom()))
            if major:
                painter.setPen(ink)
                painter.drawText(QRectF(px - 34, rect.bottom(), 68, 24), Qt.AlignmentFlag.AlignCenter, scientific_notation(f"{x:.6g}"))
        for y, major in _grid_ticks(bottom, top, rect.height()):
            py = position(low, y).y()
            painter.setPen(grid if major else minor)
            painter.drawLine(QPointF(rect.left(), py), QPointF(rect.right(), py))
            if major:
                painter.setPen(ink)
                painter.drawText(QRectF(0, py - 9, rect.left() - 7, 18),
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, scientific_notation(f"{y:.6g}"))

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
            if value is None:
                previous = None
                continue
            # El recorte de Qt dibuja los cruces de borde. Acotar coordenadas
            # lejanas evita desbordar el pintor al pasar por una asíntota.
            ratio = (value - bottom) / (top - bottom)
            point = QPointF(position(x, bottom).x(), rect.bottom() - min(4, max(-3, ratio)) * rect.height())
            if previous is not None:
                last_x, last_y, last_point = previous
                crosses_view = min(last_y, value) < bottom and max(last_y, value) > top
                if not crosses_view or self._continuous_crossing(last_x, x, last_y / 2 + value / 2, top - bottom):
                    painter.drawLine(last_point, point)
            previous = x, value, point
        markers = self.markers
        if self.result is not None:
            markers = ((self.result.initial_a, "a"), (self.result.initial_b, "b"), (self.result.root, "c"))
        for x, name in markers:
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
            value = self.function(left + (right - left) / 2)
        except ValueError:
            return False
        return math.isclose(value, expected, abs_tol=span, rel_tol=1e-5)


class PlotOverlay(QFrame):
    """Panel ampliado sobre el área cliente de la ventana."""

    closing = Signal()

    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self._previous_focus = QApplication.focusWidget()
        self.setObjectName("plotOverlay")
        self.setStyleSheet("QFrame#plotOverlay { background: rgba(0, 0, 0, 155); }")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setGeometry(host.rect())
        host.installEventFilter(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 26)
        panel, self.panel_layout = card()
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.panel_layout.addWidget(label("Gráfica de la función", "heading"))
        layout.addWidget(panel)
        self._visible_web_views = [
            view for view in host.findChildren(QWebEngineView) if view.isVisible()
        ]
        for view in self._visible_web_views:
            view.hide()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.parentWidget() and event.type() == QEvent.Type.Resize:
            self.setGeometry(watched.rect())
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        self.parentWidget().removeEventFilter(self)
        self.closing.emit()
        super().closeEvent(event)
        for view in self._visible_web_views:
            view.show()
        if self._previous_focus is not None:
            self._previous_focus.setFocus()
