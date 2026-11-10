"""Una operación real de muestra por cada grupo no numérico."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from core.bases import to_base
from core.determinant import by_cofactors
from core.equations import parse_equation, to_augmented, unknown_names
from core.matrix import Matrix
from core.scalar import format_scalar
from core.systems import SystemKind, solve
from core.vectors import add, parse_vector
from core.verification import verify
from ui.presentation import describe, render_equations, render_values, render_verification

from .math_input import MathInput
from .math_notation import matrix_rows
from .widgets import action, card, label, page_header


class SamplePage(QWidget):
    def __init__(
        self, glyph: str, title: str, subtitle: str, fields: list[MathInput],
        button: str, calculate: Callable[[], str],
    ) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(page_header(glyph, title, subtitle))
        panel, panel_layout = card()
        for field in fields:
            panel_layout.addWidget(field)
        submit = action(button)
        submit.clicked.connect(self._calculate)
        panel_layout.addWidget(submit, alignment=Qt.AlignmentFlag.AlignRight)
        self.error = label("", "inputError")
        self.error.hide()
        panel_layout.addWidget(self.error)
        layout.addWidget(panel)
        self.result, result_layout = card()
        result_layout.addWidget(label("Resultado", "heading"))
        self.output = MathInput("", "", "output")
        result_layout.addWidget(self.output)
        layout.addWidget(self.result)
        self.result.hide()
        layout.addStretch()
        self._solve = calculate

        for field in fields:
            field.changed.connect(self._clear)

    def _clear(self) -> None:
        self.result.hide()
        self.error.hide()

    def _calculate(self) -> None:
        self._clear()
        try:
            self.output.set_value(self._solve())
        except (TypeError, ValueError, ArithmeticError) as problem:
            self.error.setText(str(problem))
            self.error.show()
            return
        self.result.show()


def gauss_page() -> SamplePage:
    equations = MathInput("2x + y = 5\nx - y = 1", "Ecuaciones", "equations")

    def calculate() -> str:
        lines = [line.strip() for line in equations.value().splitlines() if line.strip()]
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
        "▦", "Eliminación Gaussiana", "Escribe una ecuación por línea. Usa Enter para agregar otra.",
        [equations], "Resolver sistema", calculate,
    )


def determinant_page() -> SamplePage:
    grid = MathInput("3;4\n5;6", "Matriz A", "matrix")

    def calculate() -> str:
        matrix = Matrix(matrix_rows(grid.value()))
        a, b = matrix.row(1)
        c, d = matrix.row(2)
        return f"det(A) = ad − bc\n       = ({a})({d}) − ({b})({c})\n       = {by_cofactors(matrix).value}"

    return SamplePage(
        "|A|", "Determinante", "Edita los coeficientes de la matriz 2 × 2. Se admiten fracciones.",
        [grid], "Calcular determinante", calculate,
    )


def vectors_page() -> SamplePage:
    first = MathInput("1, -2, 3", "Vector u", "vector")
    second = MathInput("4, 0, -1/2", "Vector v", "vector")

    def calculate() -> str:
        u, v = parse_vector(first.value()), parse_vector(second.value())
        result = add(u, v)
        entries = ", ".join(format_scalar(value) for value in result)
        lines = [f"Componente {index}: ({x}) + ({y}) = {total}"
                 for index, (x, y, total) in enumerate(zip(u, v, result), 1)]
        return f"u + v = ({entries})\n\n" + "\n".join(lines)

    return SamplePage(
        "↗", "Operaciones Vectoriales", "Suma dos vectores. Escribe las componentes separadas por comas.",
        [first, second], "Sumar vectores", calculate,
    )


def bases_page() -> SamplePage:
    decimal = MathInput("43", "Número decimal", "integer")

    def calculate() -> str:
        value = decimal.value()
        if len(value) > 33:
            raise ValueError("Escribe un entero de hasta 33 caracteres.")
        result = to_base(int(value), 2)
        divisions = [
            f"{division.dividend} = 2 · {division.quotient} + {division.remainder}"
            for division in result.divisions
        ]
        return f"{result.value}₁₀ = {result.numeral}₂\n\n" + "\n".join(divisions)

    return SamplePage(
        "⇄", "Conversiones", "Convierte un entero a binario con divisiones sucesivas entre 2.",
        [decimal], "Convertir a binario", calculate,
    )
