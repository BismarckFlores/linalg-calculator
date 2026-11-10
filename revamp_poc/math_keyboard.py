"""Teclado Qt que emite comandos de edición para el campo matemático."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QPushButton


KEYS = (
    (
        ("7", "7"), ("8", "8"), ("9", "9"), ("÷", r"\frac{#@}{#?}", "Insertar fracción"),
        ("x", "x"), ("π", r"\pi"), ("e", "e"), ("xⁿ", "#@^{#?}", "Insertar potencia"),
    ),
    (
        ("4", "4"), ("5", "5"), ("6", "6"), ("×", r"\times", "Multiplicar"),
        ("√", r"\sqrt{#0}", "Insertar raíz cuadrada"), ("(", "("), (")", ")"),
        ("←", ("moveToPreviousChar",), "Mover a la izquierda"),
    ),
    (
        ("1", "1"), ("2", "2"), ("3", "3"), ("−", "-", "Restar"),
        ("sin", r"\sin\left(#0\right)", "Insertar seno"),
        ("cos", r"\cos\left(#0\right)", "Insertar coseno"),
        ("tan", r"\tan\left(#0\right)", "Insertar tangente"),
        ("→", ("moveToNextChar",), "Mover a la derecha"),
    ),
    (
        ("0", "0"), (".", ".", "Punto decimal"), ("+", "+", "Sumar"),
        ("⌫", ("deleteBackward",), "Borrar hacia atrás"),
        ("ln", r"\ln\left(#0\right)", "Insertar logaritmo natural"),
        ("abs", r"\operatorname{abs}\left(#0\right)", "Insertar valor absoluto"),
        ("↶", ("undo",), "Deshacer"), ("↷", ("redo",), "Rehacer"),
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
        for column in range(len(KEYS[0])):
            grid.setColumnStretch(column, 1)
        for row, keys in enumerate(KEYS):
            for column, (symbol, value, *description) in enumerate(keys):
                button = QPushButton(symbol)
                button.setAccessibleName(description[0] if description else symbol)
                # Pulsar con el ratón conserva el cursor y la selección del editor.
                button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
                command = value
                if isinstance(value, str):
                    command = ("insert", value, {"format": "latex", "selectionMode": "placeholder"})
                button.clicked.connect(lambda checked=False, cmd=command: self.command.emit(cmd))
                grid.addWidget(button, row, column)
