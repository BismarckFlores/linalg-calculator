"""
Gaussian elimination, in its two forms.

`to_ref` walks the matrix down to a row echelon form: the staircase of zeros,
with every pivot normalized to 1. `to_rref` keeps going and clears the entries
*above* each pivot as well, leaving the reduced row echelon form, where a pivot
is the only non-zero entry in its column.

Both run on a single `Worksheet`, so the result and the step by step are two
readings of the same walk and cannot drift apart. They also share the walk:
`to_rref` is `to_ref` followed by a second pass, never a second algorithm.
"""

from dataclasses import dataclass

from .matrix import Matrix
from .steps import StepLog
from .worksheet import Worksheet

@dataclass(frozen=True)
class Elimination:
    """What a reduction produced: the result, how it got there, where the pivots are"""

    original: Matrix
    result: Matrix
    log: StepLog
    pivots: tuple[tuple[int, int], ...]
    reduced: bool = False

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
    return Elimination(matrix, sheet.matrix, sheet.log, tuple(pivots))

def to_rref(matrix: Matrix, title: str = "") -> Elimination:
    """
    Reduce to the reduced row echelon form: Gauss-Jordan.

    The same walk down as `to_ref`, and then back up: starting from the pivot
    furthest to the right, every entry above a pivot is cleared too. What comes
    out satisfies the two extra conditions of the reduced form, that each
    leading entry is 1 and is the only non-zero entry in its column.

    Going back up never moves a pivot, so the positions found on the way down
    are still the positions on the way out.
    """
    sheet = Worksheet(matrix, title)
    pivots = _forward(sheet)
    _backward(sheet, pivots)
    return Elimination(matrix, sheet.matrix, sheet.log, tuple(pivots), reduced=True)

def rank(matrix: Matrix) -> int:
    """How many pivots the echelon form of this matrix has."""
    return to_ref(matrix).rank

def _forward(sheet: Worksheet) -> list[tuple[int, int]]:
    """
    The walk down: find a pivot, scale it to 1, clear everything below it.

    Returns the pivot positions in the order they were found, which is by row.
    """
    pivots: list[tuple[int, int]] = []
    row = 1

    for col in range(1, sheet.matrix.cols + 1):
        if row > sheet.matrix.rows:
            break

        pivot_row = _find_pivot_row(sheet.matrix, row, col)
        if pivot_row is None:
            continue

        sheet.swap(row, pivot_row)
        sheet.scale(row, 1 / sheet.matrix.elem(row, col))
        for below in range(row + 1, sheet.matrix.rows + 1):
            sheet.add_scaled(below, row, -sheet.matrix.elem(below, col))

        pivots.append((row, col))
        row += 1

    return pivots

def _backward(sheet: Worksheet, pivots: list[tuple[int, int]]) -> None:
    """
    The walk back up: clear the entries above each pivot, rightmost pivot first.

    Right to left matters. A pivot further right has already been isolated by
    the time it is used to clear the column of a pivot further left, so no
    operation here can put back a zero that a later one removed.

    Nothing is scaled: `_forward` left every pivot at 1 already.
    """
    for row, col in reversed(pivots):
        for above in range(1, row):
            sheet.add_scaled(above, row, -sheet.matrix.elem(above, col))

def _find_pivot_row(matrix: Matrix, from_row: int, col: int) -> int | None:
    """The first row at or below `from_row` whose entry in `col` is not zero."""
    for row in range(from_row, matrix.rows + 1):
        if matrix.elem(row, col) != 0:
            return row
    return None