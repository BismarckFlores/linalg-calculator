"""Inversa de una matriz y solución por inversa."""

from core.linear_algebra.inverse import invert, solve_with_inverse
from core.linear_algebra.handlers.verification import verify
from ui.presentation import render_verification

from desktop.core.forms import Result, ToolPage
from desktop.core.widgets import label

from .core.inputs import MatrixTaskFields
from .core.results import matrix_steps, matrix_text


def inverse_page() -> ToolPage:
    inputs = MatrixTaskFields("Calcular A⁻¹", "3;4\n5;6", "7\n11", "3x + 4y = 7\n5x + 6y = 11", max_size=1000)
    hint = label("En Ecuaciones se invierte A, la matriz de coeficientes del sistema.", "muted")
    inputs.task.currentIndexChanged.connect(lambda index: hint.setVisible(index == 0))

    def calculate() -> Result:
        a, b, _ = inputs.read()
        solved = solve_with_inverse(a, b) if b is not None else None
        found = solved.inverse_result if solved else invert(a)
        parts = ["A⁻¹", matrix_text(found.inverse)]
        check = "\n".join((
            "A · A⁻¹", matrix_text(found.left_check),
            "A⁻¹ · A", matrix_text(found.right_check),
            "Ambos productos dan la identidad.",
        ))
        solution = verification = ""
        if solved and b is not None:
            solution = "\n".join(("x = A⁻¹ b", matrix_text(solved.solution)))
            verification = "\n".join((
                "Comprobación A · x", matrix_text(solved.check),
                render_verification(verify(a, b, solved.solution.column(1))),
            ))
        steps = matrix_steps(found.reduction.log, "Matriz aumentada  [ A | I ]", bar_after=a.cols)
        return Result("\n".join(parts), steps, sections=(check, solution, verification))

    return ToolPage("⁻¹", "Matriz Inversa", "Calcular A⁻¹ · transformar [ A | I ] en [ I | A⁻¹ ] por Gauss–Jordan.",
                    [*inputs.fields, hint], "Calcular", calculate, above=(inputs.task,),
                    answer_title="Resultado  A⁻¹", after=("Comprobación en la matriz original",
                                                          "Solución x = A⁻¹ b",
                                                          "Comprobación en el sistema original"))
