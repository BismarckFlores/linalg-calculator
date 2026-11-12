"""Campo MathLive local con entrada de texto de respaldo."""

import json

from PySide6.QtCore import QSignalBlocker, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from ui import theme_tokens as theme

from .assets import ASSETS
from .handlers.editor import EditorBridge
from .math_notation import from_ascii, result_blocks, to_latex
from .number_display import parse_scientific_display, scientific_notation
from .widgets import interface_fonts, label


class MathInput(QWidget):
    changed = Signal()

    def __init__(self, text: str, name: str, kind: str = "function", *, inline: bool = False) -> None:
        super().__init__()
        self._value = text
        self._latex: tuple[str, ...] = ()
        self.kind = kind
        self.name = name
        self._ready = False
        self._dark = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        if name and not inline:
            layout.addWidget(label(name, "caption"))

        self.stack = QStackedWidget()
        self.web = QWebEngineView()
        self.web.page().setBackgroundColor(QColor(Qt.GlobalColor.transparent))
        self.web.setFixedHeight(50)
        if kind == "output":
            self.text = label("", "resultFallback")
            self.text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        elif kind in ("equations", "matrix"):
            self.text = QPlainTextEdit()
            self.text.textChanged.connect(self.changed)
        else:
            self.text = QLineEdit()
            self.text.textEdited.connect(self.changed)
        self.text.setAccessibleName(name)
        self.stack.addWidget(self.web)
        self.stack.addWidget(self.text)
        self.stack.setFixedHeight(50)
        if inline:
            row = QHBoxLayout()
            caption = label(name, "caption")
            caption.setFixedWidth(68)
            row.addWidget(caption)
            row.addWidget(self.stack, 1)
            layout.addLayout(row)
        else:
            layout.addWidget(self.stack)
        self.message = QLabel()
        self.message.setObjectName("inputError")
        self.message.setWordWrap(True)
        self.message.hide()
        layout.addWidget(self.message)
        self.text_button = QPushButton("Usar entrada de texto")
        self.text_button.hide()
        self.text_button.clicked.connect(self._activate_text)
        layout.addWidget(self.text_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.bridge = EditorBridge(kind, self)
        self.channel = QWebChannel(self.web.page())
        self.channel.registerObject("editorBridge", self.bridge)
        self.web.page().setWebChannel(self.channel)
        self.bridge.expression_changed.connect(self._changed_visual)
        self.bridge.field_resized.connect(self._resize_field)
        self.bridge.initialized.connect(self._initialized)
        self._startup_timer = QTimer(self, singleShot=True)
        self._startup_timer.timeout.connect(self._offer_text_fallback)
        self.web.page().renderProcessTerminated.connect(self._offer_text_fallback)
        html = ASSETS / "editor.html"
        self.web.loadFinished.connect(self._check_load)
        self._startup_timer.start(10_000)
        self.web.load(QUrl.fromLocalFile(str(html.resolve())))

    def value(self) -> str:
        if self.stack.isHidden():
            raise ValueError("Activa la entrada de texto para continuar.")
        if self.stack.currentWidget() is self.web:
            return self._value
        text = self.text.toPlainText() if isinstance(self.text, QPlainTextEdit) else self.text.text()
        return text if self.kind == "output" else parse_scientific_display(text)

    def clear(self) -> None:
        self.set_value("")

    def set_value(self, text: str, *, latex: tuple[str, ...] = ()) -> None:
        self._value = scientific_notation(text) if self.kind == "output" else text
        self._latex = latex
        if self.stack.currentWidget() is self.text:
            self._set_fallback_value()
            if self.kind == "output":
                self._resize_fallback()
        if self._ready:
            self._send_value()
        self.changed.emit()

    def _set_fallback_value(self) -> None:
        text = scientific_notation(self._value)
        with QSignalBlocker(self.text):
            if isinstance(self.text, QPlainTextEdit):
                self.text.setPlainText(text)
            else:
                self.text.setText(text)

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        mode = int(dark)
        sans, mono = interface_fonts()
        colors = {
            "sans": json.dumps(sans), "mono": json.dumps(mono), "muted": theme.MUTED[mode],
            "field": theme.FIELD[mode],
            "border": theme.BORDER[mode], "ink": theme.INK[mode],
            "accent": theme.ACCENT, "on-accent": theme.ON_ACCENT,
            "accent-soft": theme.ACCENT_SOFT[mode],
            "radius": f"{theme.FIELD_RADIUS}px",
        }
        self._js(f"setEditorTheme({json.dumps('dark' if dark else 'light')}, {json.dumps(colors)})")

    def _js(self, command: str) -> None:
        if self._ready:
            self.web.page().runJavaScript(command)

    def accepts_math_keys(self) -> bool:
        return self.kind != "output" and self._ready and self.isVisible() and self.web.isVisible()

    def apply_math_key(self, command: tuple) -> None:
        if not self.accepts_math_keys():
            return
        self.web.setFocus()
        self._js("focusFormula()")
        if command == ("deleteAll",):
            self.clear()
        else:
            self._js(f"editFormula({json.dumps(command)})")

    def _initialized(self) -> None:
        self._startup_timer.stop()
        if self.stack.currentWidget() is self.text:
            return
        self._ready = True
        self.text_button.hide()
        self.message.hide()
        self.stack.show()
        self.set_dark(self._dark)
        self._js(f"configureEditor({json.dumps(self.kind)}, {json.dumps(self.name)})")
        self._send_value()

    def _send_value(self) -> None:
        if self.kind == "output":
            blocks = [("latex", formula) for formula in self._latex] if self._latex else result_blocks(self._value)
            self._js(f"setResult({json.dumps(blocks)})")
        else:
            self._js(f"setFormula({json.dumps(to_latex(self._value, self.kind))})")

    def _check_load(self, ok: bool) -> None:
        if not ok:
            self._offer_text_fallback()

    def _offer_text_fallback(self) -> None:
        self._startup_timer.stop()
        if self.stack.currentWidget() is self.text:
            return
        self._ready = False
        self.stack.hide()
        self.message.setText("El editor matemático no está disponible.")
        self.message.show()
        self.text_button.show()
        if self.kind == "output":
            self._activate_text()

    def _activate_text(self) -> None:
        if self.text_button.isHidden():
            return
        self._set_fallback_value()
        self.stack.setCurrentWidget(self.text)
        if self.kind == "output":
            self._resize_fallback()
        else:
            self.stack.setFixedHeight(112 if isinstance(self.text, QPlainTextEdit) else 48)
        self.stack.show()
        self.text_button.hide()
        if self.kind == "output":
            self.message.setText("Resultado en texto de respaldo.")
        else:
            self.message.setText("Entrada de texto de respaldo activada.")
            self.text.setFocus()

    def _changed_visual(self, value: str) -> None:
        value = from_ascii(value, self.kind)
        if self._ready and value != self._value:
            self._value = value
            self.changed.emit()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.kind == "output" and self.stack.currentWidget() is self.text:
            self._resize_fallback()

    def _resize_fallback(self) -> None:
        self.stack.setFixedHeight(max(24, self.text.heightForWidth(self.stack.width())))

    def _resize_field(self, height: int) -> None:
        if self.web.height() != height:
            self.web.setFixedHeight(height)
        if self.stack.currentWidget() is self.web and self.stack.height() != height:
            self.stack.setFixedHeight(height)
