"""Entrada Qt con dos modos y un campo MathLive local."""

import ast
import json
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QLineEdit, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from core.real_function import RealFunction


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
    """Recibe el texto y el espacio que solicita el teclado."""

    expression_changed = Signal(str)
    keyboard_resized = Signal(int)
    initialized = Signal()

    @Slot(str)
    def changed(self, value: str) -> None:
        self.expression_changed.emit(value)

    @Slot(int)
    def viewHeight(self, height: int) -> None:
        self.keyboard_resized.emit(height)

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
        choices = QHBoxLayout()
        self._buttons = QButtonGroup(self)
        self.visual_button = QPushButton("Editor matemático", checkable=True, checked=True)
        self.text_button = QPushButton("Texto", checkable=True)
        self._buttons.addButton(self.visual_button, 0)
        self._buttons.addButton(self.text_button, 1)
        choices.addWidget(self.visual_button)
        choices.addWidget(self.text_button)
        choices.addStretch()
        self.keyboard_button = QPushButton("⌨  Teclado")
        self.keyboard_button.setEnabled(False)
        self.keyboard_button.clicked.connect(lambda: self._js("toggleKeyboard()"))
        choices.addWidget(self.keyboard_button)
        layout.addLayout(choices)

        self.stack = QStackedWidget()
        self.web = QWebEngineView()
        self.web.setFixedHeight(74)
        self.text = QLineEdit(self._value)
        self.text.setAccessibleName("Función f(x)")
        self.text.textEdited.connect(lambda: self.changed.emit())
        self.stack.addWidget(self.web)
        self.stack.addWidget(self.text)
        # El tamaño de la página sigue solo el modo visible.
        self.stack.setFixedHeight(74)
        layout.addWidget(self.stack)
        self.message = QLabel()
        self.message.setObjectName("inputError")
        self.message.setWordWrap(True)
        self.message.hide()
        layout.addWidget(self.message)

        self.bridge = EditorBridge(self)
        self.channel = QWebChannel(self.web.page())
        self.channel.registerObject("editorBridge", self.bridge)
        self.web.page().setWebChannel(self.channel)
        self.bridge.expression_changed.connect(self._changed_visual)
        self.bridge.keyboard_resized.connect(self._resize_keyboard)
        self.bridge.initialized.connect(self._initialized)
        self._buttons.idClicked.connect(self._choose_mode)
        html = Path(__file__).parent / "assets" / "editor.html"
        self.web.loadFinished.connect(self._check_load)
        self.web.load(QUrl.fromLocalFile(str(html.resolve())))

    def value(self) -> str:
        return self.text.text() if self.stack.currentIndex() == 1 else self._value

    def hide_keyboard(self) -> None:
        self._js("hideKeyboard()")

    def set_value(self, text: str) -> None:
        self.text.setText(text)
        self._value = text
        if self.stack.currentIndex() == 0:
            self._js(f"setFormula({json.dumps(formula_latex(text))})")
        self.changed.emit()

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        self.web.page().setBackgroundColor(QColor("#1c2432" if dark else "#ffffff"))
        self._js(f"setEditorDark({json.dumps(dark)})")

    def _js(self, command: str) -> None:
        if self._ready:
            self.web.page().runJavaScript(command)

    def _initialized(self) -> None:
        self._ready = True
        self.keyboard_button.setEnabled(self.stack.currentIndex() == 0)
        self.set_dark(self._dark)
        if self.stack.currentIndex() == 0:
            self._js(f"setFormula({json.dumps(formula_latex(self._value))})")

    def _check_load(self, ok: bool) -> None:
        if not ok:
            self._choose_mode(1)
            self.message.setText("El editor matemático no se pudo cargar. Puedes escribir la función en Texto.")
            self.message.show()

    def _changed_visual(self, value: str) -> None:
        value = value.replace("a b s (", "abs(").replace("l o g10 (", "log10(")
        if value != self._value:
            self._value = value
            if self.stack.currentIndex() == 0:
                self.changed.emit()

    def _resize_keyboard(self, height: int) -> None:
        if self.web.height() != height:
            self.web.setFixedHeight(height)
        if self.stack.currentIndex() == 0 and self.stack.height() != height:
            self.stack.setFixedHeight(height)

    def _choose_mode(self, index: int) -> None:
        if index == self.stack.currentIndex():
            return
        if index == 0:
            try:
                latex = formula_latex(self.text.text())
            except ValueError as problem:
                self.text_button.setChecked(True)
                self.message.setText(str(problem))
                self.message.show()
                return
            self._value = self.text.text()
            self._js(f"setFormula({json.dumps(latex)})")
            self.stack.setFixedHeight(self.web.height())
        else:
            self.hide_keyboard()
            self.text.setText(self._value)
            self.stack.setFixedHeight(46)
        self.stack.setCurrentIndex(index)
        self._buttons.button(index).setChecked(True)
        self.keyboard_button.setEnabled(index == 0 and self._ready)
        self.message.hide()
