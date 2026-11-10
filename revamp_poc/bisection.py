"""Página compartida de los métodos de búsqueda por intervalo."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QGridLayout, QHeaderView, QHBoxLayout, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.bisection import bisect
from core.real_function import RealFunction
from core.regula_falsi import regula_falsi
from core.root_bracket import RootCriterion, RootStop

from .math_input import MathInput
from .plot import FunctionPlot
from .widgets import action, card, label, link, page_header, pill_group


CRITERIA = {
    RootCriterion.WIDTH: "Ancho b − a",
    RootCriterion.RELATIVE: "Error relativo (%)",
    RootCriterion.RESIDUAL: "Residuo |f(c)|",
}


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
        result_layout.addWidget(label("Procedimiento", "heading"))
        step_controls = QHBoxLayout()
        step_label = label("Iteración", "caption")
        self.step_index = QSpinBox()
        step_label.setBuddy(self.step_index)
        self.step_index.valueChanged.connect(self._show_step)
        step_controls.addWidget(step_label)
        step_controls.addWidget(self.step_index)
        step_controls.addStretch()
        result_layout.addLayout(step_controls)
        self.step_detail = label("", "muted")
        result_layout.addWidget(self.step_detail)
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(["i", "a", "b", "c", "f(a)", "f(b)", "f(c)", "Ancho", "Error %"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
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
        self.table.setRowCount(len(result.steps))
        for row, step in enumerate(result.steps):
            values = (step.index, step.a, step.b, step.c, step.fa, step.fb, step.fc, step.width,
                      step.relative_error)
            for column, value in enumerate(values):
                item = QTableWidgetItem("—" if value is None else f"{value:.9g}")
                if value is not None:
                    item.setToolTip(str(value))
                self.table.setItem(row, column, item)
        self.plot.show_result(result)
        self.step_index.setRange(1, max(1, len(result.steps)))
        self.step_index.setValue(1)
        self.step_index.setEnabled(bool(result.steps))
        self._show_step()
        self.result_card.show()

    def _show_step(self) -> None:
        result = self.plot.result
        if result is None:
            return
        if not result.steps:
            self.step_detail.setText(f"Un extremo inicial satisface f({result.root:.9g}) = 0.")
            return
        step = result.steps[self.step_index.value() - 1]
        detail = (
            f"Con a = {step.a:.9g}, b = {step.b:.9g}, f(a) = {step.fa:.9g} y f(b) = {step.fb:.9g}:\n"
            f"c = {self.formula} ≈ {step.c:.9g}\n"
            f"Al sustituir, f({step.c:.9g}) ≈ {step.fc:.9g}."
        )
        if step.index < len(result.steps):
            a, b = (step.a, step.c) if step.keep_left else (step.c, step.b)
            detail += f" El cambio de signo se conserva en [{a:.9g}, {b:.9g}]."
        else:
            detail += " El método se detiene en esta iteración."
        self.step_detail.setText(detail)
        self.table.selectRow(step.index - 1)


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
