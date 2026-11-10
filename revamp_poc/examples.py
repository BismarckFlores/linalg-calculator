"""Una operación real de muestra por cada grupo no numérico."""

from collections.abc import Callable

from PySide6.QtWidgets import (
    QFormLayout, QHeaderView, QLineEdit, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.bases import to_base
from core.determinant import by_cofactors
from core.equations import parse_equation, to_augmented, unknown_names
from core.matrix import Matrix
from core.scalar import format_scalar
from core.systems import SystemKind, solve
from core.vectors import add, parse_vector
from core.verification import verify
from ui.presentation import describe, render_equations, render_values, render_verification

from .widgets import action, card, label


class SamplePage(QWidget):
    def __init__(
        self, title: str, subtitle: str, fields: list[tuple[str, QWidget]],
        button: str, calculate: Callable[[], str],
    ) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(label(title, "title"))
        layout.addWidget(label(subtitle, "muted"))
        panel, panel_layout = card()
        form = QFormLayout()
        for name, field in fields:
            field.setAccessibleName(name)
            form.addRow(name, field)
        panel_layout.addLayout(form)
        submit = action(button)
        submit.clicked.connect(self._calculate)
        panel_layout.addWidget(submit)
        self.error = label("", "inputError")
        self.error.hide()
        panel_layout.addWidget(self.error)
        layout.addWidget(panel)
        self.result, result_layout = card()
        result_layout.addWidget(label("Resultado", "heading"))
        self.output = QPlainTextEdit(readOnly=True)
        self.output.setAccessibleName("Resultado")
        self.output.setMinimumHeight(190)
        result_layout.addWidget(self.output)
        layout.addWidget(self.result)
        self.result.hide()
        layout.addStretch()
        self._solve = calculate

        for _name, field in fields:
            if isinstance(field, (QLineEdit, QPlainTextEdit)):
                field.textChanged.connect(self._clear)
            elif isinstance(field, QTableWidget):
                field.itemChanged.connect(self._clear)

    def _clear(self) -> None:
        self.result.hide()
        self.error.hide()

    def _calculate(self) -> None:
        self._clear()
        try:
            self.output.setPlainText(self._solve())
        except (TypeError, ValueError, ArithmeticError) as problem:
            self.error.setText(str(problem))
            self.error.show()
            return
        self.result.show()


def gauss_page() -> SamplePage:
    equations = QPlainTextEdit("2x + y = 5\nx - y = 1")
    equations.setFixedHeight(112)

    def calculate() -> str:
        lines = [line.strip() for line in equations.toPlainText().splitlines() if line.strip()]
        if not 1 <= len(lines) <= 10:
            raise ValueError("Escribe entre 1 y 10 ecuaciones, una por línea.")
        parsed = [parse_equation(line) for line in lines]
        names = unknown_names(parsed)
        if not 1 <= len(names) <= 10:
            raise ValueError("El sistema debe tener entre 1 y 10 incógnitas.")
        result = solve(to_augmented(parsed, names))
        parts = [describe(result), render_values(result, names), "Sistema equivalente", render_equations(result, names)]
        if result.kind is SystemKind.UNIQUE:
            parts.extend(("Comprobación", render_verification(verify(result.coefficients, result.constants, result.values))))
        return "\n\n".join(parts)

    return SamplePage(
        "Eliminación Gaussiana", "Escribe el sistema con una ecuación por línea.",
        [("Ecuaciones", equations)], "Resolver sistema", calculate,
    )


def determinant_page() -> SamplePage:
    grid = QTableWidget(2, 2)
    grid.setFixedHeight(106)
    grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    grid.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    for row, values in enumerate((("3", "4"), ("5", "6"))):
        for column, value in enumerate(values):
            grid.setItem(row, column, QTableWidgetItem(value))

    def calculate() -> str:
        matrix = Matrix([[grid.item(row, column).text() for column in range(2)] for row in range(2)])
        a, b = matrix.row(1)
        c, d = matrix.row(2)
        return f"det(A) = ad − bc\n       = ({a})({d}) − ({b})({c})\n       = {by_cofactors(matrix).value}"

    return SamplePage(
        "Determinante 2 × 2", "Edita los coeficientes de la matriz. Se admiten fracciones.",
        [("Matriz A", grid)], "Calcular determinante", calculate,
    )


def vectors_page() -> SamplePage:
    first = QLineEdit("1, -2, 3")
    second = QLineEdit("4, 0, -1/2")

    def calculate() -> str:
        u, v = parse_vector(first.text()), parse_vector(second.text())
        result = add(u, v)
        entries = ", ".join(format_scalar(value) for value in result)
        lines = [f"Componente {index}: ({x}) + ({y}) = {total}"
                 for index, (x, y, total) in enumerate(zip(u, v, result), 1)]
        return f"u + v = ({entries})\n\n" + "\n".join(lines)

    return SamplePage(
        "Suma de vectores", "Escribe las componentes separadas por comas.",
        [("Vector u", first), ("Vector v", second)], "Sumar vectores", calculate,
    )


def bases_page() -> SamplePage:
    decimal = QLineEdit("43")
    decimal.setMaxLength(33)

    def calculate() -> str:
        result = to_base(int(decimal.text()), 2)
        divisions = [
            f"{division.dividend} = 2 · {division.quotient} + {division.remainder}"
            for division in result.divisions
        ]
        return f"{result.value}₁₀ = {result.numeral}₂\n\n" + "\n".join(divisions)

    return SamplePage(
        "Decimal a binario", "Convierte un entero con divisiones sucesivas entre 2.",
        [("Número decimal", decimal)], "Convertir a binario", calculate,
    )
