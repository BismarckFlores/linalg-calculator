"""
The blackboard: a matrix being worked on, and the record of what was done to it.

`Matrix` stays a plain value and `StepLog` stays a plain record; a `Worksheet`
is the pair, and the only place where an elementary operation both happens and
gets written down. An algorithm reads like the blackboard it imitates:

    sheet = Worksheet(a)
    sheet.swap(1, 2)
    sheet.scale(1, Fraction(1, 3))
    sheet.add_scaled(2, 1, -4)

Every reduction in the project runs through here, so the step by step is never
something an algorithm has to remember to keep.
"""

from .matrix import Matrix
from .scalar import NumberLike, to_scalar
from .steps import StepLog, label_add_scaled, label_scale, label_swap

class Worksheet:
    """A matrix plus the log of the operations applied to it."""

    def __init__(self, matrix: Matrix, title: str = "") -> None:
        self.matrix = matrix
        self.log = StepLog(matrix, title)

    def swap(self, i: int, j: int) -> Matrix:
        """f_i <-> f_j. Swapping a row with itself changes nothing and is skipped."""
        if i == j:
            return self.matrix
        return self._apply(self.matrix.swap_rows(i, j), label_swap(i, j))

    def scale(self, i: int, factor: NumberLike) -> Matrix:
        """f_i -> k*f_i. A factor of 1 is not written down: it does nothing."""
        factor = to_scalar(factor)
        if factor == 1:
            return self.matrix
        return self._apply(self.matrix.scale_row(i, factor), label_scale(i, factor))

    def add_scaled(self, i: int, j: int, factor: NumberLike) -> Matrix:
        """f_i -> f_i + k*f_j. A factor of 0 is not written down."""
        factor = to_scalar(factor)
        if factor == 0:
            return self.matrix
        return self._apply(
            self.matrix.add_scaled_row(i, j, factor), label_add_scaled(i, j, factor)
        )

    def _apply(self, result: Matrix, label: str) -> Matrix:
        """Record the operation and move the blackboard on to its result."""
        self.log.record(self.matrix, label, result)
        self.matrix = result
        return result