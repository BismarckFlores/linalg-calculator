"""Gráfica Qt para inspeccionar la función antes de resolver."""

import math

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPalette, QPen, QShortcut
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from core.numerical_methods.handlers.real_function import RealFunction, sample_function
from core.numerical_methods.handlers.root_bracket import BracketResult
from ui import theme_tokens as theme

from desktop.core.number_display import scientific_notation
from desktop.core.widgets import card, label


def _major_step(span: float, pixels: float) -> float:
    """Elige una distancia de la serie 1, 2, 5 según el zoom."""
    target = max(math.ulp(0.0) * 10, span * min(1, 60 / pixels))
    unit = 10.0 ** math.floor(math.log10(target))
    return next((unit * factor for factor in (1, 2, 5) if unit * factor >= target), unit * 10)


def _grid_ticks(low: float, high: float, pixels: float):
    """Marcas cartesianas ancladas en cero, con cinco divisiones por marca mayor."""
    major = _major_step(high - low, pixels)
    step = major / 5
    if not math.isfinite(step):
        return
    for index in range(math.ceil(low / step), math.floor(high / step) + 1):
        yield index * step, index % 5 == 0


class PlotButton(QPushButton):
    """Botón de icono con el color de texto del tema activo."""

    def __init__(self, icon: str, name: str) -> None:
        super().__init__()
        self.setObjectName("plotButton")
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_symbol(icon, name)

    def set_symbol(self, icon: str, name: str) -> None:
        self._icon = icon
        self.setAccessibleName(name)
        self.setToolTip(name)
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(self.width() / 2, self.height() / 2)
            pen = QPen(self.palette().color(QPalette.ColorRole.ButtonText), 1.8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            if self._icon in ("plus", "minus"):
                painter.drawLine(QPointF(-6, 0), QPointF(6, 0))
                if self._icon == "plus":
                    painter.drawLine(QPointF(0, -6), QPointF(0, 6))
            elif self._icon == "reset":
                painter.drawArc(QRectF(-6, -6, 12, 12), -120 * 16, 300 * 16)
                painter.drawLine(QPointF(-6, 0), QPointF(-6, -5))
                painter.drawLine(QPointF(-6, 0), QPointF(-1, 0))
            elif self._icon == "close":
                painter.drawLine(QPointF(-5, -5), QPointF(5, 5))
                painter.drawLine(QPointF(-5, 5), QPointF(5, -5))
            else:
                for x in (-1, 1):
                    for y in (-1, 1):
                        corner = QPointF(6 * x, 6 * y)
                        painter.drawLine(corner, QPointF(2 * x, 6 * y))
                        painter.drawLine(corner, QPointF(6 * x, 2 * y))


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
        self.solution: tuple[float, float, bool] | None = None
        self.dark = False
        self._view = (-10.0, 10.0, -1.0, 1.0)
        self._reference_span = self._view[1] - self._view[0]
        self._drag: tuple[QPointF, tuple[float, float, float, float]] | None = None
        self._panning = False
        self._samples: tuple[tuple[float, float | None], ...] = ()

        buttons = QVBoxLayout(self)
        buttons.setContentsMargins(0, 0, 8, 32)
        buttons.setSpacing(4)
        buttons.addStretch()
        for icon, name, callback in (
            ("plus", "Acercar", lambda: self.zoom(0.8)),
            ("minus", "Alejar", lambda: self.zoom(1.25)),
            ("reset", "Restablecer", self.reset),
        ):
            button = PlotButton(icon, name)
            button.clicked.connect(callback)
            buttons.addWidget(button, alignment=Qt.AlignmentFlag.AlignRight)
        self.expand_button = PlotButton("expand", "Maximizar")
        buttons.addWidget(self.expand_button, alignment=Qt.AlignmentFlag.AlignRight)

    def set_function(self, function: RealFunction | None) -> None:
        self.function = function
        self.result = None
        self.markers = ()
        self.solution = None
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
        left, right = self._range
        self._reference_span = right - left

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

    def show_solution(self, x: float, value: float, *, converged: bool) -> None:
        y = 0.0 if converged else value
        self.solution = (x, y, converged)
        left, right, bottom, top = self._view
        if converged and not (left <= x <= right and bottom <= 0 <= top):
            half = (right - left) / 2
            if not left <= x <= right:
                left, right = x - half, x + half
            center_y = bottom + (top - bottom) / 2 if bottom <= 0 <= top else 0.0
            self._fit_view(left, right, center_y)
        self.update()

    def clear_solution(self) -> None:
        if self.solution is not None:
            self.solution = None
            self.update()

    def _plot_rect(self) -> QRectF:
        return QRectF(64, 48, self.width() - 116, self.height() - 82)

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

    def _draw_scale(self, painter: QPainter, rect: QRectF, ink: QColor) -> None:
        """Dibuja en la cabecera una distancia medida en unidades de la gráfica."""
        painter.setPen(ink)
        low, high = self._range
        span = high - low
        ratio = scientific_notation(f"{self._reference_span / span:.4g}")
        painter.drawText(QPointF(12, 23), f"Escala {ratio}:1")
        units = _major_step(span, rect.width())
        pixels = units / span * rect.width()
        if not math.isfinite(pixels) or pixels > rect.width():
            return
        right = rect.right() - 2
        left = right - pixels
        y = 27
        painter.drawLine(QPointF(left, y), QPointF(right, y))
        for index in range(6):
            x = left + pixels * index / 5
            tick = 5 if index in (0, 5) else 3
            painter.drawLine(QPointF(x, y - tick), QPointF(x, y + tick))
        caption = scientific_notation(f"{units:.6g}") + " u"
        width = max(pixels, painter.fontMetrics().horizontalAdvance(caption) + 4)
        painter.drawText(QRectF(right - width, 2, width, 18), Qt.AlignmentFlag.AlignCenter, caption)

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

        self._draw_scale(painter, rect, ink)
        painter.setPen(ink)
        painter.drawText(QPointF(rect.left(), rect.top() - 5), "f(x)")
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

        if self.solution is not None:
            x, y, converged = self.solution
            if low <= x <= high and bottom <= y <= top:
                self._draw_solution(painter, rect, position(x, y), x, converged)

    def _draw_solution(
        self, painter: QPainter, rect: QRectF, point: QPointF, x: float, converged: bool,
    ) -> None:
        color = QColor(theme.GREEN if self.dark else "#17743d") if converged else QColor(theme.ORANGE)
        painter.setPen(QPen(QColor(theme.CARD[int(self.dark)]), 2))
        painter.setBrush(color)
        painter.drawEllipse(point, 5, 5)
        name = "Raíz" if converged else "Última aprox."
        caption = f"{name} ≈ {scientific_notation(f'{x:.10g}')}"
        metrics = painter.fontMetrics()
        width = metrics.horizontalAdvance(caption) + 12
        height = metrics.height() + 6
        left = max(rect.left() + 2, min(point.x() + 10, rect.right() - width - 2))
        top = point.y() - height - 8
        if top < rect.top() + 2:
            top = min(point.y() + 8, rect.bottom() - height - 2)
        badge = QRectF(left, top, width, height)
        painter.setPen(QPen(color, 1))
        painter.setBrush(QColor(theme.CARD[int(self.dark)]))
        painter.drawRoundedRect(badge, 6, 6)
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, caption)

    def _continuous_crossing(self, left: float, right: float, expected: float, span: float) -> bool:
        if self.function is None:
            return False
        try:
            value = self.function(left + (right - left) / 2)
        except ValueError:
            return False
        return math.isclose(value, expected, abs_tol=span, rel_tol=1e-5)


