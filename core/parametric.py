"""
The general solution of a system that has infinitely many.

`systems.solve` stops at saying which variables are free. This writes the
family out: every basic variable — the one holding a pivot — in terms of the
free ones, which is what the course means by the general solution.

It reads the reduced form and nothing else. In the reduced form a pivot is 1
and alone in its column, so the row `x1 + 4*x3 = 1` is already the answer for
x1 with one sign change, and no back substitution is needed. Handing this an
unreduced echelon form would be a bug, so it refuses one.
"""

from dataclasses import dataclass

from .elimination import Elimination
from .scalar import Scalar

@dataclass(frozen=True)
class Basic:
    """One basic variable, written in terms of the free ones."""

    column: int
    constant: Scalar
    terms: tuple[tuple[Scalar, int], ...]

@dataclass(frozen=True)
class General:
    """The whole family: the basic variables, and the free ones they lean on."""

    basic: tuple[Basic, ...]
    free: tuple[int, ...]

def general_solution(reduction: Elimination, unknowns: int) -> General:
    """
    Read the family off the reduced form: every basic variable in terms of the
    free ones.

    Only the columns of A count as variables; a pivot on the constants column
    means the system has no solution at all, and there is no family to write.
    The caller classifies first and only asks when there is something to ask
    for.
    """
    if not reduction.reduced:
        raise ValueError("The general solution is read off the reduced form.")

    result = reduction.result
    constants = unknowns + 1
    pivots = [(row, column) for row, column in reduction.pivots if column <= unknowns]
    held = {column for _row, column in pivots}
    free = tuple(column for column in range(1, unknowns + 1) if column not in held)

    basic = tuple(
        Basic(
            column,
            result.elem(row, constants),
            tuple(
                (-result.elem(row, other), other)
                for other in free
                if result.elem(row, other) != 0
            ),
        )
        for row, column in pivots
    )
    return General(basic, free)
