"""
La pizarra: una matriz en la que se esta trabajando, y el registro de lo que se
le ha hecho.

Matrix sigue siendo un valor y StepLog un registro; un Worksheet es la pareja, y
el unico sitio donde una operacion elemental ocurre y queda apuntada a la vez.
Un algoritmo se lee como la pizarra que imita:

    sheet = Worksheet(a)
    sheet.swap(1, 2)
    sheet.scale(1, Fraction(1, 3))
    sheet.add_scaled(2, 1, -4)

Toda reduccion del proyecto pasa por aqui, asi que el paso a paso nunca es algo
que un algoritmo tenga que acordarse de guardar.
"""

from .matrix import Matrix
from .scalar import NumberLike, to_scalar
from .steps import StepLog, label_add_scaled, label_scale, label_swap

class Worksheet:
    """Una matriz junto con el registro de las operaciones que se le aplicaron."""

    def __init__(self, matrix: Matrix, title: str = "") -> None:
        self.matrix = matrix
        self.log = StepLog(matrix, title)

    def swap(self, i: int, j: int) -> Matrix:
        """f_i <-> f_j. Intercambiar una fila consigo misma no cambia nada y se omite."""
        if i == j:
            return self.matrix
        return self._apply(self.matrix.swap_rows(i, j), label_swap(i, j))

    def scale(self, i: int, factor: NumberLike) -> Matrix:
        """f_i -> k*f_i. Un factor de 1 no se apunta: no hace nada."""
        factor = to_scalar(factor)
        if factor == 1:
            return self.matrix
        return self._apply(self.matrix.scale_row(i, factor), label_scale(i, factor))

    def add_scaled(self, i: int, j: int, factor: NumberLike) -> Matrix:
        """f_i -> f_i + k*f_j. Un factor de 0 no se apunta."""
        factor = to_scalar(factor)
        if factor == 0:
            return self.matrix
        return self._apply(
            self.matrix.add_scaled_row(i, j, factor), label_add_scaled(i, j, factor)
        )

    def _apply(self, result: Matrix, label: str) -> Matrix:
        """Registra la operacion y deja la pizarra en el resultado."""
        self.log.record(self.matrix, label, result)
        self.matrix = result
        return result
