"""Lectura de matrices y sistemas compartida por las herramientas de álgebra."""

from PySide6.QtWidgets import QHBoxLayout

from core.linear_algebra.handlers.equations import parse_equation, to_augmented, unknown_names
from core.linear_algebra.handlers.matrix import Matrix

from desktop.core.math_input import MathInput
from desktop.core.math_notation import matrix_rows
from desktop.core.widgets import SegmentedControl, Stepper, label


EXAMPLE = "1;-2;1\n0;2;-8\n-4;5;9"
CONSTANTS = "0\n8\n-9"
EQUATIONS = "x - 2y + z = 0\n2y - 8z = 8\n-4x + 5y + 9z = -9"


class MatrixInput(MathInput):
    """Matriz editable, con dimensiones ajustables y pegado de filas."""

    def __init__(self, value: str, name: str, *, max_size: int = 10, column: bool = False) -> None:
        super().__init__(value, "", "matrix")
        self.name = name
        self.text.setAccessibleName(name)
        self.max_size = max_size
        self.column = column
        self._cells: dict[tuple[int, int], str] = {}
        layout = QHBoxLayout()
        layout.setSpacing(6)
        rows = matrix_rows(value)
        self._shape = len(rows), len(rows[0])
        self.rows = Stepper("Filas", 1, max_size, len(rows))
        self.cols = Stepper("Columnas", 1, 1 if column else max_size, len(rows[0]))
        layout.addWidget(label(name.upper(), "fieldTitle"))
        layout.addSpacing(8)
        for caption, size in (("Filas", self.rows), ("Columnas", self.cols)):
            if column and size is self.cols:
                continue
            field_label = label(caption, "caption")
            field_label.setWordWrap(False)
            layout.addWidget(field_label)
            layout.addWidget(size)
            layout.addSpacing(8)
            size.valueChanged.connect(self._resize)
        layout.addStretch()
        self.layout().insertLayout(0, layout)
        self.changed.connect(self._sync_size)

    def _sync_size(self) -> None:
        try:
            rows = matrix_rows(self.value())
        except ValueError:
            pass
        else:
            self._shape = len(rows), len(rows[0])
        for control, count in zip((self.rows, self.cols), self._shape):
            old = control.blockSignals(True)
            control.setValue(count)
            control.blockSignals(old)

    def clear(self) -> None:
        self._cells.clear()
        row = ";".join(["0"] * self.cols.value())
        self.set_value("\n".join([row] * self.rows.value()))

    def _resize(self) -> None:
        try:
            current = matrix_rows(self.value())
        except ValueError:
            self._sync_size()
            return
        self._cells.update(
            ((i, j), cell) for i, row in enumerate(current) for j, cell in enumerate(row)
        )
        rows, cols = self.rows.value(), self.cols.value()
        self.set_value("\n".join(
            ";".join(self._cells.get((i, j), "0") for j in range(cols)) for i in range(rows)
        ))

    def matrix(self) -> Matrix:
        rows = matrix_rows(self.value())
        if len(rows) > self.max_size or len(rows[0]) > self.max_size:
            raise ValueError(f"Se admiten hasta {self.max_size} filas y columnas.")
        if self.column and len(rows[0]) != 1:
            raise ValueError("Escribe el vector b en una sola columna.")
        return Matrix(rows)


def read_equations(editor: MathInput, max_size: int) -> tuple[Matrix, list[str]]:
    lines = [line.strip() for line in editor.value().splitlines() if line.strip()]
    if not 1 <= len(lines) <= max_size:
        raise ValueError(f"Escribe entre 1 y {max_size} ecuaciones, una por línea.")
    parsed = []
    for index, line in enumerate(lines, 1):
        try:
            parsed.append(parse_equation(line))
        except ValueError as problem:
            raise ValueError(f"Ecuación {index}. {problem}") from problem
    names = unknown_names(parsed)
    if not 1 <= len(names) <= max_size:
        raise ValueError(f"El sistema debe tener entre 1 y {max_size} incógnitas.")
    return to_augmented(parsed, names), names


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


class MatrixTaskFields:
    """Comparte la entrada de matriz sola o de sistema para inversa y LU."""

    def __init__(self, task: str, matrix: str, vector: str, example: str, *, max_size: int = 10) -> None:
        self.task = SegmentedControl(task, "Resolver A x = b")
        self.task.setAccessibleName("Tarea")
        self.mode, self.coefficients, self.constants, self.equations = system_input(
            max_size=max_size, matrix=matrix, vector=vector, example=example,
        )
        self.fields = [self.mode, (self.coefficients, self.constants), self.equations]
        self.constants.hide()
        self.equations.hide()
        self.mode.currentIndexChanged.connect(self._show_fields)
        self.task.currentIndexChanged.connect(self._show_fields)

    def _show_fields(self) -> None:
        by_equations = self.mode.currentIndex() == 1
        self.coefficients.setVisible(not by_equations)
        self.constants.setVisible(self.task.currentIndex() == 1 and not by_equations)
        self.equations.setVisible(by_equations)

    def read(self) -> tuple[Matrix, Matrix | None, list[str]]:
        solve_system = self.task.currentIndex() == 1
        if self.mode.currentIndex() == 1:
            augmented, names = read_equations(self.equations, self.coefficients.max_size)
            coefficients = augmented.take_columns(1, len(names))
            constants = augmented.take_columns(len(names) + 1, augmented.cols) if solve_system else None
            return coefficients, constants, names
        return self.coefficients.matrix(), self.constants.matrix() if solve_system else None, []
