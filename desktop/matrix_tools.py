"""Sistemas lineales y herramientas matriciales sobre el motor exacto."""

from PySide6.QtWidgets import QLabel

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

from .forms import MatrixInput, Result, ToolPage, matrix_steps, matrix_text, read_equations
from .math_input import MathInput
from .widgets import SegmentedControl, Toggle, label


EXAMPLE = "1;-2;1\n0;2;-8\n-4;5;9"
CONSTANTS = "0\n8\n-9"
EQUATIONS = "x - 2y + z = 0\n2y - 8z = 8\n-4x + 5y + 9z = -9"


def system_input(
    *, max_size: int = 10, matrix: str = EXAMPLE, vector: str = CONSTANTS, example: str = EQUATIONS,
) -> tuple:
    mode = SegmentedControl("Coeficientes", "Ecuaciones")
    mode.setAccessibleName("Forma de entrada")
    coefficients = MatrixInput(matrix, "Matriz A", max_size=max_size)
    constants = MatrixInput(vector, "Vector b", max_size=max_size, column=True)
    equations = MathInput(example, "Una ecuación por línea", "equations")
    coefficients.changed.connect(lambda: constants.rows.setValue(coefficients.rows.value()))
    constants.changed.connect(lambda: coefficients.rows.setValue(constants.rows.value()))
    return mode, coefficients, constants, equations


def read_system(mode, coefficients, constants, equations) -> tuple[Matrix, list[str]]:
    if mode.currentIndex() == 1:
        return read_equations(equations, coefficients.max_size)
    return coefficients.matrix().augment(constants.matrix()), []


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


def operations_page() -> ToolPage:
    operation = SegmentedControl("A + B", "A − B", "A × B", "k · A", "Aᵀ")
    operation.setAccessibleName("Operación")
    left = MatrixInput("1;2\n3;4", "Matriz A")
    right = MatrixInput("5;6\n7;8", "Matriz B")
    scalar = MathInput("1/2", "Escalar k", "number")
    descriptions = (
        "Suma de matrices, entrada por entrada.", "Resta de matrices, entrada por entrada.",
        "Producto de filas de A por columnas de B.", "Multiplica cada entrada de A por k.",
        "Intercambia las filas y columnas de A.",
    )
    description = label(descriptions[0], "muted")

    def show_fields() -> None:
        right.setVisible(operation.currentIndex() < 3)
        scalar.setVisible(operation.currentIndex() == 3)
        description.setText(descriptions[operation.currentIndex()])

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
        return Result(matrix_text(result), title=f"Resultado  C = {operation.currentText()}",
                      badge=f"Dimensión: {result.rows} × {result.cols}")

    page = ToolPage("⊞", "Operaciones Matriciales",
                    "Suma, resta, producto de matrices, producto por un escalar y transpuesta.",
                    [scalar, (left, right)], "Calcular", calculate, above=(operation, description))
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
    task = SegmentedControl("Calcular A⁻¹" if inverse else "Factorizar A", "Resolver A x = b")
    task.setAccessibleName("Tarea")
    if inverse:
        mode, coefficients, constants, equations = system_input(
            max_size=1000, matrix="3;4\n5;6", vector="7\n11", example="3x + 4y = 7\n5x + 6y = 11",
        )
    else:
        mode, coefficients, constants, equations = system_input(
            matrix="3;-7;-2;2\n-3;5;1;0\n6;-4;0;-5\n-9;5;-5;12",
            vector="-9\n5\n7\n11",
            example="3x1 - 7x2 - 2x3 + 2x4 = -9\n-3x1 + 5x2 + x3 = 5\n"
                    "6x1 - 4x2 - 5x4 = 7\n-9x1 + 5x2 - 5x3 + 12x4 = 11",
        )
    partial = Toggle("Pivoteo parcial: en cada columna, el mayor valor absoluto")
    strict = Toggle("Modo estricto: rechazar una matriz singular")
    hint = label("En Ecuaciones se invierte A, la matriz de coeficientes del sistema.", "muted")
    fields = [mode, (coefficients, constants), equations]
    if inverse:
        fields.append(hint)
    if not inverse:
        fields.extend((partial, strict))

    def show_fields() -> None:
        by_equations = mode.currentIndex() == 1
        solve_system = task.currentIndex() == 1
        coefficients.setVisible(not by_equations)
        constants.setVisible(solve_system and not by_equations)
        equations.setVisible(by_equations)
        strict.setEnabled(not solve_system)
        hint.setVisible(inverse and not solve_system)

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
            parts = ["A⁻¹", matrix_text(found.inverse)]
            check = "\n".join((
                "A · A⁻¹", matrix_text(found.left_check),
                "A⁻¹ · A", matrix_text(found.right_check),
                "Ambos productos dan la identidad.",
            ))
            steps = matrix_steps(found.reduction.log, "Matriz aumentada  [ A | I ]", bar_after=a.cols)
            details = [check, "", ""]
        else:
            solved = solve_with_lu(a, b, partial.isChecked()) if solve_system else None
            found = solved.factorization if solved else factorize(a, partial.isChecked(), strict.isChecked())
            parts = [factorization_text(found)]
            steps = matrix_steps(found.log)
            details = ["", "", ""]
            if solved:
                for index, substitutions in enumerate((solved.forward, solved.backward)):
                    lines = []
                    for sub in substitutions:
                        variable = unknown_name(sub.unknown, names)
                        known = [(k, v, unknown_name(col, names)) for k, v, col in sub.known]
                        lines.extend(render_despeje("", variable, sub.divisor, known, sub.constant, sub.value))
                    details[index] = "\n".join(lines)

        if solved:
            solution_text = "\n".join(("x = A⁻¹ b" if inverse else "Solución x", matrix_text(solved.solution)))
            if inverse:
                details[1] = solution_text
            else:
                parts.extend(("P · b", matrix_text(solved.permuted), "Vector y", matrix_text(solved.intermediate),
                              solution_text))
            details[2] = "\n".join((
                "Comprobación A · x", matrix_text(solved.check),
                render_verification(verify(a, b, solved.solution.column(1))),
            ))
        return Result("\n".join(parts), steps, sections=tuple(details))

    glyph, title, subtitle = (
        ("⁻¹", "Matriz Inversa", "Calcular A⁻¹ · transformar [ A | I ] en [ I | A⁻¹ ] por Gauss–Jordan.")
        if inverse else ("LU", "Factorización LU",
                         "A = LU · A como una triangular inferior de unos por una triangular superior, con P si hubo intercambios.")
    )
    headings = (
        ("Comprobación en la matriz original", "Solución x = A⁻¹ b")
        if inverse else ("Sustitución hacia adelante  L y = P b", "Sustitución hacia atrás  U x = y")
    )
    page = ToolPage(glyph, title, subtitle, fields, "Calcular", calculate, above=(task,),
                    answer_title="Resultado  A⁻¹" if inverse else "Factorización",
                    after=(*headings, "Comprobación en el sistema original"))
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
