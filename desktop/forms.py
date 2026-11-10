"""Formularios y procedimientos compartidos por las herramientas de álgebra."""

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLineEdit, QPlainTextEdit, QSpinBox, QVBoxLayout, QWidget,
)

from core.equations import parse_equation, to_augmented, unknown_names
from core.matrix import Matrix
from core.steps import StepLog
from ui.presentation import pretty_label

from .math_input import MathInput
from .math_notation import matrix_rows
from .widgets import ResultTable, action, card, label, link, page_header


def choice(*values: str) -> QComboBox:
    widget = QComboBox()
    widget.addItems(values)
    return widget


def text_input(name: str, value: str, *, multiline: bool = False) -> QWidget:
    widget = QPlainTextEdit(value) if multiline else QLineEdit(value)
    widget.setAccessibleName(name)
    if multiline:
        widget.setFixedHeight(110)
    return widget


def integer(name: str, low: int, high: int, value: int) -> QSpinBox:
    widget = QSpinBox()
    widget.setAccessibleName(name)
    widget.setRange(low, high)
    widget.setValue(value)
    return widget


def matrix_text(matrix: Matrix) -> str:
    return "\n".join("[ " + "; ".join(map(str, row)) + " ]" for row in matrix.data)


class MatrixInput(MathInput):
    """Matriz editable, con dimensiones ajustables y pegado de filas."""

    def __init__(self, value: str, name: str, *, max_size: int = 10, column: bool = False) -> None:
        super().__init__(value, name, "matrix")
        self.max_size = max_size
        self.column = column
        layout = QHBoxLayout()
        rows = matrix_rows(value)
        self.rows = integer("Filas", 1, max_size, len(rows))
        self.cols = integer("Columnas", 1, 1 if column else max_size, len(rows[0]))
        for caption, size in (("Filas", self.rows), ("Columnas", self.cols)):
            if column and size is self.cols:
                continue
            field_label = label(caption, "caption")
            field_label.setBuddy(size)
            layout.addWidget(field_label)
            layout.addWidget(size)
            size.valueChanged.connect(self._resize)
        layout.addStretch()
        self.layout().insertLayout(1, layout)
        self.changed.connect(self._sync_size)

    def _sync_size(self) -> None:
        try:
            rows = matrix_rows(self.value())
        except ValueError:
            return
        for control, count in ((self.rows, len(rows)), (self.cols, len(rows[0]))):
            old = control.blockSignals(True)
            control.setValue(count)
            control.blockSignals(old)

    def _resize(self) -> None:
        try:
            current = matrix_rows(self.value())
        except ValueError:
            return
        rows, cols = self.rows.value(), self.cols.value()
        self.set_value("\n".join(
            ";".join(
                current[i][j] if i < len(current) and j < len(current[i]) else "0"
                for j in range(cols)
            ) for i in range(rows)
        ))

    def matrix(self) -> Matrix:
        rows = matrix_rows(self.value())
        if len(rows) > self.max_size or len(rows[0]) > self.max_size:
            raise ValueError(f"Se admiten hasta {self.max_size} filas y columnas.")
        if self.column and len(rows[0]) != 1:
            raise ValueError("Escribe el vector b en una sola columna.")
        return Matrix(rows)


def read_equations(editor: MathInput, max_size: int) -> tuple[Matrix, list[str]]:
    lines = [line.strip() for line in editor.value().splitlines() if line.strip()]
    if not 1 <= len(lines) <= max_size:
        raise ValueError(f"Escribe entre 1 y {max_size} ecuaciones, una por línea.")
    parsed = []
    for index, line in enumerate(lines, 1):
        try:
            parsed.append(parse_equation(line))
        except ValueError as problem:
            raise ValueError(f"Ecuación {index}. {problem}") from problem
    names = unknown_names(parsed)
    if not 1 <= len(names) <= max_size:
        raise ValueError(f"El sistema debe tener entre 1 y {max_size} incógnitas.")
    return to_augmented(parsed, names), names


@dataclass(frozen=True)
class Result:
    text: str
    steps: tuple[str, ...] = ()
    headers: tuple[str, ...] = ()
    rows: tuple[tuple, ...] = ()