class PlotPanel(QWidget):
    """La misma gráfica y sus campos se alojan en las dos vistas."""

    def __init__(self, plot: FunctionPlot, hint: str) -> None:
        super().__init__()
        self.plot = plot
        self._overlay: PlotOverlay | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        panel, self._content = card()
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._heading = label("Gráfica de la función", "heading")
        self._hint = label(hint, "muted")
        self._content.addWidget(self._heading)
        surface = QWidget()
        self._layers = QGridLayout(surface)
        self._layers.setContentsMargins(0, 0, 0, 0)
        self._layers.addWidget(plot, 0, 0)
        self._content.addWidget(surface, 1)
        self._content.addWidget(self._hint)

        self._floating = QWidget()
        self._floating.setMaximumWidth(560)
        self._floating_layout = QVBoxLayout(self._floating)
        self._floating_layout.setContentsMargins(14, 52, 0, 0)
        self._floating_layout.setSpacing(6)
        self._toggle_fields = QPushButton(checkable=True)
        self._toggle_fields.setObjectName("plotParametersToggle")
        self._toggle_fields.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_fields.toggled.connect(self._show_floating_fields)
        self._floating_layout.addWidget(self._toggle_fields, alignment=Qt.AlignmentFlag.AlignLeft)
        self._layers.addWidget(self._floating, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._floating.hide()
        layout.addWidget(panel)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.plot.expand_button.clicked.connect(self._toggle_expanded)

    def set_hint(self, hint: str) -> None:
        self._hint.setText(hint)

    def parameters(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        self._parameters = QFrame()
        self._parameters.setObjectName("plotParameters")
        self._parameters_title = title
        self._parameters_heading = label(title, "heading")
        layout = QVBoxLayout(self._parameters)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)
        layout.addWidget(self._parameters_heading)
        self._content.addWidget(self._parameters)
        return self._parameters, layout

    def _show_floating_fields(self, shown: bool) -> None:
        self._toggle_fields.setText(f"{self._parameters_title}  {'▴' if shown else '▾'}")
        self._parameters.setVisible(shown)

    def _set_expanded(self, expanded: bool) -> None:
        policy = QSizePolicy.Policy.Expanding if expanded else QSizePolicy.Policy.Maximum
        self.setSizePolicy(QSizePolicy.Policy.Preferred, policy)
        margins = (0, 0, 0, 0) if expanded else (24, 22, 24, 22)
        self._content.setContentsMargins(*margins)
        self._heading.setVisible(not expanded)
        self._hint.setVisible(not expanded)
        self._parameters_heading.setVisible(not expanded)
        if expanded:
            self._floating_layout.addWidget(self._parameters)
            self._floating.show()
            self._floating.raise_()
            self._toggle_fields.setChecked(True)
            self._show_floating_fields(True)
        else:
            self._content.addWidget(self._parameters)
            self._parameters.show()
            self._floating.hide()
        self.plot.expand_button.set_symbol(
            "close" if expanded else "expand", "Cerrar" if expanded else "Maximizar",
        )

    def _toggle_expanded(self) -> None:
        if self._overlay is not None:
            self._overlay.close()
        elif self.plot.function is not None:
            self._overlay = PlotOverlay(self.window(), self)
            self._set_expanded(True)
            self._overlay.show()
            self._overlay.raise_()
            self._overlay.setFocus()
            self._overlay.notify_keyboard(True)

    def finish(self, result: QWidget) -> None:
        """Muestra el resultado debajo del panel al calcular desde la vista ampliada."""
        if self._overlay is None:
            return
        self._overlay.close()
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, QScrollArea):
            parent = parent.parentWidget()
        if parent is not None:
            QTimer.singleShot(0, result, lambda: parent.ensureWidgetVisible(result, 0, 12))

    def restore(self) -> None:
        self._overlay = None
        self._set_expanded(False)


