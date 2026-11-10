"""Operaciones matriciales elementales."""

from core.scalar import to_scalar

from desktop.core.forms import Result, ToolPage
from desktop.core.math_input import MathInput
from desktop.core.widgets import SegmentedControl, label

from .core.inputs import MatrixInput
from .core.results import matrix_text


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
