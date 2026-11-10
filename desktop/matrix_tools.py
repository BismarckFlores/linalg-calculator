"""Sistemas lineales y herramientas matriciales sobre el motor exacto."""

from PySide6.QtWidgets import QCheckBox

from core.determinant import COFACTOR_LIMIT, Cofactors, by_cofactors, by_lu, costs, drawn_terms
from core.echelon import analyse
from core.elimination import to_rref
from core.inverse import invert, solve_with_inverse
from core.lu import Factorization, factorize, solve_with_lu
from core.matrix import Matrix
from core.parametric import general_solution
from core.scalar import to_scalar
from core.systems import SystemKind, solve
from core.verification import verify
from ui.presentation import (
    describe, render_despeje, render_general, render_substitutions, render_system,
    render_values, render_verification, unknown_name,
)

from .forms import MatrixInput, Result, ToolPage, choice, matrix_steps, matrix_text, read_equations
from .math_input import MathInput
from .widgets import label


EXAMPLE = "1;-2;1\n2;1;-1\n-4;5;-9"
CONSTANTS = "0\n8\n-9"
EQUATIONS = "x - 2y + z = 0\n2x + y - z = 8\n-4x + 5y - 9z = -9"


def system_input(*, max_size: int = 10) -> tuple:
    mode = choice("Coeficientes", "Ecuaciones")
    mode.setAccessibleName("Forma de entrada")
    coefficients = MatrixInput(EXAMPLE, "Matriz A", max_size=max_size)
    constants = MatrixInput(CONSTANTS, "Vector b", max_size=max_size, column=True)
    equations = MathInput(EQUATIONS, "Ecuaciones · una por línea", "equations")
    coefficients.changed.connect(lambda: constants.rows.setValue(coefficients.rows.value()))
    return mode, coefficients, constants, equations


def read_system(mode, coefficients, constants, equations) -> tuple[Matrix, list[str]]:
    if mode.currentIndex() == 1:
        return read_equations(equations, coefficients.max_size)
    return coefficients.matrix().augment(constants.matrix()), []


def gauss_page() -> ToolPage:
    method = choice("Gauss", "Gauss–Jordan")
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
            "Matriz A", matrix_text(solution.coefficients), "Vector b", matrix_text(solution.constants),
            describe(solution),
            f"Rango de A: {solution.coefficient_rank} · Rango de [A | b]: {solution.rank}",
            render_values(solution, names),
            "Columnas pivote en A: " + (", ".join(
                str(col) for _, col in reduction.pivots if col <= solution.unknowns
            ) or "ninguna"),
            "Sistema equivalente", render_system(reduction.result, solution.unknowns, names),
        ]
        steps = matrix_steps(reduction.log)
        if solution.kind is SystemKind.INFINITE:
            reduced = reduction if jordan else to_rref(augmented)
            parts.extend(("Solución general", render_general(general_solution(reduced, solution.unknowns), names)))
        if solution.kind is SystemKind.UNIQUE:
            if not jordan:
                steps += ("Sustitución hacia atrás\n" + render_substitutions(solution, names),)
            check = verify(solution.coefficients, solution.constants, solution.values)
            parts.extend(("Comprobación en el sistema original", render_verification(check)))
        return Result("\n".join(parts), steps)

    page = ToolPage("▦", "Eliminación Gaussiana", "Resuelve un sistema con Gauss o Gauss–Jordan.",
                    [method, mode, coefficients, constants, equations], "Resolver sistema", calculate)
    mode.currentIndexChanged.connect(show_fields)
    show_fields()
    return page


def echelon_page() -> ToolPage:
    mode = choice("Coeficientes", "Ecuaciones")
    mode.setAccessibleName("Forma de entrada")
    field = MatrixInput("1;2;0\n0;0;1\n0;0;0", "Matriz")
    equations = MathInput(EQUATIONS, "Ecuaciones · una por línea", "equations")
    augmented = QCheckBox("La última columna contiene los términos independientes")

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
        parts.extend((
            "Forma reducida", matrix_text(reduction.result),
            f"Posiciones pivote: {reduction.pivots or 'ninguna'}",
            f"Columnas libres: {reduction.free_columns() or 'ninguna'}",
        ))
        if by_equations or augmented.isChecked():
            solution = solve(matrix)
            parts.extend((describe(solution), render_system(reduction.result, solution.unknowns, names)))
        return Result("\n".join(parts), matrix_steps(reduction.log))

    page = ToolPage("▧", "Formas Escalonadas", "Comprueba las cinco propiedades y localiza pivotes.",
                    [mode, field, equations, augmented], "Analizar matriz", calculate)
    mode.currentIndexChanged.connect(show_fields)
    show_fields()
    return page


def operations_page() -> ToolPage:
    operation = choice("A + B", "A − B", "A × B", "k · A", "Aᵀ")
    operation.setAccessibleName("Operación")
    left = MatrixInput("1;2\n3;4", "Matriz A")
    right = MatrixInput("5;6\n7;8", "Matriz B")
    scalar = MathInput("1/2", "Escalar k", "number")

    def show_fields() -> None:
        right.setVisible(operation.currentIndex() < 3)
        scalar.setVisible(operation.currentIndex() == 3)

    def calculate() -> Result:
        a = left.matrix()
        index = operation.currentIndex()
        if index == 4:
            result = a.transpose()
        elif index == 3:
            result = a * to_scalar(scalar.value())
        else:
            b = right.matrix()
            if index == 0:
                result = a + b
            elif index == 1:
                result = a - b
            else:
                result = a * b
        return Result(f"C = {operation.currentText()}\n{matrix_text(result)}\nDimensión: {result.rows} × {result.cols}")

    page = ToolPage("⊞", "Operaciones Matriciales", "Opera con matrices y fracciones exactas.",
                    [operation, left, right, scalar], "Calcular", calculate)
    operation.currentIndexChanged.connect(show_fields)
    show_fields()
    return page


