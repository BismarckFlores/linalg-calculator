"""Campo MathLive local con entrada de texto de respaldo."""

import ast
import json
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from core.real_function import RealFunction
from ui import theme_tokens as theme

from .math_keyboard import MathKeyboard


def formula_latex(text: str) -> str:
    """Convierte una expresión ya validada en LaTeX para el modo visual."""
    if not text.strip():
        return ""
    function = RealFunction(text)

    def render(node: ast.expr, minimum: int = 0) -> str:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                return str(node.value)
            token = ast.get_source_segment(function._source, node)
            number = token.replace("_", "") if token else str(node.value)
            if "e" in number.lower():
                mantissa, exponent = number.lower().split("e")
                return rf"\left({mantissa}\times 10^{{{int(exponent)}}}\right)"
            return number
        if isinstance(node, ast.Name):
            return r"\pi" if node.id == "pi" else node.id
        if isinstance(node, ast.UnaryOp):
            sign = "-" if isinstance(node.op, ast.USub) else "+"
            precedence = 3
            content = sign + render(node.operand, precedence)
        elif isinstance(node, ast.Call):
            name = node.func.id
            argument = render(node.args[0])
            if name == "sqrt":
                return rf"\sqrt{{{argument}}}"
            if name in ("sin", "cos", "tan", "exp", "ln", "log"):
                return rf"\{name}\left({argument}\right)"
            return rf"\operatorname{{{name}}}\left({argument}\right)"
        else:
            assert isinstance(node, ast.BinOp)
            if isinstance(node.op, ast.Div):
                precedence = 2
                content = rf"\frac{{{render(node.left)}}}{{{render(node.right)}}}"
            elif isinstance(node.op, ast.Pow):
                precedence = 4
                base = render(node.left, precedence + 1)
                content = rf"{base}^{{{render(node.right)}}}"
            else:
                sign, precedence = {
                    ast.Add: ("+", 1), ast.Sub: ("-", 1), ast.Mult: (r"\cdot ", 2),
                }[type(node.op)]
                content = render(node.left, precedence) + sign + render(node.right, precedence + 1)
        return rf"\left({content}\right)" if precedence < minimum else content

    return render(function._tree)


class EditorBridge(QObject):
    """Recibe la expresión y la altura del campo de MathLive."""

    expression_changed = Signal(str)
    field_resized = Signal(int)
    initialized = Signal()

    @Slot(str)
    def changed(self, value: str) -> None:
        self.expression_changed.emit(value)

    @Slot(str, result=str)
    def latexForPaste(self, text: str) -> str:
        try:
            return formula_latex(text)
        except ValueError:
            # MathLive también permite pegar fragmentos que aún no son una función completa.
            return ""

    @Slot(int)
    def viewHeight(self, height: int) -> None:
        self.field_resized.emit(height)

    @Slot()
    def ready(self) -> None:
        self.initialized.emit()


