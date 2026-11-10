"""Página compartida de los métodos de búsqueda por intervalo."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QHBoxLayout, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from core.bisection import bisect
from core.real_function import RealFunction
from core.regula_falsi import regula_falsi
from core.root_bracket import BracketStep, RootCriterion, RootStop

from .forms import StepView
from .math_input import MathInput
from .plot import FunctionPlot
from .widgets import ResultTable, action, card, label, page_header, pill_group


CRITERIA = {
    RootCriterion.WIDTH: "Ancho b − a",
    RootCriterion.RELATIVE: "Error relativo (%)",
    RootCriterion.RESIDUAL: "Residuo |f(c)|",
}
TABLE_HEADERS = ("i", "a", "b", "c", "f(a)", "f(b)", "f(c)", "Ancho", "Error %")
TABLE_PAGE_SIZE = 15


class RootBracketPage(QWidget):
    title = "Método de Bisección"
    glyph = "½"
    subtitle = "Encuentra una raíz de f(x) = 0 reduciendo un intervalo a la mitad."
    formula = "a + (b − a) / 2"
    criteria = (RootCriterion.WIDTH, RootCriterion.RESIDUAL, RootCriterion.RELATIVE)
    solve = staticmethod(bisect)
    presets = (
        ("Raíz de 2", "x^2 - 2", "1", "2", "0.0001", RootCriterion.WIDTH),
        ("Fracción con raíz", "sqrt(x+1)/2 - 1", "2", "4", "0.0001", RootCriterion.WIDTH),
        ("Polinomio del Excel", "x^4 - 5x^3 + 0.5x^2 - 11x + 10", "0.6", "1", "0.0001", RootCriterion.RESIDUAL),
        ("Potencia décima", "x^10 - 1", "0", "1.3", "0.0001", RootCriterion.WIDTH),
    )

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
        presets, examples = pill_group()
        for name, *values in self.presets:
            button = QPushButton(name)
            button.clicked.connect(lambda checked=False, inputs=values: self._example(*inputs))
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
        form = QGridLayout()
        form.setHorizontalSpacing(16)
        for index, field in enumerate((self.a, self.b, self.tolerance)):
            row, column = divmod(index, 2)
            form.addWidget(field, row, column)
            field.changed.connect(self._clear_result)
        control_layout.addLayout(form)
        self.criterion = QComboBox()
        self.criterion.addItems([CRITERIA[value] for value in self.criteria])
        self.criterion.currentIndexChanged.connect(self._clear_result)
        self.limit = QSpinBox()
        self.limit.setRange(1, 1000)
        self.limit.setValue(100)
        self.limit.valueChanged.connect(self._clear_result)
        for caption, widget in (("Criterio de parada", self.criterion), ("Máximo de iteraciones", self.limit)):
            field_label = label(caption, "caption")
            field_label.setBuddy(widget)
            control_layout.addWidget(field_label)
            control_layout.addWidget(widget)
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

        self.result_card, result_layout = card()
        result_layout.addWidget(label("Resultado", "heading"))
        self.answer = MathInput("", "", "output")
        result_layout.addWidget(self.answer)
        self.summary = label("", "muted")
        result_layout.addWidget(self.summary)
        self.bounds = label("", "muted")
        result_layout.addWidget(self.bounds)
        self.walk = StepView("Iteración")
        self.walk.index.valueChanged.connect(self._select_iteration)
        result_layout.addWidget(self.walk)
        result_layout.addWidget(label("Tabla de iteraciones", "heading"))
        table_controls = QHBoxLayout()
        self.format = QComboBox()
        self.format.setAccessibleName("Formato numérico")
        self.format.addItems(("Automático", "Decimal"))
        self.decimals = QSpinBox()
        self.decimals.setAccessibleName("Decimales")
        self.decimals.setRange(0, 17)
        self.decimals.setValue(5)
        self.table_page = QSpinBox()
        self.table_page.setAccessibleName("Página de la tabla")
        self.table_page.setMinimum(1)
        for widget in (self.format, self.decimals, label("Página", "caption"), self.table_page):
            table_controls.addWidget(widget)
        table_controls.addStretch()
        self.decimals.hide()
        self.format.currentIndexChanged.connect(self._fill_table)
        self.decimals.valueChanged.connect(self._fill_table)
        self.table_page.valueChanged.connect(self._fill_table)
        result_layout.addLayout(table_controls)
        self.table = ResultTable()
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
            result = self.solve(
                self._function, self.a.value(), self.b.value(), self.tolerance.value(),
                criterion=self.criteria[self.criterion.currentIndex()],
                max_iterations=self.limit.value(),
            )
        except ValueError as problem:
            self.solve_error.setText(str(problem))
            self.solve_error.show()
            return
        reason = {
            RootStop.ZERO: "La evaluación dio cero.",
            RootStop.TOLERANCE: "Se alcanzó la tolerancia seleccionada.",
            RootStop.LIMIT: "Sin convergencia: se alcanzó el máximo de iteraciones.",
            RootStop.STAGNATION: "Sin convergencia: la aproximación coincide con un extremo por redondeo.",
        }[result.stop]
        self.answer.set_value(f"x ≈ {result.root:.12g}\nf({result.root:.12g}) ≈ {result.value:.8g}")
        self.summary.setText(
            f"Iteraciones: {len(result.steps)} · {CRITERIA[result.criterion]} < {result.tolerance:g}\n"
            f"|f(c)| = {abs(result.value):.8g}\n{reason}"
        )
        relative = result.steps[-1].relative_error if result.steps else None
        relative_text = "—" if relative is None else f"{relative:.10g} %"
        self.bounds.setText(
            f"Intervalo final: [{result.a:.12g}, {result.b:.12g}] · "
            f"Cota en x si hay continuidad: {result.bound:.10g}\n"
            f"Cambio relativo: {relative_text}"
        )
        self.plot.show_result(result)
        self.table_page.setMaximum(max(1, (len(result.steps) + TABLE_PAGE_SIZE - 1) // TABLE_PAGE_SIZE))
        self.table_page.setValue(1)
        self._fill_table()
        steps = tuple(self._step_text(step, len(result.steps)) for step in result.steps)
        if not steps:
            steps = (f"Un extremo inicial satisface f({result.root:.9g}) = 0.",)
        self.walk.set_steps(steps)
        self._select_iteration(1)
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

    def _select_iteration(self, index: int) -> None:
        result = self.plot.result
        if result is not None and result.steps:
            self.table_page.setValue((index - 1) // TABLE_PAGE_SIZE + 1)
            self.table.selectRow((index - 1) % TABLE_PAGE_SIZE)

    def _fill_table(self) -> None:
        decimal = self.format.currentIndex() == 1
        self.decimals.setVisible(decimal)
        result = self.plot.result
        if result is None:
            return
        offset = (self.table_page.value() - 1) * TABLE_PAGE_SIZE
        rows = [
            (step.index, step.a, step.b, step.c, step.fa, step.fb, step.fc, step.width, step.relative_error)
            for step in result.steps[offset:offset + TABLE_PAGE_SIZE]
        ]
        self.table.fill(TABLE_HEADERS, rows, decimals=self.decimals.value() if decimal else None)


class RegulaFalsiPage(RootBracketPage):
    title = "Regula Falsi"
    glyph = "RF"
    subtitle = "Aproxima una raíz por el cruce de la secante con el eje x."
    formula = "b − f(b)(a − b) / (f(a) − f(b))"
    criteria = (RootCriterion.RELATIVE, RootCriterion.RESIDUAL)
    solve = staticmethod(regula_falsi)
    presets = (
        ("Ejercicio de la guía", "x^3 - 4.23603x^2 - 2.73620x - 13.09037",
         "4.95", "5.5", "0.01", RootCriterion.RELATIVE),
        ("Raíz de 2", "x^2 - 2", "1", "2", "0.0001", RootCriterion.RESIDUAL),
        ("Potencia décima", "x^10 - 1", "0", "1.3", "0.0001", RootCriterion.RESIDUAL),
    )