class PlotOverlay(QFrame):
    """Amplía el panel sobre la ventana y devuelve los mismos controles al cerrar."""

    def __init__(self, host: QWidget, panel: PlotPanel) -> None:
        super().__init__(host)
        self._panel = panel
        self._original_layout = panel.parentWidget().layout()
        self._original_index = self._original_layout.indexOf(panel)
        self._previous_focus = QApplication.focusWidget()
        self.setObjectName("plotOverlay")
        self.setStyleSheet("QFrame#plotOverlay { background: rgba(0, 0, 0, 155); }")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setGeometry(host.rect())
        host.installEventFilter(self)
        escape = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        escape.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        escape.activated.connect(self.close)

        self._visible_web_views = [
            view for view in host.findChildren(QWebEngineView)
            if view.isVisible() and not panel.isAncestorOf(view)
        ]
        for view in self._visible_web_views:
            view.hide()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(panel, 1)
        panel.show()

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

    def notify_keyboard(self, expanded: bool) -> None:
        callback = getattr(self.parentWidget(), "set_plot_overlay", None)
        if callback is not None:
            callback(self if expanded else None)

    def closeEvent(self, event) -> None:
        self.parentWidget().removeEventFilter(self)
        self._original_layout.insertWidget(self._original_index, self._panel)
        self._panel.restore()
        self._panel.show()
        super().closeEvent(event)
        for view in self._visible_web_views:
            view.show()
        self.notify_keyboard(False)
        if self._previous_focus is not None:
            self._previous_focus.setFocus()
