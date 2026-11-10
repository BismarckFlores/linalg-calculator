"""Operaciones vectoriales y combinaciones lineales."""

from core.linear_algebra import vectors
from core.linear_algebra.handlers.matrix import Matrix
from core.scalar import to_scalar
from ui.presentation import describe, render_general, render_linear_sum, render_system, render_values, subscript

from desktop.core.forms import Result, ToolPage, text_input
from desktop.core.math_input import MathInput
from desktop.core.widgets import SegmentedControl, label

from .core.results import matrix_steps, matrix_text


def vectors_page() -> ToolPage:
    operation = SegmentedControl("u + v", "u − v", "k · u", "Combinación lineal")
    operation.setAccessibleName("Operación vectorial")
    first = MathInput("1, -2, 3", "u =", "vector", inline=True)
    second = MathInput("4, 0, -1/2", "v =", "vector", inline=True)
    scalar = MathInput("1/2", "k =", "number", inline=True)
    target = MathInput("1, -2, 3", "b =", "vector", inline=True)
    for editor in (first, second, target):
        editor.setMaximumWidth(434)
    scalar.setMaximumWidth(164)
    generators = text_input("Vectores generadores", "1, 0, 0\n0, 1, 0\n0, 0, 1", multiline=True)
    generators.setPlaceholderText("Un vector generador por línea")

    def show_fields() -> None:
        index = operation.currentIndex()
        first.setVisible(index != 3)
        target.setVisible(index == 3)
        second.setVisible(index < 2)
        scalar.setVisible(index == 2)
        generators.setVisible(index == 3)

    def read_vector(text: str):
        vector = vectors.parse_vector(text)
        if len(vector) > 10:
            raise ValueError("Se admiten hasta 10 componentes por vector.")
        return vector

    def calculate() -> Result:
        index = operation.currentIndex()
        u = read_vector(target.value() if index == 3 else first.value())
        if index == 3:
            lines = [line for line in generators.toPlainText().splitlines() if line.strip()]
            if not 1 <= len(lines) <= 10:
                raise ValueError("Escribe de 1 a 10 vectores, uno por línea.")
            found = vectors.combine([read_vector(line) for line in lines], u)
            solution = found.solution
            names = [f"c_{i}" for i in range(1, len(lines) + 1)]
            symbols = [f"v{subscript(i)}" for i in range(1, len(lines) + 1)]
            setup = render_system(solution.augmented, solution.unknowns, names)
            parts = [describe(solution), render_values(solution, names)]
            details = []
            if found.general:
                parts.extend(("Familia de escalares", render_general(found.general, names)))
            weights = found.weights
            if weights is not None:
                check = vectors.linear_sum(weights, found.vectors)
                details.extend((
                    "Comprobación con los escalares libres en cero" if found.general else "Comprobación",
                    f"b = {render_linear_sum(weights, symbols)}",
                    matrix_text(Matrix.column_vector(check)),
                    "La suma reproduce el vector objetivo." if check == u else "La suma difiere del vector objetivo.",
                ))
                for i, components in enumerate(zip(*found.vectors), 1):
                    terms = " + ".join(f"({k})({entry})" for k, entry in zip(weights, components))
                    details.append(f"b{subscript(i)} = {terms} = {check[i - 1]}")
            return Result("\n".join(parts), matrix_steps(solution.log), sections=(setup, "", "\n".join(details)))
        if index == 2:
            factor = to_scalar(scalar.value())
            result = vectors.scale(factor, u)
            title = "k · u"
            operations = [f"({factor})({entry})" for entry in u]
        else:
            v = read_vector(second.value())
            if index == 0:
                result, sign = vectors.add(u, v), "+"
            else:
                result, sign = vectors.subtract(u, v), "−"
            title = f"u {sign} v"
            operations = [f"({left}) {sign} ({right})" for left, right in zip(u, v)]
        lines = [f"{title} = ({', '.join(map(str, result))})", matrix_text(Matrix.column_vector(result))]
        details = "\n".join(
            f"Componente {i}: {expression} = {value}"
            for i, (expression, value) in enumerate(zip(operations, result), 1)
        )
        return Result("\n".join(lines), sections=("", details))

    help_text = label("Separa las componentes con comas o espacios, y usa punto decimal: 1, -2, 0.5, 1/3.\n"
                      "La dimensión es la cantidad de componentes que escribas.", "muted")
    page = ToolPage("↗", "Operaciones Vectoriales", "Suma dos vectores de ℝⁿ, componente a componente.",
                    [scalar, first, second, target, generators, help_text], "Calcular", calculate, above=(operation,),
                    before=("Planteamiento",), after=("Componente a componente", "Comprobación"))
    page.form.setSpacing(8)
    operation.currentIndexChanged.connect(show_fields)
    show_fields()
    return page