def matrix_steps(log: StepLog) -> tuple[str, ...]:
    return (
        f"Matriz inicial\n{matrix_text(log.initial)}",
        *(f"{pretty_label(step.label)}\n{matrix_text(step.after)}" for step in log),
    )


class StepView(QWidget):
    """Navega resultados ya calculados y permite desplegar el recorrido."""

    def __init__(self, caption: str = "Paso") -> None:
        super().__init__()
        self.steps: tuple[str, ...] = ()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("Procedimiento", "heading"))
        controls = QHBoxLayout()
        previous, next_step = link("← Anterior"), link("Siguiente →")
        self.index = integer(caption, 1, 1, 1)
        self.total = label("", "caption")
        self.all_steps = QCheckBox("Ver todos los pasos")
        for widget in (previous, label(caption, "caption"), self.index, self.total, next_step, self.all_steps):
            controls.addWidget(widget)
        controls.addStretch()
        layout.addLayout(controls)
        self.output = MathInput("", "", "output")
        layout.addWidget(self.output)
        previous.clicked.connect(self.index.stepDown)
        next_step.clicked.connect(self.index.stepUp)
        self.index.valueChanged.connect(self._show)
        self.all_steps.toggled.connect(self._show)

    def set_steps(self, steps: tuple[str, ...]) -> None:
        self.steps = steps
        self.index.setRange(1, max(1, len(steps)))
        self.index.setValue(1)
        self.total.setText(f"de {len(steps)}")
        self.setVisible(bool(steps))
        self._show()

    def _show(self) -> None:
        if not self.steps:
            return
        show_all = self.all_steps.isChecked()
        self.index.setEnabled(not show_all and len(self.steps) > 1)
        if show_all:
            self.output.set_value("\n\n".join(
                f"Paso {i}\n{step}" for i, step in enumerate(self.steps, 1)
            ))
        else:
            self.output.set_value(self.steps[self.index.value() - 1])


class ToolPage(QWidget):
    """Presenta un formulario, invalida resultados y conecta su cálculo."""

    def __init__(
        self, glyph: str, title: str, subtitle: str, fields: list[QWidget],
        button: str, calculate: Callable[[], Result],
    ) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(page_header(glyph, title, subtitle))
        panel, self.form = card()
        for field in fields:
            self.form.addWidget(field)
        submit = action(button)
        submit.clicked.connect(self._calculate)
        self.form.addWidget(submit, alignment=Qt.AlignmentFlag.AlignRight)
        self.error = label("", "inputError")
        self.error.hide()
        self.form.addWidget(self.error)
        layout.addWidget(panel)
        self.result, result_layout = card()
        result_layout.addWidget(label("Resultado", "heading"))
        self.output = MathInput("", "", "output")
        result_layout.addWidget(self.output)
        self.walk = StepView()
        result_layout.addWidget(self.walk)
        self.table = ResultTable()
        result_layout.addWidget(self.table)
        layout.addWidget(self.result)
        self.result.hide()
        layout.addStretch()
        self._solve = calculate

        for field in fields:
            if isinstance(field, MathInput):
                field.changed.connect(self._clear)
            elif isinstance(field, QComboBox):
                field.currentIndexChanged.connect(self._clear)
            elif isinstance(field, (QCheckBox, QSpinBox)):
                signal = field.toggled if isinstance(field, QCheckBox) else field.valueChanged
                signal.connect(self._clear)
            elif isinstance(field, (QLineEdit, QPlainTextEdit)):
                field.textChanged.connect(self._clear)

    def _clear(self) -> None:
        self.result.hide()
        self.error.hide()

    def _calculate(self) -> None:
        self._clear()
        try:
            result = self._solve()
        except (TypeError, ValueError, ArithmeticError) as problem:
            self.error.setText(str(problem))
            self.error.show()
            return
        self.output.set_value(result.text)
        self.walk.set_steps(result.steps)
        self.table.fill(result.headers, result.rows)
        self.table.setVisible(bool(result.headers))
        self.result.show()