class MathInput(QWidget):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._value = "x^2 - 2"
        self._ready = False
        self._dark = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.keyboard_button = QPushButton("⌨  Teclado", checkable=True)
        self.keyboard_button.setObjectName("keyboardToggle")
        self.keyboard_button.setEnabled(False)
        shortcut = QShortcut(QKeySequence("Alt+Shift+Space"), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.keyboard_button.click)
        layout.addWidget(self.keyboard_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.stack = QStackedWidget()
        self.web = QWebEngineView()
        self.web.setFixedHeight(60)
        self.text = QLineEdit(self._value)
        self.text.setAccessibleName("Función f(x)")
        self.text.textEdited.connect(lambda: self.changed.emit())
        self.stack.addWidget(self.web)
        self.stack.addWidget(self.text)
        # El tamaño de la página sigue solo el modo visible.
        self.stack.setFixedHeight(60)
        layout.addWidget(self.stack)
        self.keyboard = MathKeyboard()
        self.keyboard.hide()
        self.keyboard.command.connect(self._edit_formula)
        self.keyboard_button.toggled.connect(self.keyboard.setVisible)
        self.keyboard_button.clicked.connect(self._focus_formula)
        layout.addWidget(self.keyboard)
        self.message = QLabel()
        self.message.setObjectName("inputError")
        self.message.setWordWrap(True)
        self.message.hide()
        layout.addWidget(self.message)
        self.text_button = QPushButton("Usar entrada de texto")
        self.text_button.hide()
        self.text_button.clicked.connect(self._activate_text)
        layout.addWidget(self.text_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.bridge = EditorBridge(self)
        self.channel = QWebChannel(self.web.page())
        self.channel.registerObject("editorBridge", self.bridge)
        self.web.page().setWebChannel(self.channel)
        self.bridge.expression_changed.connect(self._changed_visual)
        self.bridge.field_resized.connect(self._resize_field)
        self.bridge.initialized.connect(self._initialized)
        self._startup_timer = QTimer(self, singleShot=True)
        self._startup_timer.timeout.connect(self._offer_text_fallback)
        self.web.page().renderProcessTerminated.connect(self._offer_text_fallback)
        html = Path(__file__).parent / "assets" / "editor.html"
        self.web.loadFinished.connect(self._check_load)
        self._startup_timer.start(10_000)
        self.web.load(QUrl.fromLocalFile(str(html.resolve())))

    def value(self) -> str:
        if self.stack.isHidden():
            raise ValueError("Activa la entrada de texto para continuar.")
        return self.text.text() if self.stack.currentWidget() is self.text else self._value

    def hide_keyboard(self) -> None:
        self.keyboard_button.setChecked(False)

    def set_value(self, text: str) -> None:
        self.text.setText(text)
        self._value = text
        if self._ready:
            self._js(f"setFormula({json.dumps(formula_latex(text))})")
        self.changed.emit()

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        mode = int(dark)
        colors = {
            "card": theme.CARD[mode], "field": theme.FIELD[mode],
            "border": theme.BORDER[mode], "ink": theme.INK[mode],
            "accent": theme.ACCENT, "on-accent": theme.ON_ACCENT,
            "accent-soft": theme.ACCENT_SOFT[mode],
            "radius": f"{theme.FIELD_RADIUS}px",
        }
        self.web.page().setBackgroundColor(QColor(colors["card"]))
        self._js(f"setEditorTheme({json.dumps('dark' if dark else 'light')}, {json.dumps(colors)})")

    def _js(self, command: str) -> None:
        if self._ready:
            self.web.page().runJavaScript(command)

    def _edit_formula(self, command: tuple) -> None:
        self._focus_formula()
        self._js(f"editFormula({json.dumps(command)})")

    def _focus_formula(self) -> None:
        self.web.setFocus()
        self._js("focusFormula()")

    def _initialized(self) -> None:
        self._startup_timer.stop()
        if self.stack.currentWidget() is self.text:
            return
        self._ready = True
        self.text_button.hide()
        self.message.hide()
        self.stack.show()
        self.keyboard_button.setEnabled(True)
        self.keyboard_button.show()
        self.set_dark(self._dark)
        self._js(f"setFormula({json.dumps(formula_latex(self._value))})")

    def _check_load(self, ok: bool) -> None:
        if not ok:
            self._offer_text_fallback()

    def _offer_text_fallback(self) -> None:
        self._startup_timer.stop()
        if self.stack.currentWidget() is self.text:
            return
        self._ready = False
        self.hide_keyboard()
        self.keyboard_button.setEnabled(False)
        self.keyboard_button.hide()
        self.stack.hide()
        self.message.setText("El editor matemático no está disponible.")
        self.message.show()
        self.text_button.show()

    def _activate_text(self) -> None:
        if self.text_button.isHidden():
            return
        self.text.setText(self._value)
        self.stack.setCurrentWidget(self.text)
        self.stack.setFixedHeight(40)
        self.stack.show()
        self.text_button.hide()
        self.message.setText("Entrada de texto de respaldo activada.")
        self.text.setFocus()

    def _changed_visual(self, value: str) -> None:
        value = value.replace("a b s (", "abs(").replace("l o g10 (", "log10(")
        if self._ready and value != self._value:
            self._value = value
            self.changed.emit()

    def _resize_field(self, height: int) -> None:
        if self.web.height() != height:
            self.web.setFixedHeight(height)
        if self.stack.currentWidget() is self.web and self.stack.height() != height:
            self.stack.setFixedHeight(height)
