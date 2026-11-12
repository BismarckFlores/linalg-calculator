"""Teclado acoplable compartido por los campos MathLive de una ventana."""

from PySide6.QtCore import QEvent, QPoint, QRect, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ..math_input import MathInput
from ..math_keyboard import MathKeyboard
from ..widgets import GlassFrame, label, link


class UniversalMathKeyboard(GlassFrame):
    def __init__(self, host: QWidget, dock: QVBoxLayout) -> None:
        super().__init__(host)
        self._dock_area = dock.parentWidget()
        self._dock_slot = QWidget()
        self._dock_slot.hide()
        dock.addWidget(self._dock_slot)
        self._floating = False
        self._floating_position: QPoint | None = None
        self._drag_offset: QPoint | None = None
        self._plot_overlay: QWidget | None = None
        self.setObjectName("universalKeyboard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self._host = host
        self._target: MathInput | None = None

        self.toggle = QPushButton("⌨  Teclado matemático", checkable=True)
        self.toggle.setObjectName("keyboardToggle")
        self.toggle.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.toggle.setToolTip("Mostrar u ocultar el teclado matemático (Alt+Mayús+Espacio)")
        self.toggle.toggled.connect(self._set_open)
        self.plot_toggle = QPushButton("⌨  Teclado matemático  ▾", host)
        self.plot_toggle.setObjectName("plotParametersToggle")
        self.plot_toggle.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.plot_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.plot_toggle.clicked.connect(self.toggle.click)
        self.plot_toggle.hide()
        shortcut = QShortcut(QKeySequence("Alt+Shift+Space"), host)
        shortcut.activated.connect(self.toggle.click)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(4)
        self._handle = QWidget()
        self._handle.installEventFilter(self)
        header = QHBoxLayout(self._handle)
        header.setContentsMargins(6, 0, 0, 0)
        header.setSpacing(10)
        title = label("Teclado matemático", "heading")
        self._status = label("", "caption")
        for caption in (title, self._status):
            caption.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        header.addWidget(title)
        header.addWidget(self._status, 1)
        self.mode_button = link("Flotar")
        self.mode_button.setToolTip("Cambiar entre el modo acoplado y flotante")
        self.mode_button.clicked.connect(self._toggle_mode)
        header.addWidget(self.mode_button)
        self._close_button = link("Cerrar")
        self._close_button.clicked.connect(lambda: self.toggle.setChecked(False))
        header.addWidget(self._close_button)
        layout.addWidget(self._handle)
        self.keys = MathKeyboard()
        self.keys.command.connect(self._apply)
        layout.addWidget(self.keys)

        self.hide()
        self._dock_area.installEventFilter(self)
        host.installEventFilter(self)
        QApplication.instance().focusChanged.connect(self._focus_changed)

    def _focus_changed(self, _previous: QWidget | None, current: QWidget | None) -> None:
        widget = current
        while widget is not None and widget is not self._host:
            if isinstance(widget, MathInput):
                if self._host.isAncestorOf(widget):
                    field = widget if widget.accepts_math_keys() else None
                    if field is not self._target:
                        self._set_target(field)
                break
            widget = widget.parentWidget()
        self.refresh()

    def _set_target(self, field: MathInput | None) -> None:
        if self._target is not None:
            self._target.removeEventFilter(self)
            self._target.web.removeEventFilter(self)
        self._target = field
        if field is not None:
            field.installEventFilter(self)
            field.web.installEventFilter(self)

    def refresh(self) -> None:
        field = self._target
        if field is not None and (
            not field.accepts_math_keys()
            or (self._plot_overlay is not None and not self._plot_overlay.isAncestorOf(field))
        ):
            self._set_target(None)
            field = None
        self._position_plot_toggle()
        if not self.toggle.isChecked():
            return
        self._status.setText(field.name if field is not None else "Selecciona un campo matemático")
        self.keys.set_input_kind(field.kind if field is not None else None)
        self._position()
        self.show()
        self.raise_()

    def _set_open(self, opened: bool) -> None:
        if opened:
            self.refresh()
        else:
            self.hide()
            self._dock_slot.hide()
            self._position_plot_toggle()

    def _toggle_mode(self) -> None:
        self._floating = not self._floating
        self._drag_offset = None
        self.mode_button.setText("Acoplar" if self._floating else "Flotar")
        self.refresh()

    def set_plot_overlay(self, overlay: QWidget | None) -> None:
        """Presenta el teclado como otro control de la gráfica ampliada."""
        self._plot_overlay = overlay
        expanded = overlay is not None
        self._drag_offset = None
        self.mode_button.setVisible(not expanded)
        self._close_button.setVisible(not expanded)
        self.setProperty("plotMode", expanded)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        self.refresh()

    def paintEvent(self, event) -> None:
        if self._plot_overlay is None:
            super().paintEvent(event)
        else:
            QFrame.paintEvent(self, event)

    def _position_plot_toggle(self) -> None:
        if self._plot_overlay is None:
            self.plot_toggle.hide()
            return
        arrow = "▴" if self.toggle.isChecked() else "▾"
        self.plot_toggle.setText(f"⌨  Teclado matemático  {arrow}")
        self.plot_toggle.adjustSize()
        self.plot_toggle.move(14, self._host.height() - 48 - self.plot_toggle.height())
        self.plot_toggle.show()
        self.plot_toggle.raise_()

    def _is_floating(self) -> bool:
        return self._floating and self._plot_overlay is None

    def _position(self) -> None:
        area = QRect(self._dock_area.mapTo(self._host, QPoint()), self._dock_area.size())
        width = min(area.width(), 560) if self._plot_overlay is not None else area.width()
        height = self.heightForWidth(width)
        if height < 0:
            height = self.sizeHint().height()
        self.resize(width, height)

        floating = self._is_floating()
        self._handle.setCursor(Qt.CursorShape.SizeAllCursor if floating else Qt.CursorShape.ArrowCursor)
        self._handle.setToolTip("Arrastra para mover el teclado" if floating else "")
        if self._plot_overlay is not None:
            self._dock_slot.hide()
            self.move(self.plot_toggle.x(), self.plot_toggle.y() - height - 6)
            return
        if not floating:
            # La reserva participa en el diseño. El panel usa el borde del área,
            # independiente de cualquier posición guardada durante el arrastre.
            self._dock_slot.setFixedHeight(height)
            self._dock_slot.show()
            self.move(area.left(), area.bottom() + 1 - height)
            return

        self._dock_slot.hide()
        if self._floating_position is not None:
            self._move_inside(self._floating_position)
            return
        x = area.left()
        y = area.bottom() + 1 - height
        if self._target is not None:
            view = self._target.web
            target = QRect(view.mapTo(self._host, QPoint()), view.size())
            if QRect(x, y, width, height).intersects(target):
                y = area.top()
        self._move_inside(QPoint(x, y))

    def _move_inside(self, position: QPoint) -> None:
        self.move(
            max(0, min(position.x(), self._host.width() - self.width())),
            max(0, min(position.y(), self._host.height() - self.height())),
        )

    def _drag(self, event) -> bool:
        if not self._is_floating():
            return False
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = self._host.mapFromGlobal(event.globalPosition().toPoint()) - self.pos()
            return True
        if self._drag_offset is not None and event.type() == QEvent.Type.MouseMove:
            self._move_inside(self._host.mapFromGlobal(event.globalPosition().toPoint()) - self._drag_offset)
            self._floating_position = self.pos()
            return True
        if self._drag_offset is not None and event.type() == QEvent.Type.MouseButtonRelease:
            self._drag_offset = None
            return True
        return False

    def _apply(self, command: tuple) -> None:
        self.refresh()
        if self._target is not None:
            self._target.apply_math_key(command)

    def eventFilter(self, watched, event) -> bool:
        if watched is self._handle and self._drag(event):
            return True
        if (
            event.type() in (QEvent.Type.Move, QEvent.Type.Resize)
            and watched in (self._dock_area, self._host)
        ):
            self._position_plot_toggle()
            if self.toggle.isChecked():
                self._position()
        elif event.type() == QEvent.Type.Hide and self._target is not None:
            if watched in (self._target, self._target.web):
                self._set_target(None)
                self.refresh()
        return super().eventFilter(watched, event)
