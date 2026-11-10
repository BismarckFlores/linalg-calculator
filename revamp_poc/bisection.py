"""Prueba del flujo de Bisección con editor matemático."""

from PySide6.QtWidgets import (
    QAbstractItemView, QFormLayout, QHeaderView, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.bisection import bisect
from core.real_function import RealFunction
from core.root_bracket import RootStop

from .math_input import MathInput
from .plot import FunctionPlot
from .widgets import action, card, label


class BisectionPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._function: RealFunction | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(label("Método de Bisección", "title"))
        layout.addWidget(label("Grafica la función y luego acota una raíz.", "muted"))

        input_card, fields = card()
        fields.addWidget(label("Función f(x)", "heading"))
        self.editor = MathInput()
        self.editor.changed.connect(self._invalidate)
        fields.addWidget(self.editor)
        examples = QHBoxLayout()
        for name, function, a, b in (
            ("Raíz de 2", "x^2 - 2", "1", "2"),
            ("Fracción con raíz", "sqrt(x+1)/2 - 1", "2", "4"),
        ):
            button = QPushButton(name)
            button.clicked.connect(lambda checked=False, f=function, lo=a, hi=b: self._example(f, lo, hi))
            examples.addWidget(button)
        examples.addStretch()
        fields.addLayout(examples)
        graph = action("Graficar función")
        graph.clicked.connect(self._graph)
        fields.addWidget(graph)
        self.graph_error = label("", "inputError")
        self.graph_error.hide()
        fields.addWidget(self.graph_error)
        layout.addWidget(input_card)

        self.graph_card, graph_layout = card()
        graph_layout.addWidget(label("Gráfica de la función", "heading"))
        self.plot = FunctionPlot()
        graph_layout.addWidget(self.plot)
        buttons = QHBoxLayout()
        for text, callback in (
            ("+  Acercar", lambda: self.plot.zoom(0.8)),
            ("−  Alejar", lambda: self.plot.zoom(1.25)),
            ("Restablecer", self.plot.reset),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        buttons.addStretch()
        graph_layout.addLayout(buttons)
        graph_layout.addWidget(label("Usa la rueda para acercar o alejar. Arrastra para mover la vista.", "muted"))
        layout.addWidget(self.graph_card)
        self.graph_card.hide()

        self.controls, control_layout = card()
        control_layout.addWidget(label("Intervalo de resolución", "heading"))
        self.a = QLineEdit("1")
        self.b = QLineEdit("2")
        self.tolerance = QLineEdit("0.0001")
        form = QFormLayout()
        for name, field in (("Extremo a", self.a), ("Extremo b", self.b), ("Tolerancia E", self.tolerance)):
            field.setAccessibleName(name)
            form.addRow(name, field)
            field.textChanged.connect(self._clear_result)
        control_layout.addLayout(form)
        control_layout.addWidget(label(
            "Parada por ancho del intervalo. Máximo de 100 iteraciones. "
            "Elige un intervalo continuo con cambio de signo.", "muted",
        ))
        calculate = action("Calcular raíz")
        calculate.clicked.connect(self._calculate)
        control_layout.addWidget(calculate)
        self.solve_error = label("", "inputError")
        self.solve_error.hide()
        control_layout.addWidget(self.solve_error)
        layout.addWidget(self.controls)
        self.controls.hide()

        self.result_card, result_layout = card()
        result_layout.addWidget(label("Resultado", "heading"))
        self.answer = label("")
        result_layout.addWidget(self.answer)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["i", "a", "b", "c", "f(c)", "Ancho"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(230)
        result_layout.addWidget(self.table)
        layout.addWidget(self.result_card)
        self.result_card.hide()
        layout.addStretch()

    def set_dark(self, dark: bool) -> None:
        self.editor.set_dark(dark)
        self.plot.dark = dark
        self.plot.update()

    def _clear_result(self) -> None:
        self.result_card.hide()
        self.solve_error.hide()
        self.plot.result = None
        self.plot.update()

    def _invalidate(self) -> None:
        self._function = None
        self.graph_error.hide()
        self.graph_card.hide()
        self.controls.hide()
        self._clear_result()

    def _example(self, function: str, a: str, b: str) -> None:
        self.editor.set_value(function)
        self.a.setText(a)
        self.b.setText(b)
        self.tolerance.setText("0.0001")

    def _graph(self) -> None:
        self._invalidate()
        try:
            self._function = RealFunction(self.editor.value())
        except ValueError as problem:
            self.graph_error.setText(str(problem))
            self.graph_error.show()
            return
        self.editor.hide_keyboard()
        self.plot.set_function(self._function)
        self.graph_card.show()
        self.controls.show()

    def _calculate(self) -> None:
        if self._function is None:
            return
        self._clear_result()
        try:
            result = bisect(self._function, self.a.text(), self.b.text(), self.tolerance.text())
        except ValueError as problem:
            self.solve_error.setText(str(problem))
            self.solve_error.show()
            return
        reason = {
            RootStop.ZERO: "La evaluación dio cero.",
            RootStop.TOLERANCE: "Se alcanzó la tolerancia del intervalo.",
            RootStop.LIMIT: "Se alcanzó el máximo de iteraciones.",
            RootStop.STAGNATION: "La precisión numérica impidió seguir reduciendo el intervalo.",
        }[result.stop]
        self.answer.setText(
            f"x ≈ {result.root:.12g}    f(x) = {result.value:.8g}    "
            f"Iteraciones: {len(result.steps)}\n{reason}"
        )
        self.table.setRowCount(len(result.steps))
        for row, step in enumerate(result.steps):
            values = (step.index, step.a, step.b, step.c, step.fc, step.width)
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(f"{value:.9g}"))
        self.plot.result = result
        self.plot.update()
        self.result_card.show()