def factorization_text(found: Factorization) -> str:
    parts = [
        "L", matrix_text(found.lower), "U", matrix_text(found.upper),
        f"Rango: {found.rank} · Intercambios: {found.swaps}",
        "La matriz es singular." if found.singular else "La matriz es invertible.",
    ]
    if found.permuted:
        parts.extend(("P", matrix_text(found.permutation), f"Orden de las filas: {found.row_order}"))
    parts.extend((
        "PA = LU" if found.permuted else "A = LU",
        matrix_text(found.product),
        "La comprobación exacta se cumple." if found.holds else "La comprobación exacta falló.",
    ))
    return "\n".join(parts)


def factor_page(*, inverse: bool) -> ToolPage:
    task = choice("Calcular inversa" if inverse else "Factorizar A", "Resolver A x = b")
    task.setAccessibleName("Tarea")
    mode, coefficients, constants, equations = system_input(max_size=1000 if inverse else 10)
    partial = QCheckBox("Pivoteo parcial")
    strict = QCheckBox("Modo estricto")
    fields = [task, mode, coefficients, constants, equations]
    if not inverse:
        fields.extend((partial, strict))

    def show_fields() -> None:
        by_equations = mode.currentIndex() == 1
        solve_system = task.currentIndex() == 1
        coefficients.setVisible(not by_equations)
        constants.setVisible(solve_system and not by_equations)
        equations.setVisible(by_equations)
        strict.setEnabled(not solve_system)

    def calculate() -> Result:
        solve_system = task.currentIndex() == 1
        names: list[str] = []
        b = None
        if mode.currentIndex() == 1:
            augmented, names = read_equations(equations, coefficients.max_size)
            a = augmented.take_columns(1, len(names))
            b = augmented.take_columns(len(names) + 1, augmented.cols)
        else:
            a = coefficients.matrix()
            if solve_system:
                b = constants.matrix()

        if inverse:
            solved = solve_with_inverse(a, b) if solve_system else None
            found = solved.inverse_result if solved else invert(a)
            parts = [
                "Inversa", matrix_text(found.inverse),
                "A · A⁻¹", matrix_text(found.left_check),
                "A⁻¹ · A", matrix_text(found.right_check),
                "Ambos productos dan la identidad.",
            ]
            steps = matrix_steps(found.reduction.log)
        else:
            solved = solve_with_lu(a, b, partial.isChecked()) if solve_system else None
            found = solved.factorization if solved else factorize(a, partial.isChecked(), strict.isChecked())
            parts = [factorization_text(found)]
            steps = matrix_steps(found.log)
            if solved:
                parts.extend(("P · b", matrix_text(solved.permuted), "Vector y", matrix_text(solved.intermediate)))
                for title, substitutions in (("L y = P b", solved.forward), ("U x = y", solved.backward)):
                    steps += (title,)
                    for sub in substitutions:
                        variable = unknown_name(sub.unknown, names)
                        known = [(k, v, unknown_name(col, names)) for k, v, col in sub.known]
                        steps += ("\n".join(render_despeje("", variable, sub.divisor, known, sub.constant, sub.value)),)

        if solved:
            parts.extend((
                "x = A⁻¹ b" if inverse else "Solución x", matrix_text(solved.solution),
                "Comprobación A · x", matrix_text(solved.check),
                render_verification(verify(a, b, solved.solution.column(1))),
            ))
        return Result("\n".join(parts), steps)

    glyph, title, subtitle = (
        ("⁻¹", "Matriz Inversa", "Reduce [A | I] y comprueba la inversa.")
        if inverse else ("LU", "Factorización LU", "Descompone PA = LU y resuelve por sustitución.")
    )
    page = ToolPage(glyph, title, subtitle, fields, "Calcular", calculate)
    for field in (mode, task):
        field.currentIndexChanged.connect(show_fields)
    show_fields()
    return page


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
    method = choice("Cofactores", "Factorización LU")
    method.setAccessibleName("Método")
    field = MatrixInput("3;4\n5;6", "Matriz A")
    advice = label("", "muted")

    def advise() -> None:
        try:
            matrix = field.matrix()
        except ValueError:
            advice.clear()
            return
        if not matrix.is_square():
            advice.setText("El determinante requiere una matriz cuadrada.")
            return
        cost = costs(matrix.rows)
        advice.setText(
            f"Multiplicaciones estimadas · Cofactores: {cost.cofactor} · LU: {cost.lu}. "
            f"Método recomendado: {cost.advised}."
        )

    def calculate() -> Result:
        matrix = field.matrix()
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
        if matrix.rows <= 7:
            check = by_cofactors(matrix).value if use_lu else by_lu(matrix).value
            parts.append(f"Comprobación por {'cofactores' if use_lu else 'LU'}: det(A) = {check}")
        return Result("\n".join([f"det(A) = {found.value}", *parts]), steps)

    page = ToolPage("|A|", "Determinante", "Calcula por cofactores o por factorización LU.",
                    [field, advice, method], "Calcular determinante", calculate)
    field.changed.connect(advise)
    field.bridge.initialized.connect(advise)
    advise()
    return page
