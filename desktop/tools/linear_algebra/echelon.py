"""Análisis de formas escalonadas y pivotes."""

from core.linear_algebra.echelon import analyse
from core.linear_algebra.handlers.elimination import to_rref
from core.linear_algebra.systems import solve
from ui.presentation import describe, render_system

from desktop.core.forms import Result, ToolPage
from desktop.core.math_input import MathInput
from desktop.core.widgets import SegmentedControl, Toggle

from .core.inputs import EQUATIONS, MatrixInput, read_equations
from .core.results import matrix_steps, matrix_text


def echelon_page() -> ToolPage:
    mode = SegmentedControl("Coeficientes", "Ecuaciones")
    mode.setAccessibleName("Forma de entrada")
    field = MatrixInput("1;-2;1;0\n0;2;-8;8\n-4;5;9;-9", "Matriz")
    equations = MathInput(EQUATIONS, "Ecuaciones · una por línea", "equations")
    augmented = Toggle("Es una matriz aumentada  [ A | b ]")

    def show_fields() -> None:
        by_equations = mode.currentIndex() == 1
        equations.setVisible(by_equations)
        field.setVisible(not by_equations)
        augmented.setVisible(not by_equations)

    def calculate() -> Result:
        by_equations = mode.currentIndex() == 1
        matrix, names = read_equations(equations, 10) if by_equations else (field.matrix(), [])
        form = analyse(matrix)
        reduction = to_rref(matrix)
        properties = (
            "Filas nulas al final", "Entradas principales avanzan a la derecha",
            "Ceros debajo de cada entrada principal", "Entradas principales iguales a uno",
            "Ceros en el resto de cada columna pivote",
        )
        parts = [
            f"Forma escalonada: {'sí' if form.is_echelon else 'no'}",
            f"Forma escalonada reducida: {'sí' if form.is_reduced else 'no'}",
            f"Entradas principales de la matriz original: {form.leading or 'ninguna'}",
        ]
        for condition, title in zip(form.conditions, properties):
            verdict = "cumple"
            if not condition.holds:
                verdict = f"falla en la fila {condition.row}"
                if condition.column:
                    verdict += f", columna {condition.column}"
            parts.append(f"{condition.number}. {title} · {verdict}.")
        pivots = [
            "Forma reducida", matrix_text(reduction.result),
            f"Posiciones pivote: {reduction.pivots or 'ninguna'}",
            f"Columnas libres: {reduction.free_columns() or 'ninguna'}",
        ]
        bar_after = None
        if by_equations or augmented.isChecked():
            solution = solve(matrix)
            bar_after = solution.unknowns
            pivots.extend((describe(solution), render_system(reduction.result, solution.unknowns, names)))
        return Result("\n".join(pivots), matrix_steps(reduction.log, bar_after=bar_after),
                      sections=("\n".join(parts),))

    page = ToolPage("▧", "Formas Escalonadas",
                    "Comprobar si una matriz está en forma escalonada, reducirla y localizar sus pivotes.",
                    [mode, field, equations, augmented], "Analizar", calculate,
                    before=("Forma de la matriz",), answer_title="Posiciones y columnas pivote",
                    walk_title="Reducción a la forma escalonada reducida")
    mode.currentIndexChanged.connect(show_fields)
    show_fields()
    return page
