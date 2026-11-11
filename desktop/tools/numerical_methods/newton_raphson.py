"""Página de Newton–Raphson con selección gráfica de la aproximación inicial."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from core.numerical_methods.handlers.real_function import RealFunction
from core.numerical_methods.handlers.root_bracket import RootStop, read_root_number
from core.numerical_methods.newton_raphson import NewtonStep, newton_raphson
from desktop.core.forms import FieldRow, StepView, input_actions
from desktop.core.math_input import MathInput
from desktop.core.number_display import scientific_notation
from desktop.core.widgets import SegmentedControl, Stepper, action, card, label, page_header

from .core.iteration_table import IterationTable
from .core.plot import FunctionPlot


TITLE = "Newton–Raphson"
GLYPH = "NR"
SUBTITLE = "Grafica la función, elige x₀ y aproxima una raíz mediante la derivada automática."
EXAMPLE = "x^3 - x - 2"
TOLERANCE = "0.000001"
TABLE_HEADERS = ("Iter.", "xₙ", "f(xₙ)", "f′(xₙ)", "xₙ₊₁", "Error absoluto")
STOP_MESSAGES = {
    RootStop.ZERO: "La evaluación de la función dio cero.",
    RootStop.TOLERANCE: "Se alcanzó la tolerancia de error absoluto.",
    RootStop.LIMIT: "Se alcanzó el máximo de iteraciones sin cumplir la tolerancia.",
}


class NewtonRaphsonPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(page_header(GLYPH, TITLE, SUBTITLE))

        inputs, fields = card()
        self.editor = MathInput(EXAMPLE, "Función f(x)")
        self.editor.changed.connect(self._invalidate)
        fields.addWidget(self.editor)
        fields.addSpacing(6)
        fields.addWidget(label("Cargar ejemplo", "caption"))
        self.examples = SegmentedControl("Cargar ejemplo de Semana 13", selected=-1)
        self.examples.setAccessibleName("Cargar ejemplo")
        self.examples.activated.connect(lambda _: self._example())
        fields.addWidget(self.examples, alignment=Qt.AlignmentFlag.AlignLeft)
        graph = action("Graficar función")
        graph.clicked.connect(self._graph)
        fields.addLayout(input_actions(self, graph, self._clear_inputs))
        self.graph_error = label("", "inputError")
        self.graph_error.hide()
        fields.addWidget(self.graph_error)
        layout.addWidget(inputs)

        self.graph_card, graph_layout = card()
        graph_layout.addWidget(label("Gráfica de la función", "heading"))
        self.plot = FunctionPlot(select_x=True)
        self.plot.x_selected.connect(self._select_initial)
        graph_layout.addLayout(self.plot.controls("Maximizar", self.plot.expand))
        graph_layout.addWidget(self.plot)
        graph_layout.addWidget(label(
            "Haz clic en la gráfica para elegir x₀. Arrastra para mover la vista y usa la rueda para ajustar el zoom.",
            "muted",
        ))
        layout.addWidget(self.graph_card)
        self.graph_card.hide()

        self.controls, control_layout = card()
        control_layout.addWidget(label("Aproximación inicial", "heading"))
        self.initial = MathInput("", "Aproximación inicial x₀", "number")
        self.tolerance = MathInput(TOLERANCE, "Tolerancia E", "number")
        self.limit = Stepper("Máximo de iteraciones", 1, 1000, 100, editable=True)
        control_layout.addWidget(FieldRow((self.initial, self.tolerance)))
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
        self.tolerance.changed.connect(self._clear_result)
        self.limit.valueChanged.connect(self._clear_result)
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
        self.iterations = IterationTable(TABLE_HEADERS)
        self.table = self.iterations.table
        self.walk.index.valueChanged.connect(self.iterations.select_iteration)
        table_layout.addWidget(self.iterations)
        results.addWidget(self.table_card)
        layout.addWidget(self.result_card)
        self.result_card.hide()
        layout.addStretch()

    def _clear_result(self) -> None:
        self.result_card.hide()
        self.solve_error.hide()

    def _invalidate(self) -> None:
        self.plot.set_function(None)
        self.graph_error.hide()
        self.graph_card.hide()
        self.controls.hide()
        self._clear_result()

    def _clear_inputs(self) -> None:
        self.examples.setCurrentIndex(-1)
        for field in (self.editor, self.initial, self.tolerance):
            field.clear()
        self.limit.setValue(100)

    def _example(self) -> None:
        self.editor.set_value(EXAMPLE)
        self.initial.set_value("1.5")
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
        self.editor.hide_keyboard()
        self.plot.set_function(function)
        self._mark_initial()
        self.graph_card.show()
        self.controls.show()

    def _select_initial(self, x: float) -> None:
        self.initial.set_value(f"{x:.12g}")

    def _mark_initial(self) -> None:
        self._clear_result()
        try:
            markers = ((read_root_number(self.initial.value()), "x₀"),) if self.plot.function else ()
        except ValueError:
            markers = ()
        self.plot.set_markers(markers)

    def _calculate(self) -> None:
        function = self.plot.function
        if function is None:
            return
        self._clear_result()
        try:
            result = newton_raphson(
                function, self.initial.value(), self.tolerance.value(), max_iterations=self.limit.value(),
            )
        except ValueError as problem:
            self.solve_error.setText(scientific_notation(str(problem)))
            self.solve_error.show()
            return

        caption = "Raíz aproximada" if result.converged else "Última aproximación válida"
        reason = STOP_MESSAGES.get(result.stop, result.detail)
        self.answer.set_value(
            f"x ≈ {result.root:.12g}\nf({result.root:.12g}) ≈ {result.value:.8g}\n"
            f"Iteraciones: {result.iterations} · Error absoluto < {result.tolerance:g}\n"
            f"|f(x)| = {abs(result.value):.8g}\n{caption}. {reason}"
        )
        self.iterations.set_rows([
            (step.index, step.x, step.fx, step.dfx, step.next_x, step.absolute_error)
            for step in result.steps
        ])
        self.walk.set_steps(tuple(self._step_text(step) for step in result.steps))
        self.iterations.select_iteration(1)
        self.procedure_card.setVisible(bool(result.steps))
        self.table_card.setVisible(bool(result.steps))
        self.result_card.show()

    @staticmethod
    def _step_text(step: NewtonStep) -> str:
        return (
            "xₙ₊₁ = xₙ − f(xₙ) / f′(xₙ)\n"
            f"xₙ₊₁ = {step.x:.12g} − ({step.fx:.12g}) / ({step.dfx:.12g}) ≈ {step.next_x:.12g}\n"
            f"Error absoluto = |{step.next_x:.12g} − ({step.x:.12g})| ≈ {step.absolute_error:.10g}"
        )
