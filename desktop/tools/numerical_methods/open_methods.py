"""Métodos abiertos con una gráfica y una traza por método."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from core.numerical_methods.handlers.real_function import RealFunction
from core.numerical_methods.handlers.root_bracket import RootStop, read_root_number
from core.numerical_methods.newton_raphson import NewtonStep, newton_raphson
from core.numerical_methods.secant import SecantStep, secant
from desktop.core.forms import FieldRow, StepView, input_actions
from desktop.core.math_input import MathInput
from desktop.core.number_display import scientific_notation
from desktop.core.widgets import SegmentedControl, Stepper, action, card, label, page_header

from .core.iteration_table import IterationTable
from .core.plot import FunctionPlot, PlotPanel


TITLE = "Métodos Abiertos"
GLYPH = "MA"
SUBTITLE = "Grafica la función y aproxima una raíz por Newton–Raphson o Secante."
EXAMPLE = "x^3 - x - 2"
TOLERANCE = "0.000001"
NEWTON_HEADERS = ("Iter.", "xₙ", "f(xₙ)", "f′(xₙ)", "xₙ₊₁", "Error absoluto", "|f(xₙ₊₁)|")
SECANT_HEADERS = (
    "Iter.", "xₙ₋₁", "xₙ", "f(xₙ₋₁)", "f(xₙ)", "xₙ₊₁", "Error absoluto", "|f(xₙ₊₁)|",
)
STOP_MESSAGES = {
    RootStop.ZERO: "La evaluación de la función dio cero.",
    RootStop.TOLERANCE: "Se alcanzó la tolerancia de error absoluto.",
    RootStop.LIMIT: "Se alcanzó el máximo de iteraciones sin cumplir la tolerancia.",
}


class OpenMethodsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(page_header(GLYPH, TITLE, SUBTITLE))

        inputs, fields = card()
        self.method = SegmentedControl("Newton–Raphson", "Secante")
        self.method.setAccessibleName("Método abierto")
        fields.addWidget(label("Método", "caption"))
        fields.addWidget(self.method, alignment=Qt.AlignmentFlag.AlignLeft)
        self.editor = MathInput(EXAMPLE, "Función f(x)")
        self.editor.changed.connect(self._invalidate)
        fields.addWidget(self.editor)
        fields.addSpacing(6)
        fields.addWidget(label("Cargar ejemplo", "caption"))
        self.examples = SegmentedControl(
            "Cargar ejemplo de Semana 13", "Práctica integradora", selected=-1,
        )
        self.examples.setAccessibleName("Cargar ejemplo")
        self.examples.activated.connect(self._example)
        fields.addWidget(self.examples, alignment=Qt.AlignmentFlag.AlignLeft)
        graph = action("Graficar función")
        graph.clicked.connect(self._graph)
        fields.addLayout(input_actions(self, graph, self._clear_inputs))
        self.graph_error = label("", "inputError")
        self.graph_error.hide()
        fields.addWidget(self.graph_error)
        layout.addWidget(inputs)

        self.plot = FunctionPlot(select_x=True)
        self.plot.x_selected.connect(self._select_initial)
        self.graph_card = PlotPanel(
            self.plot, "Haz clic en la gráfica para elegir x₀. Arrastra para mover la vista.",
        )
        layout.addWidget(self.graph_card)
        self.graph_card.hide()

        self.controls, control_layout = self.graph_card.parameters("Aproximación inicial")
        self.initial = MathInput("", "Aproximación inicial x₀", "constant")
        self.second = MathInput("", "Aproximación inicial x₁", "constant")
        self.point = SegmentedControl("x₀", "x₁")
        self.point.setAccessibleName("Punto para seleccionar en la gráfica")
        control_layout.addWidget(self.point, alignment=Qt.AlignmentFlag.AlignLeft)
        self.tolerance = MathInput(TOLERANCE, "Tolerancia E", "constant")
        self.limit = Stepper("Máximo de iteraciones", 1, 1000, 100, editable=True)
        control_layout.addWidget(FieldRow((self.initial, self.second, self.tolerance)))
        limit_field = QWidget()
        limit_layout = QVBoxLayout(limit_field)
        limit_layout.setContentsMargins(0, 0, 0, 0)
        limit_layout.setSpacing(6)
        limit_layout.addWidget(label("Máximo de iteraciones", "caption"))
        limit_layout.addWidget(self.limit, alignment=Qt.AlignmentFlag.AlignLeft)
        criterion = QWidget()
        criterion_layout = QVBoxLayout(criterion)
        criterion_layout.setContentsMargins(0, 0, 0, 0)
        criterion_layout.setSpacing(6)
        criterion_layout.addWidget(label("Criterio de parada", "caption"))
        criterion_layout.addWidget(label("Error absoluto |xₙ₊₁ − xₙ|", "muted"))
        control_layout.addWidget(FieldRow((criterion, limit_field)))
        self.initial.changed.connect(self._mark_initial)
        self.second.changed.connect(self._mark_initial)
        self.tolerance.changed.connect(self._clear_result)
        self.limit.valueChanged.connect(self._clear_result)
        calculate = action("Calcular raíz")
        calculate.clicked.connect(self._calculate)
        control_layout.addWidget(calculate, alignment=Qt.AlignmentFlag.AlignRight)
        self.solve_error = label("", "inputError")
        self.solve_error.hide()
        control_layout.addWidget(self.solve_error)

        self.result_card = QWidget()
        results = QVBoxLayout(self.result_card)
        results.setContentsMargins(0, 0, 0, 0)
        results.setSpacing(16)
        answer_card, answer_layout = card()
        answer_layout.addWidget(label("Resultado", "heading"))
        self.answer = MathInput("", "", "output")
        answer_layout.addWidget(self.answer)
        results.addWidget(answer_card)
        self.procedure_card, procedure_layout = card()
        self.walk = StepView("Iteración")
        procedure_layout.addWidget(self.walk)
        results.addWidget(self.procedure_card)
        self.table_card, table_layout = card()
        self.iterations = IterationTable(NEWTON_HEADERS)
        self.table = self.iterations.table
        self.walk.index.valueChanged.connect(self.iterations.select_iteration)
        table_layout.addWidget(self.iterations)
        results.addWidget(self.table_card)
        layout.addWidget(self.result_card)
        self.result_card.hide()
        layout.addStretch()
        self.method.currentIndexChanged.connect(self._change_method)
        self._change_method()

    @property
    def uses_secant(self) -> bool:
        return self.method.currentIndex() == 1

    def _change_method(self) -> None:
        use_secant = self.uses_secant
        self.second.setVisible(use_secant)
        self.point.setVisible(use_secant)
        self.point.setCurrentIndex(0)
        self.examples.setCurrentIndex(-1)
        self.graph_card.set_hint(
            "Haz clic para elegir x₀ y luego x₁. Usa el selector para ajustar cualquiera de los dos."
            if use_secant else "Haz clic en la gráfica para elegir x₀. Arrastra para mover la vista."
        )
        self._mark_initial()

    def _clear_result(self) -> None:
        self.result_card.hide()
        self.solve_error.hide()

    def _invalidate(self) -> None:
        self.plot.set_function(None)
        self.graph_error.hide()
        self.graph_card.hide()
        self._clear_result()

    def _clear_inputs(self) -> None:
        self.examples.setCurrentIndex(-1)
        self.point.setCurrentIndex(0)
        for field in (self.editor, self.initial, self.second, self.tolerance):
            field.clear()
        self.limit.setValue(100)

    def _example(self, index: int) -> None:
        self.editor.set_value("x^3 - 2x - 5" if index else EXAMPLE)
        self.initial.set_value("2" if index else "1" if self.uses_secant else "1.5")
        self.second.set_value("3" if index else "2")
        self.point.setCurrentIndex(0)
        self.tolerance.set_value(TOLERANCE)
        self.limit.setValue(100)

    def _graph(self) -> None:
        self._invalidate()
        try:
            function = RealFunction(self.editor.value())
        except ValueError as problem:
            self.graph_error.setText(scientific_notation(str(problem)))
            self.graph_error.show()
            return
        self.plot.set_function(function)
        self.point.setCurrentIndex(0)
        self._mark_initial()
        self.graph_card.show()

    def _select_initial(self, x: float) -> None:
        field = self.second if self.uses_secant and self.point.currentIndex() == 1 else self.initial
        field.set_value(f"{x:.12g}")
        if self.uses_secant:
            self.point.setCurrentIndex(1)

    def _mark_initial(self) -> None:
        self._clear_result()
        markers = []
        if self.plot.function:
            fields = ((self.initial, "x₀"), (self.second, "x₁")) if self.uses_secant else ((self.initial, "x₀"),)
            for field, name in fields:
                try:
                    value = read_root_number(field.value())
                except ValueError:
                    continue
                markers.append((value, name))
        self.plot.set_markers(tuple(markers))

    def _calculate(self) -> None:
        function = self.plot.function
        if function is None:
            return
        self._clear_result()
        try:
            tolerance, limit = self.tolerance.value(), self.limit.value()
            if self.uses_secant:
                result = secant(function, self.initial.value(), self.second.value(), tolerance, max_iterations=limit)
            else:
                result = newton_raphson(function, self.initial.value(), tolerance, max_iterations=limit)
        except ValueError as problem:
            self.solve_error.setText(scientific_notation(str(problem)))
            self.solve_error.show()
            return

        caption = "Raíz aproximada" if result.converged else "Última aproximación válida"
        reason = STOP_MESSAGES.get(result.stop, result.detail)
        self.answer.set_value(
            f"x ≈ {result.root:.12g}\nf({result.root:.12g}) ≈ {result.value:.8g}\n"
            f"Iteraciones: {result.iterations} · Error absoluto ≤ {result.tolerance:g}\n"
            f"|f(x)| = {abs(result.value):.8g}\n{caption}. {reason}"
        )
        if self.uses_secant:
            self.iterations.set_rows([
                (step.index, step.previous, step.x, step.previous_fx, step.fx,
                 step.next_x, step.absolute_error, abs(step.next_fx))
                for step in result.steps
            ], headers=SECANT_HEADERS)
            self.walk.set_steps(tuple(self._secant_step(step) for step in result.steps))
        else:
            self.iterations.set_rows([
                (step.index, step.x, step.fx, step.dfx, step.next_x, step.absolute_error, abs(step.next_fx))
                for step in result.steps
            ], headers=NEWTON_HEADERS)
            self.walk.set_steps(tuple(self._newton_step(step) for step in result.steps))
        self.iterations.select_iteration(1)
        self.procedure_card.setVisible(bool(result.steps))
        self.table_card.setVisible(bool(result.steps))
        self.result_card.show()
        self.graph_card.finish(self.result_card)

    @staticmethod
    def _newton_step(step: NewtonStep) -> str:
        return (
            "xₙ₊₁ = xₙ − f(xₙ) / f′(xₙ)\n"
            f"xₙ₊₁ = {step.x:.12g} − ({step.fx:.12g}) / ({step.dfx:.12g}) ≈ {step.next_x:.12g}\n"
            f"Error absoluto: |{step.next_x:.12g} − ({step.x:.12g})| ≈ {step.absolute_error:.10g}\n"
            f"|f(xₙ₊₁)| ≈ {abs(step.next_fx):.10g}"
        )

    @staticmethod
    def _secant_step(step: SecantStep) -> str:
        return (
            "xₙ₊₁ = xₙ − f(xₙ) · (xₙ − xₙ₋₁) / [f(xₙ) − f(xₙ₋₁)]\n"
            f"f({step.previous:.12g}) = {step.previous_fx:.12g}, f({step.x:.12g}) = {step.fx:.12g}\n"
            f"xₙ₊₁ = {step.x:.12g} − ({step.fx:.12g}) · "
            f"({step.x:.12g} − ({step.previous:.12g})) / "
            f"[{step.fx:.12g} − ({step.previous_fx:.12g})] ≈ {step.next_x:.12g}\n"
            f"Error absoluto: |{step.next_x:.12g} − ({step.x:.12g})| ≈ {step.absolute_error:.10g}\n"
            f"|f(xₙ₊₁)| ≈ {abs(step.next_fx):.10g}"
        )
