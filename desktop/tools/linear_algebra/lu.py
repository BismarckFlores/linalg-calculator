"""Factorización LU y solución por sustituciones triangulares."""

from core.linear_algebra.lu import factorize, solve_with_lu
from core.linear_algebra.handlers.verification import verify
from ui.presentation import render_despeje, render_verification, unknown_name

from desktop.core.forms import Result, ToolPage
from desktop.core.widgets import Toggle

from .core.inputs import MatrixTaskFields
from .core.results import factorization_text, matrix_steps, matrix_text


def lu_page() -> ToolPage:
    inputs = MatrixTaskFields(
        "Factorizar A", "3;-7;-2;2\n-3;5;1;0\n6;-4;0;-5\n-9;5;-5;12", "-9\n5\n7\n11",
        "3x1 - 7x2 - 2x3 + 2x4 = -9\n-3x1 + 5x2 + x3 = 5\n"
        "6x1 - 4x2 - 5x4 = 7\n-9x1 + 5x2 - 5x3 + 12x4 = 11",
    )
    partial = Toggle("Pivoteo parcial: en cada columna, el mayor valor absoluto")
    strict = Toggle("Modo estricto: rechazar una matriz singular")
    inputs.task.currentIndexChanged.connect(lambda index: strict.setEnabled(index == 0))

    def calculate() -> Result:
        a, b, names = inputs.read()
        if b is None:
            found = factorize(a, partial.isChecked(), strict.isChecked())
            return Result(factorization_text(found), matrix_steps(found.log))

        solved = solve_with_lu(a, b, partial.isChecked())
        found = solved.factorization
        parts = (factorization_text(found), "P · b", matrix_text(solved.permuted),
                 "Vector y", matrix_text(solved.intermediate), "Solución x", matrix_text(solved.solution))
        details = []
        for substitutions in (solved.forward, solved.backward):
            lines = []
            for sub in substitutions:
                variable = unknown_name(sub.unknown, names)
                known = [(k, v, unknown_name(col, names)) for k, v, col in sub.known]
                lines.extend(render_despeje("", variable, sub.divisor, known, sub.constant, sub.value))
            details.append("\n".join(lines))
        details.append("\n".join((
            "Comprobación A · x", matrix_text(solved.check),
            render_verification(verify(a, b, solved.solution.column(1))),
        )))
        return Result("\n".join(parts), matrix_steps(found.log), sections=tuple(details))

    return ToolPage("LU", "Factorización LU",
                    "A = LU · A como una triangular inferior de unos por una triangular superior, con P si hubo intercambios.",
                    [*inputs.fields, partial, strict], "Calcular", calculate, above=(inputs.task,),
                    answer_title="Factorización", after=("Sustitución hacia adelante  L y = P b",
                                                         "Sustitución hacia atrás  U x = y",
                                                         "Comprobación en el sistema original"))
