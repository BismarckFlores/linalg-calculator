"""Página compartida de los métodos de búsqueda por intervalo."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from core.numerical_methods.handlers.real_function import RealFunction
from core.numerical_methods.handlers.root_bracket import BracketResult, BracketStep, RootCriterion, RootStop

from desktop.core.forms import StepView, input_actions
from desktop.core.math_input import MathInput
from desktop.core.number_display import scientific_notation
from desktop.core.widgets import SegmentedControl, Stepper, action, card, label, page_header

from .iteration_table import IterationTable
from .plot import FunctionPlot


CRITERIA = {
    RootCriterion.WIDTH: "Ancho b − a",
    RootCriterion.RELATIVE: "Error relativo (%)",
    RootCriterion.RESIDUAL: "Residuo |f(c)|",
}
TABLE_HEADERS = ("i", "a", "b", "c", "f(a)", "f(b)", "f(c)", "Ancho", "Error %")


class RootBracketPage(QWidget):
    """Flujo de entrada, gráfica y resultados de un método de intervalo."""

    title: str
    glyph: str
    subtitle: str
    formula: str
    criteria: tuple[RootCriterion, ...]
    solve: Callable[..., BracketResult]
    presets: tuple[tuple[str, str, str, str, str, RootCriterion], ...]

    def __init__(self) -> None:
        super().__init__()
        self._function: RealFunction | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(page_header(
            self.glyph, self.title, self.subtitle,
        ))

        input_card, fields = card()
        _, function, a, b, tolerance, _ = self.presets[0]
        self.editor = MathInput(function, "Función f(x)")
        self.editor.changed.connect(self._invalidate)
        fields.addWidget(self.editor)
        fields.addSpacing(6)
        fields.addWidget(label("Cargar ejemplo", "caption"))
        self.examples = SegmentedControl(*(item[0] for item in self.presets), selected=-1)
        self.examples.setAccessibleName("Cargar ejemplo")
        self.examples.activated.connect(lambda index: self._example(*self.presets[index][1:]))
        fields.addWidget(self.examples, alignment=Qt.AlignmentFlag.AlignLeft)
        graph = action("Graficar función")
        graph.clicked.connect(self._graph)
        fields.addLayout(input_actions(self, graph, self._clear_inputs))
        self.graph_error = label("", "inputError")
        self.graph_error.hide()
        fields.addWidget(self.graph_error)
        layout.addWidget(input_card)

        self.graph_card, graph_layout = card()
        graph_layout.addWidget(label("Gráfica de la función", "heading"))
        self.plot = FunctionPlot()
        graph_layout.addLayout(self.plot.controls("Maximizar", self.plot.expand))
        graph_layout.addWidget(self.plot)
        graph_layout.addWidget(label("Usa la rueda para acercar o alejar. Arrastra para mover la vista.", "muted"))
        layout.addWidget(self.graph_card)
        self.graph_card.hide()

        self.controls, control_layout = card()
        control_layout.addWidget(label("Intervalo de resolución", "heading"))
        self.a = MathInput(a, "Extremo inferior a", "number")
        self.b = MathInput(b, "Extremo superior b", "number")
        self.tolerance = MathInput(tolerance, "Tolerancia E", "number")
        self.limit = Stepper("Máximo de iteraciones", 1, 1000, 100, editable=True)
        form = QGridLayout()
        form.setHorizontalSpacing(16)
        for index, field in enumerate((self.a, self.b, self.tolerance)):
            row, column = divmod(index, 2)
            form.addWidget(field, row, column)
            field.changed.connect(self._clear_result)
        limit_field = QVBoxLayout()
        limit_field.setSpacing(6)
        limit_field.addWidget(label("Máximo de iteraciones", "caption"))
        limit_field.addWidget(self.limit, alignment=Qt.AlignmentFlag.AlignLeft)
        form.addLayout(limit_field, 1, 1)
        control_layout.addLayout(form)
        self.criterion = SegmentedControl(*(CRITERIA[value] for value in self.criteria))
        self.criterion.setAccessibleName("Criterio de parada")
        self.criterion.currentIndexChanged.connect(self._clear_result)
        self.limit.valueChanged.connect(self._clear_result)
        control_layout.addWidget(label("Criterio de parada", "caption"))
        control_layout.addWidget(self.criterion)
        control_layout.addWidget(label(
            "Elige un intervalo donde la función sea continua y cambie de signo. "
            "Para el error relativo, 1 representa 1 %.", "muted",
        ))
        calculate = action("Calcular raíz")
        calculate.clicked.connect(self._calculate)
        control_layout.addWidget(calculate, alignment=Qt.AlignmentFlag.AlignRight)
        self.solve_error = label("", "inputError")
        self.solve_error.hide()
        control_layout.addWidget(self.solve_error)
        layout.addWidget(self.controls)
        self.controls.hide()

        self.result_card = QWidget()
        results = QVBoxLayout(self.result_card)
        results.setContentsMargins(0, 0, 0, 0)
        results.setSpacing(16)
        answer_card, result_layout = card()
        results.addWidget(answer_card)
        result_layout.addWidget(label("Resultado", "heading"))
        self.answer = MathInput("", "", "output")
        result_layout.addWidget(self.answer)
        self.walk = StepView("Iteración")
        procedure_card, procedure_layout = card()
        procedure_layout.addWidget(self.walk)
        results.addWidget(procedure_card)
        table_card, table_layout = card()
        results.addWidget(table_card)
        self.iterations = IterationTable(TABLE_HEADERS)
        self.table = self.iterations.table
        self.format = self.iterations.format
        self.decimals = self.iterations.decimals
        self.table_page = self.iterations.page
        self.walk.index.valueChanged.connect(self.iterations.select_iteration)
        table_layout.addWidget(self.iterations)
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
        self.plot.set_function(None)
        self.graph_error.hide()
        self.graph_card.hide()
        self.controls.hide()
        self._clear_result()

    def _clear_inputs(self) -> None:
        self.examples.setCurrentIndex(-1)
        for field in (self.a, self.b, self.tolerance, self.editor):
            field.clear()

    def _example(self, function: str, a: str, b: str, tolerance: str, criterion: RootCriterion) -> None:
        self.editor.set_value(function)
        self.a.set_value(a)
        self.b.set_value(b)
        self.tolerance.set_value(tolerance)
        self.criterion.setCurrentIndex(self.criteria.index(criterion))
        self.limit.setValue(100)

    def _graph(self) -> None:
        self._invalidate()
        try:
            self._function = RealFunction(self.editor.value())
        except ValueError as problem:
            self.graph_error.setText(scientific_notation(str(problem)))
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
            result = self.solve(
                self._function, self.a.value(), self.b.value(), self.tolerance.value(),
                criterion=self.criteria[self.criterion.currentIndex()],
                max_iterations=self.limit.value(),
            )
        except ValueError as problem:
            self.solve_error.setText(scientific_notation(str(problem)))
            self.solve_error.show()
            return
        reason = {
            RootStop.ZERO: "La evaluación dio cero.",
            RootStop.TOLERANCE: "Se alcanzó la tolerancia seleccionada.",
            RootStop.LIMIT: "Sin convergencia: se alcanzó el máximo de iteraciones.",
            RootStop.STAGNATION: "Sin convergencia: la aproximación coincide con un extremo por redondeo.",
        }[result.stop]
        relative = result.steps[-1].relative_error if result.steps else None
        relative_text = "—" if relative is None else f"{relative:.10g} %"
        self.answer.set_value(
            f"x ≈ {result.root:.12g}\nf({result.root:.12g}) ≈ {result.value:.8g}\n"
            f"Iteraciones: {len(result.steps)} · {CRITERIA[result.criterion]} < {result.tolerance:g}\n"
            f"|f(c)| = {abs(result.value):.8g}\n{reason}\n"
            f"Intervalo final: [{result.a:.12g}, {result.b:.12g}]\n"
            f"Cota en x si hay continuidad: {result.bound:.10g}\n"
            f"Cambio relativo: {relative_text}"
        )
        self.plot.show_result(result)
        self.iterations.set_rows([
            (step.index, step.a, step.b, step.c, step.fa, step.fb, step.fc, step.width, step.relative_error)
            for step in result.steps
        ])
        steps = tuple(self._step_text(step, len(result.steps)) for step in result.steps)
        if not steps:
            steps = (f"Un extremo inicial es raíz.\nf({result.root:.9g}) = 0",)
        self.walk.set_steps(steps)
        self.iterations.select_iteration(1)
        self.result_card.show()

    def _step_text(self, step: BracketStep, count: int) -> str:
        detail = (
            f"Extremos: a = {step.a:.9g}, b = {step.b:.9g}\n"
            f"Evaluación: f(a) = {step.fa:.9g}, f(b) = {step.fb:.9g}\n"
            f"c = {self.formula} ≈ {step.c:.9g}\n"
            f"Sustitución: f({step.c:.9g}) ≈ {step.fc:.9g}"
        )
        if step.index < count:
            a, b = (step.a, step.c) if step.keep_left else (step.c, step.b)
            detail += f"\nEl cambio de signo se conserva en [{a:.9g}, {b:.9g}]."
        else:
            detail += "\nEl método se detiene en esta iteración."
        return detail
