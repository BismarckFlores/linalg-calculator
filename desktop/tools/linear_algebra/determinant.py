"""Determinante por cofactores y factorización LU."""

from core.linear_algebra.determinant import COFACTOR_LIMIT, Cofactors, by_cofactors, by_lu, costs, drawn_terms
from core.linear_algebra.handlers.matrix import Matrix

from desktop.core.forms import Result, ToolPage
from desktop.core.math_input import MathInput
from desktop.core.widgets import SegmentedControl, label

from .core.inputs import MatrixInput, read_equations
from .core.results import factorization_text, matrix_steps, matrix_text


def cofactor_steps(expansion: Cofactors, caption: str = "Matriz A") -> tuple[str, ...]:
    if expansion.rule:
        rule = expansion.rule
        return (f"{caption}\n{matrix_text(expansion.matrix)}\n"
                f"ad − bc = ({rule.a})({rule.d}) − ({rule.b})({rule.c}) = {expansion.value}",)
    if not expansion.terms:
        return (f"{caption}\n{matrix_text(expansion.matrix)}\ndet = {expansion.value}",)
    steps = (f"{caption}\n{matrix_text(expansion.matrix)}\nDesarrollo por {expansion.along} {expansion.index}.",)
    for term in expansion.terms:
        steps += cofactor_steps(
            term.minor,
            f"Menor ({term.row}, {term.col}) · Entrada {term.entry} · Signo {term.sign} · Aporte {term.amount}",
        )
    return steps


def determinant_page() -> ToolPage:
    method = SegmentedControl("Cofactores", "LU")
    method.setAccessibleName("Método")
    mode = SegmentedControl("Coeficientes", "Ecuaciones")
    mode.setAccessibleName("Forma de entrada")
    field = MatrixInput("1;-4;2\n-2;8;-9\n-1;7;0", "Matriz A")
    equations = MathInput("x - 4y + 2z = 0\n-2x + 8y - 9z = 0\n-x + 7y = 0",
                          "Una ecuación por línea", "equations")
    advice = label("", "advice")

    def read_matrix() -> Matrix:
        if mode.currentIndex() == 0:
            return field.matrix()
        augmented, names = read_equations(equations, 10)
        return augmented.take_columns(1, len(names))

    def advise() -> None:
        try:
            matrix = read_matrix()
        except ValueError:
            advice.clear()
            return
        if not matrix.is_square():
            advice.setText("El determinante requiere una matriz cuadrada.")
            return
        cost = costs(matrix.rows)
        advice.setText(
            f"Para una matriz {matrix.rows} × {matrix.cols} conviene {cost.advised}.\n"
            f"Cofactores: {cost.cofactor} multiplicaciones.   LU: {cost.lu} multiplicaciones."
        )

    def calculate() -> Result:
        matrix = read_matrix()
        matrix.require_square()
        use_lu = method.currentIndex() == 1
        parts = []
        if use_lu:
            found = by_lu(matrix)
            factors = found.factorization
            diagonal = " · ".join(f"({entry})" for entry in factors.diagonal)
            parts.extend((factorization_text(factors), f"det(A) = (−1)^{factors.swaps} · {diagonal} = {found.value}"))
            steps = matrix_steps(factors.log)
        else:
            if matrix.rows > COFACTOR_LIMIT:
                raise ValueError(f"El desarrollo por cofactores admite hasta orden {COFACTOR_LIMIT}. Usa LU.")
            found = by_cofactors(matrix)
            expansion = found
            if drawn_terms(found) > 30:
                depth = 1
                expansion = by_cofactors(matrix, depth)
                candidate = by_cofactors(matrix, depth + 1)
                while drawn_terms(candidate) <= 30:
                    expansion = candidate
                    depth += 1
                    candidate = by_cofactors(matrix, depth + 1)
                parts.append("Desarrollo parcial: los menores restantes muestran su valor.")
            steps = cofactor_steps(expansion)
        comparison = ""
        if matrix.rows <= 7:
            check = by_cofactors(matrix).value if use_lu else by_lu(matrix).value
            comparison = f"Comprobación por {'cofactores' if use_lu else 'LU'}: det(A) = {check}"
        return Result("\n".join([f"det(A) = {found.value}", *parts]), steps, sections=(comparison,))

    def show_fields() -> None:
        by_equations = mode.currentIndex() == 1
        field.setVisible(not by_equations)
        equations.setVisible(by_equations)
        advise()

    page = ToolPage("|A|", "Determinante", "det A por desarrollo de cofactores: cada entrada por su menor con signo.",
                    [mode, field, equations, advice], "Calcular", calculate, above=(method,),
                    after=("Comprobación con el otro método",))
    mode.currentIndexChanged.connect(show_fields)
    for editor in (field, equations):
        editor.changed.connect(advise)
        editor.bridge.initialized.connect(advise)
    show_fields()
    return page
