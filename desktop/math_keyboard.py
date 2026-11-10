"""Teclado Qt que emite comandos de edición para el campo matemático."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QPushButton

from .widgets import label


KEYS = (
    (
        ("xⁿ", "#@^{#?}", "Insertar potencia", "template"),
        ("a⁄b", r"\frac{#@}{#?}", "Insertar fracción", "template"),
        ("√", r"\sqrt{#0}", "Insertar raíz cuadrada", "template"),
        ("π", r"\pi", "Insertar pi", "symbol"),
        ("←", ("moveToPreviousChar",), "Mover a la izquierda", "edit"),
        ("→", ("moveToNextChar",), "Mover a la derecha", "edit"),
        ("⌫", ("deleteBackward",), "Borrar hacia atrás", "edit"),
    ),
    (
        ("sin", r"\sin\left(#0\right)", "Insertar seno", "symbol"),
        ("cos", r"\cos\left(#0\right)", "Insertar coseno", "symbol"),
        ("tan", r"\tan\left(#0\right)", "Insertar tangente", "symbol"),
        ("ln", r"\ln\left(#0\right)", "Insertar logaritmo natural", "symbol"),
        ("abs", r"\operatorname{abs}\left(#0\right)", "Insertar valor absoluto", "symbol"),
        ("↶", ("undo",), "Deshacer", "edit"),
        ("↷", ("redo",), "Rehacer", "edit"),
    ),
)


class MathKeyboard(QFrame):
    command = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("mathKeyboard")
        self.setAccessibleName("Teclado matemático")
        grid = QGridLayout(self)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(6)
        columns = len(KEYS[0])
        grid.addWidget(label(
            "Usa ^ para potencias y / para fracciones. Pulsa → para salir del exponente o denominador.",
            "caption",
        ), 0, 0, 1, columns)
        for column in range(columns):
            grid.setColumnStretch(column, 1)
        for row, keys in enumerate(KEYS, start=1):
            for column, (symbol, value, description, role) in enumerate(keys):
                button = QPushButton(symbol)
                button.setAccessibleName(description)
                button.setToolTip(description)
                button.setProperty("mathRole", role)
                # Pulsar con el ratón conserva el cursor y la selección del editor.
                button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
                command = value
                if isinstance(value, str):
                    command = ("insert", value, {"format": "latex", "selectionMode": "placeholder"})
                button.clicked.connect(lambda checked=False, cmd=command: self.command.emit(cmd))
                grid.addWidget(button, row, column)
