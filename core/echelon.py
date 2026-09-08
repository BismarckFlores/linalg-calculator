"""
Reading the form of a matrix, instead of putting it in one.

`elimination` takes a matrix to the echelon form. This asks the opposite
question: the matrix as it stands, is it in that form already? The course
answers it with five numbered properties, and so does this module — one check
per property, each reporting the entry that breaks it when one does.

Checking property by property is the point. A single yes or no is not worth
much to somebody learning the definition; being told that property 2 fails at
row 3 is.

Nothing here decides a word. A `Condition` is a number, a verdict and the
position that justifies it; whoever draws it writes the sentence.
"""

from dataclasses import dataclass

from .elimination import to_rref
from .matrix import Matrix

# The five properties, numbered the way the course numbers them: the first
# three define the echelon form, and the last two the reduced one.
ECHELON = (1, 2, 3)
REDUCED = (4, 5)

@dataclass(frozen=True)
class Condition:
    """
    One numbered property, and the entry that breaks it when one does.

    `row` and `column` are 1-based and only meaningful when `holds` is false.
    Property 1 is the exception: it fails at a whole row, so `column` stays 0.
    """

    number: int
    holds: bool
    row: int = 0
    column: int = 0

@dataclass(frozen=True)
class Form:
    """What form a matrix is in, property by property."""

    matrix: Matrix
    conditions: tuple[Condition, ...]
    leading: tuple[tuple[int, int], ...]

    def condition(self, number: int) -> Condition:
        """The verdict on one numbered property."""
        for condition in self.conditions:
            if condition.number == number:
                return condition
        raise ValueError(f"There is no property number {number}.")

    @property
    def is_echelon(self) -> bool:
        """Whether the first three properties all hold."""
        return all(self.condition(number).holds for number in ECHELON)

    @property
    def is_reduced(self) -> bool:
        """Whether all five do."""
        return self.is_echelon and all(
            self.condition(number).holds for number in REDUCED
        )

def leading_column(matrix: Matrix, row: int) -> int | None:
    """
    The column of the leading entry of a row: its leftmost entry that is not
    zero.

    A row of zeros has none, which is what `None` says. Every property below is
    written in terms of these, exactly as the definition is.
    """
    for column in range(1, matrix.cols + 1):
        if matrix.elem(row, column) != 0:
            return column
    return None

def leading_entries(matrix: Matrix) -> tuple[tuple[int, int], ...]:
    """The position of every leading entry, in row order."""
    found = []
    for row in range(1, matrix.rows + 1):
        column = leading_column(matrix, row)
        if column is not None:
            found.append((row, column))
    return tuple(found)

def analyse(matrix: Matrix) -> Form:
    """
    Check the five properties against a matrix exactly as they are written.

    A matrix of zeros passes all five: every property is a claim about the rows
    that are not zero, and it has none. That is not a special case handled here,
    it is what the loops do when there is nothing to loop over.
    """
    leading = leading_entries(matrix)
    return Form(
        matrix,
        (
            _zero_rows_last(matrix),
            _staircase(leading),
            _zeros_below(matrix, leading),
            _leading_ones(matrix, leading),
            _alone_in_column(matrix, leading),
        ),
        leading,
    )

def pivot_positions(matrix: Matrix) -> tuple[tuple[int, int], ...]:
    """
    The pivot positions of a matrix: where the leading entries of its reduced
    form are.

    The definition is not about the matrix as it stands. A pivot position of A
    is a place in A holding a leading entry once A is in reduced echelon form,
    so this reduces first and reports the positions it found on the way.
    """
    return to_rref(matrix).pivots

def pivot_columns(matrix: Matrix) -> tuple[int, ...]:
    """The columns holding a pivot position."""
    return tuple(column for _row, column in pivot_positions(matrix))

def free_columns(matrix: Matrix) -> tuple[int, ...]:
    """The columns that hold none."""
    held = set(pivot_columns(matrix))
    return tuple(column for column in range(1, matrix.cols + 1) if column not in held)

def _zero_rows_last(matrix: Matrix) -> Condition:
    """Property 1: no row of zeros sits above a row that is not zeros."""
    zeros_seen = False
    for row in range(1, matrix.rows + 1):
        if matrix.is_zero_row(row):
            zeros_seen = True
        elif zeros_seen:
            return Condition(1, False, row)
    return Condition(1, True)

def _staircase(leading: tuple[tuple[int, int], ...]) -> Condition:
    """Property 2: each leading entry stands to the right of the one above."""
    rightmost = 0
    for row, column in leading:
        if column <= rightmost:
            return Condition(2, False, row, column)
        rightmost = column
    return Condition(2, True)

def _zeros_below(matrix: Matrix, leading: tuple[tuple[int, int], ...]) -> Condition:
    """Property 3: under a leading entry, the rest of its column is zeros."""
    for row, column in leading:
        for below in range(row + 1, matrix.rows + 1):
            if matrix.elem(below, column) != 0:
                return Condition(3, False, below, column)
    return Condition(3, True)

def _leading_ones(matrix: Matrix, leading: tuple[tuple[int, int], ...]) -> Condition:
    """Property 4: every leading entry is a 1."""
    for row, column in leading:
        if matrix.elem(row, column) != 1:
            return Condition(4, False, row, column)
    return Condition(4, True)

def _alone_in_column(matrix: Matrix, leading: tuple[tuple[int, int], ...]) -> Condition:
    """Property 5: a leading entry is the only entry of its column that is not zero."""
    for row, column in leading:
        for other in range(1, matrix.rows + 1):
            if other != row and matrix.elem(other, column) != 0:
                return Condition(5, False, other, column)
    return Condition(5, True)
