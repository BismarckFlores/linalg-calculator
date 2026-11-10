"""Prueba del flujo de Bisección con editor matemático."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QGridLayout, QHeaderView, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.bisection import bisect
from core.real_function import RealFunction
from core.root_bracket import RootStop

from .math_input import MathInput
from .plot import FunctionPlot
from .widgets import action, card, label, link, page_header, pill_group


class BisectionPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._function: RealFunction | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(page_header(
            "½", "Método de Bisección", "Encuentra una raíz de f(x) = 0 reduciendo un intervalo a la mitad.",
        ))

        input_card, fields = card()
        self.editor = MathInput("x^2 - 2", "Función f(x)")
        self.editor.changed.connect(self._invalidate)
        fields.addWidget(self.editor)
        fields.addSpacing(6)
        fields.addWidget(label("Cargar ejemplo", "caption"))
        presets, examples = pill_group()
        for name, function, a, b in (
            ("Raíz de 2", "x^2 - 2", "1", "2"),
            ("Fracción con raíz", "sqrt(x+1)/2 - 1", "2", "4"),
        ):
            button = QPushButton(name)
            button.clicked.connect(lambda checked=False, f=function, lo=a, hi=b: self._example(f, lo, hi))
            examples.addWidget(button)
        fields.addWidget(presets, alignment=Qt.AlignmentFlag.AlignLeft)
        graph = action("Graficar función")
        graph.clicked.connect(self._graph)
        fields.addWidget(graph, alignment=Qt.AlignmentFlag.AlignRight)
        self.graph_error = label("", "inputError")
        self.graph_error.hide()
        fields.addWidget(self.graph_error)
        layout.addWidget(input_card)

        self.graph_card, graph_layout = card()
        graph_layout.addWidget(label("Gráfica de la función", "heading"))
        self.plot = FunctionPlot()
        buttons = QHBoxLayout()
        for text, callback in (
            ("+  Acercar", lambda: self.plot.zoom(0.8)),
            ("−  Alejar", lambda: self.plot.zoom(1.25)),
            ("Restablecer", self.plot.reset),
        ):
            button = link(text)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        buttons.addStretch()
        graph_layout.addLayout(buttons)
        graph_layout.addWidget(self.plot)
        graph_layout.addWidget(label("Usa la rueda para acercar o alejar. Arrastra para mover la vista.", "muted"))
        layout.addWidget(self.graph_card)
        self.graph_card.hide()

        self.controls, control_layout = card()
        control_layout.addWidget(label("Intervalo de resolución", "heading"))
        self.a = MathInput("1", "Extremo inferior a", "number")
        self.b = MathInput("2", "Extremo superior b", "number")
        self.tolerance = MathInput("0.0001", "Tolerancia E", "number")
        form = QGridLayout()
        form.setHorizontalSpacing(16)
        for index, field in enumerate((self.a, self.b, self.tolerance)):
            row, column = divmod(index, 2)
            form.addWidget(field, row, column)
            field.changed.connect(self._clear_result)
        control_layout.addLayout(form)
        control_layout.addWidget(label(
            "Parada por ancho del intervalo. Máximo de 100 iteraciones. "
            "Elige un intervalo continuo con cambio de signo.", "muted",
        ))
        calculate = action("Calcular raíz")
        calculate.clicked.connect(self._calculate)
        control_layout.addWidget(calculate, alignment=Qt.AlignmentFlag.AlignRight)
        self.solve_error = label("", "inputError")
        self.solve_error.hide()
        control_layout.addWidget(self.solve_error)
        layout.addWidget(self.controls)
        self.controls.hide()

        self.result_card, result_layout = card()
        result_layout.addWidget(label("Resultado", "heading"))
        self.answer = MathInput("", "", "output")
        result_layout.addWidget(self.answer)
        self.summary = label("", "muted")
        result_layout.addWidget(self.summary)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["i", "a", "b", "c", "f(c)", "Ancho"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(230)
        result_layout.addWidget(self.table)
        layout.addWidget(self.result_card)
        self.result_card.hide()
        layout.addStretch()

    def set_dark(self, dark: bool) -> None:
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
        self.a.set_value(a)
        self.b.set_value(b)
        self.tolerance.set_value("0.0001")

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
            result = bisect(self._function, self.a.value(), self.b.value(), self.tolerance.value())
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
        self.answer.set_value(f"x ≈ {result.root:.12g}\nf(x) = {result.value:.8g}")
        self.summary.setText(f"Iteraciones: {len(result.steps)}\n{reason}")
        self.table.setRowCount(len(result.steps))
        for row, step in enumerate(result.steps):
            values = (step.index, step.a, step.b, step.c, step.fc, step.width)
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(f"{value:.9g}"))
        self.plot.result = result
        self.plot.update()
        self.result_card.show()
