"""
Gaussian elimination.

`to_ref` walks the matrix down to a row echelon form: the staircase of zeros,
with every pivot normalized to 1. It runs on a single `Worksheet`, so the result
and the step by step are two readings of the same walk and cannot drift apart.
"""

from dataclasses import dataclass

from .matrix import Matrix
from .steps import StepLog
from .worksheet import Worksheet

@dataclass(frozen=True)
class Elimination:
    """What a reduction produced: the result, how it got there, were the pivots are"""

    original: Matrix
    result: Matrix
    log: StepLog
    pivots: tuple[tuple[int, int], ...]

    @property
    def rank(self) -> int:
        """The number of pivots, which is the rank of the matrix."""
        return len(self.pivots)

    def pivot_columns(self) -> list[int]:
        """The 1-based columns holding a pivot."""
        return [col for _row, col in self.pivots]

    def free_columns(self) -> list[int]:
        """The 1-based columns with no pivot: the free variables of a system."""
        held = set(self.pivot_columns())
        return [col for col in range(1, self.result.cols + 1) if col not in held]

    def zero_rows(self) -> list[int]:
        """The 1-based rows that ended up entirely zero."""
        return [i for i in range(1, self.result.rows + 1) if self.result.is_zero_row(i)]

def to_ref(matrix: Matrix, title: str = "") -> Elimination:
    """
    Reduce to a row echelon form, recording every elementary operation.

    One pivot per column, normalized to 1, with zeros beneath it. A column that
    is all zeros from `row` down holds no pivot and is left alone; the same row
    then goes looking one column further right, which is what makes the
    staircase uneven when a variable turns out to be free.
    """
    sheet = Worksheet(matrix, title)
    pivots = _forward(sheet)
    row = 1

    for col in range(1, matrix.cols + 1):
        if row > matrix.rows:
            break

        pivot_row = _find_pivot_row(sheet.matrix, row, col)
        if pivot_row is None:
            continue

        sheet.swap(row, pivot_row)
        sheet.scale(row, 1 / sheet.matrix.elem(row, col))
        for below in range(row + 1, matrix.rows + 1):
            sheet.add_scaled(below, row, -sheet.matrix.elem(below, col))

        pivots.append((row, col))
        row += 1

    return Elimination(matrix, sheet.matrix, sheet.log, tuple(pivots))

def rank(matrix: Matrix) -> int:
    """How many pivots the echelon form of this matrix has."""
    return to_ref(matrix).rank

def _find_pivot_row(matrix: Matrix, from_row: int, col: int) -> int | None:
    """The first row at or below `from_row` whose entry in `col` is not zero."""
    for row in range(from_row, matrix.rows + 1):
        if matrix.elem(row, col) != 0:
            return row
    return None