"""Eliminación Gaussiana y Gauss–Jordan."""

from PySide6.QtWidgets import QLabel

from core.linear_algebra.handlers.elimination import to_rref
from core.linear_algebra.handlers.parametric import general_solution
from core.linear_algebra.systems import SystemKind, solve
from core.linear_algebra.handlers.verification import verify
from ui.presentation import (
    describe, render_general, render_substitutions, render_system, render_values,
    render_verification, unknown_name,
)

from desktop.core.forms import Result, ToolPage
from desktop.core.widgets import SegmentedControl

from .core.inputs import read_system, system_input
from .core.results import matrix_steps, matrix_text


def gauss_page() -> ToolPage:
    method = SegmentedControl("Gauss", "Gauss-Jordan")
    method.setAccessibleName("Método de eliminación")
    mode, coefficients, constants, equations = system_input()

    def show_fields() -> None:
        by_equations = mode.currentIndex() == 1
        coefficients.setVisible(not by_equations)
        constants.setVisible(not by_equations)
        equations.setVisible(by_equations)

    def calculate() -> Result:
        augmented, names = read_system(mode, coefficients, constants, equations)
        solution = solve(augmented)
        jordan = method.currentIndex() == 1
        reduction = to_rref(augmented) if jordan else solution.reduction
        parts = [
            f"rango(A) = {solution.coefficient_rank} · rango(A|b) = {solution.rank} · incógnitas = {solution.unknowns}",
            "Columnas pivote: " + (", ".join(
                str(col) for _, col in reduction.pivots if col <= solution.unknowns
            ) or "ninguna"),
            describe(solution),
            render_values(solution, names),
        ]
        if solution.free_columns:
            parts.insert(2, "Columnas libres: " + ", ".join(map(str, solution.free_columns)))
        setup = "\n".join(
            f"[ {'; '.join(map(str, row))} ] · [ {unknown_name(index, names)} ] = [ {constant} ]"
            for index, (row, (constant,)) in enumerate(zip(solution.coefficients.data, solution.constants.data), 1)
        ) if solution.coefficients.rows == solution.unknowns else "\n".join((
            "Matriz A", matrix_text(solution.coefficients), "Vector b", matrix_text(solution.constants),
        ))
        equivalent = render_system(reduction.result, solution.unknowns, names)
        steps = matrix_steps(reduction.log, "Matriz aumentada  [ A | b ]", bar_after=solution.unknowns)
        substitution = ""
        verification = ""
        if solution.kind is SystemKind.INFINITE:
            reduced = reduction if jordan else to_rref(augmented)
            parts.extend(("Solución general", render_general(general_solution(reduced, solution.unknowns), names)))
        if solution.kind is SystemKind.UNIQUE:
            if not jordan:
                substitution = render_substitutions(solution, names)
            check = verify(solution.coefficients, solution.constants, solution.values)
            verification = render_verification(check)
        return Result("\n".join(parts), steps, sections=(setup, equivalent, substitution, verification))

    subtitles = (
        "Resolver A x = b · forma escalonada por operaciones elementales de fila.",
        "Resolver A x = b · forma escalonada reducida, con cada pivote solo en su columna.",
    )
    page = ToolPage("▦", "Eliminación Gaussiana", subtitles[0],
                    [mode, (coefficients, constants), equations], "Calcular", calculate, above=(method,),
                    before=("Ecuación matricial A x = b",),
                    between=("Sistema equivalente",),
                    after=("Sustitución hacia atrás", "Comprobación en el sistema original"))
    subtitle = page.header.findChild(QLabel, "muted")
    method.currentIndexChanged.connect(lambda index: subtitle.setText(subtitles[index]))
    mode.currentIndexChanged.connect(show_fields)
    show_fields()
    return page
