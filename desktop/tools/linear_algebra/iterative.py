"""Sistemas lineales por Jacobi y Gauss–Seidel."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from core.linear_algebra.iterative import IterativeCriterion, IterativeMethod, IterativeStop, solve_iterative
from core.linear_algebra.vectors import parse_vector
from core.scalar import format_scalar
from desktop.core.forms import Result, ToolPage
from desktop.core.math_input import MathInput
from desktop.core.widgets import SegmentedControl, Stepper, label

from .core.inputs import read_system, system_input


EXAMPLES = (
    ("Sistema 3 × 3", "10;2;1\n1;5;1\n2;3;10", "7\n-8\n6",
     "10x_1 + 2x_2 + x_3 = 7\nx_1 + 5x_2 + x_3 = -8\n2x_1 + 3x_2 + 10x_3 = 6"),
    ("Sistema 4 × 4", "10;-1;2;0\n-1;11;-1;3\n2;-1;10;-1\n0;3;-1;8", "6\n25\n-11\n15",
     "10x_1 - x_2 + 2x_3 = 6\n-x_1 + 11x_2 - x_3 + 3x_4 = 25\n2x_1 - x_2 + 10x_3 - x_4 = -11\n3x_2 - x_3 + 8x_4 = 15"),
)


def iterative_page() -> ToolPage:
    method = SegmentedControl("Jacobi", "Gauss–Seidel")
    method.setAccessibleName("Método iterativo")
    mode, coefficients, constants, equations = system_input(
        matrix=EXAMPLES[0][1], vector=EXAMPLES[0][2], example=EXAMPLES[0][3],
    )
    examples = SegmentedControl(*(item[0] for item in EXAMPLES), selected=-1)
    examples.setAccessibleName("Cargar ejemplo iterativo")
    initial = MathInput("", "Vector inicial (vacío para ceros)", "vector")
    tolerance = MathInput("0.0001", "Tolerancia E", "number")
    limit = Stepper("Máximo de iteraciones", 1, 1000, 50, editable=True)
    criterion = SegmentedControl("Error absoluto", "Residuo")
    criterion.setAccessibleName("Criterio de parada")
    criterion_field = QWidget()
    criterion_layout = QVBoxLayout(criterion_field)
    criterion_layout.setContentsMargins(0, 0, 0, 0)
    criterion_layout.setSpacing(6)
    criterion_layout.addWidget(label("Criterio de parada", "caption"))
    criterion_layout.addWidget(criterion, alignment=Qt.AlignmentFlag.AlignLeft)
    limit_field = QWidget()
    limit_layout = QVBoxLayout(limit_field)
    limit_layout.setContentsMargins(0, 0, 0, 0)
    limit_layout.setSpacing(6)
    limit_layout.addWidget(label("Máximo de iteraciones", "caption"))
    limit_layout.addWidget(limit, alignment=Qt.AlignmentFlag.AlignLeft)
    description = label("", "muted")

    def show_fields() -> None:
        by_equations = mode.currentIndex() == 1
        coefficients.setVisible(not by_equations)
        constants.setVisible(not by_equations)
        equations.setVisible(by_equations)
        description.setText(
            "Jacobi usa el vector anterior completo en cada iteración."
            if method.currentIndex() == 0 else
            "Gauss–Seidel usa cada valor nuevo en los cálculos siguientes de la misma iteración."
        )

    def load_example(index: int) -> None:
        _, matrix, vector, system = EXAMPLES[index]
        coefficients.set_value(matrix)
        constants.set_value(vector)
        equations.set_value(system)
        initial.clear()
        tolerance.set_value("0.0001")
        limit.setValue(50)

    def calculate() -> Result:
        augmented, names = read_system(mode, coefficients, constants, equations)
        size = augmented.cols - 1
        a = augmented.take_columns(1, size)
        b = tuple(row[-1] for row in augmented.data)
        selected = tuple(IterativeMethod)[method.currentIndex()]
        result = solve_iterative(
            a, b, method=selected,
            initial=parse_vector(initial.value()) if initial.value().strip() else None,
            tolerance=tolerance.value(), max_iterations=limit.value(),
            criterion=tuple(IterativeCriterion)[criterion.currentIndex()],
        )
        variables = names or [f"x_{i + 1}" for i in range(size)]
        def number(value) -> str:
            return f"{float(value):.10g}"
        dominance = [
            f"Fila {i + 1}: |aᵢᵢ| = {format_scalar(diagonal)} "
            f"{'>' if diagonal > others else '≤'} {format_scalar(others)}"
            for i, (diagonal, others) in enumerate(result.dominance)
        ]
        dominance.append(
            "Dominancia diagonal estricta por filas. Es una condición suficiente de convergencia."
            if result.strictly_dominant else
            "Sin dominancia diagonal estricta. La convergencia depende del sistema."
        )
        formulas = []
        for i, variable in enumerate(variables):
            terms = " + ".join(
                f"({format_scalar(a.data[i][j])})·{variables[j]}" for j in range(size) if j != i
            ) or "0"
            formulas.append(f"{variable} = ({format_scalar(b[i])} − ({terms})) / ({format_scalar(a.data[i][i])})")
        preparation = "\n".join((
            *dominance, "", "Despejes", *formulas, "",
            "Vector inicial: (" + ", ".join(number(value) for value in result.initial) + ")",
        ))
        steps = []
        for step in result.steps:
            lines = []
            for i, variable in enumerate(variables):
                terms = []
                for j in range(size):
                    if i == j:
                        continue
                    fresh = selected is IterativeMethod.GAUSS_SEIDEL and j < i
                    value = step.values[j] if fresh else step.previous[j]
                    terms.append(f"({format_scalar(a.data[i][j])})·({number(value)})")
                total = " + ".join(terms) or "0"
                lines.append(
                    f"{variable} = ({format_scalar(b[i])} − ({total})) / "
                    f"({format_scalar(a.data[i][i])}) ≈ {number(step.values[i])}"
                )
            lines.extend((
                f"Cambio absoluto máximo = {number(step.error)}",
                f"Residuo máximo |b − Ax| = {number(step.residual)}",
            ))
            steps.append("\n".join(lines))
        reasons = {
            IterativeStop.EXACT: "El residuo del sistema es cero.",
            IterativeStop.TOLERANCE: (
                "Se cumplió la tolerancia de cambio absoluto entre iteraciones."
                if criterion.currentIndex() == 0 else "Se cumplió la tolerancia de residuo máximo."
            ),
            IterativeStop.LIMIT: (
                f"No convergió. Se detuvo en la iteración {len(result.steps)} "
                "por alcanzar el máximo de iteraciones."
            ),
            IterativeStop.RANGE: (
                f"No convergió. Se completaron {len(result.steps)} iteraciones. "
                f"Falló la iteración {len(result.steps) + 1} por valores fuera del rango de presentación."
            ),
        }
        answer = "\n".join((
            reasons[result.stop],
            *(f"{variable} ≈ {number(value)}" for variable, value in zip(variables, result.values)),
            f"Criterio: {criterion.currentText()} < {tolerance.value()}",
            f"Error absoluto máximo = {number(result.steps[-1].error) if result.steps else '—'}",
            f"Residuo máximo |b − Ax| = {number(result.residual)}",
        ))
        rows = [(0, *(float(value) for value in result.initial), None, None)]
        rows.extend(
            (step.index, *(float(value) for value in step.values), float(step.error), float(step.residual))
            for step in result.steps
        )
        return Result(
            answer, steps=tuple(steps), headers=("k", *variables, "Cambio absoluto", "Residuo"),
            rows=tuple(rows), sections=(preparation,),
            title=(f"Sin convergencia · {selected.value}"
                   if result.stop in (IterativeStop.LIMIT, IterativeStop.RANGE)
                   else f"Aproximación por {selected.value}"),
            badge=f"{len(result.steps)} iteraciones",
        )

    page = ToolPage(
        "JS", "Jacobi y Gauss–Seidel", "Resuelve Ax = b por aproximaciones sucesivas y revisa cada sustitución.",
        [mode, (coefficients, constants), equations, label("Cargar ejemplo", "caption"), examples,
         label("Aproximación inicial y parada", "heading"), (initial, tolerance),
         (criterion_field, limit_field)],
        "Resolver sistema", calculate, above=(method, description),
        before=("Dominancia y despejes",), walk_title="Iteraciones",
        paginated_table=True,
    )
    mode.currentIndexChanged.connect(show_fields)
    method.currentIndexChanged.connect(show_fields)
    examples.activated.connect(load_example)
    criterion.currentIndexChanged.connect(page._clear)
    limit.valueChanged.connect(page._clear)
    page.walk.index.valueChanged.connect(lambda index: page.iterations.select_iteration(index + 1))
    show_fields()
    return page
