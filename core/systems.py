"""
Linear systems, read out of an augmented matrix [A | b].

`solve` reduces the augmented matrix by row elimination and classifies the
system the way Rouche-Frobenius does: compare the rank of the coefficient matrix
with the rank of the augmented one, and then with the number of unknowns.

    rank(A) < rank(A|b)                 no solution
    rank(A) = rank(A|b) < unknowns      infinitely many
    rank(A) = rank(A|b) = unknowns      exactly one

When there is exactly one solution the unknowns are cleared by back
substitution, from the last to the first, and every one of those steps is kept:
seeing the echelon matrix and then the clearing is the point of the method.

Nothing here writes a sentence for a user: the interface decides the wording.
"""

from dataclasses import dataclass
from enum import Enum

from .elimination import Elimination, to_ref
from .matrix import Matrix
from .scalar import Scalar
from .steps import StepLog

class SystemKind(Enum):
    """The Rouche-Frobenius classification of a system."""

    INCONSISTENT = "inconsistent"
    UNIQUE = "unique"
    INFINITE = "infinite"

@dataclass(frozen=True)
class BackSubstitution:
    """One unknown cleared from the echelon form, and what it took to clear it."""

    column: int
    row: int
    constant: Scalar
    terms: tuple[tuple[Scalar, int], ...]
    value: Scalar

@dataclass(frozen=True)
class Solution:
    """What the echelon form says about the system."""

    kind: SystemKind
    reduction: Elimination
    unknowns: int
    values: tuple[Scalar, ...]
    free_columns: tuple[int, ...]
    homogeneous: bool
    substitutions: tuple[BackSubstitution, ...]

    @property
    def log(self) -> StepLog:
        return self.reduction.log

    @property
    def augmented(self) -> Matrix:
        """The [A | b] the system was handed in as."""
        return self.reduction.original

    @property
    def result(self) -> Matrix:
        """The echelon form the elimination ended on."""
        return self.reduction.result

    @property
    def coefficients(self) -> Matrix:
        """A on its own, for putting a solution back into the original system."""
        return self.augmented.take_columns(1, self.unknowns)

    @property
    def constants(self) -> Matrix:
        """b on its own, as a single column."""
        return self.augmented.take_columns(self.unknowns + 1, self.unknowns + 1)

    @property
    def rank(self) -> int:
        """Rank of the augmented matrix."""
        return self.reduction.rank

    @property
    def coefficient_rank(self) -> int:
        """Rank of A: the pivots that fall on an unknown, not on the constants."""
        return sum(1 for _row, col in self.reduction.pivots if col <= self.unknowns)

def solve(augmented: Matrix) -> Solution:
    """
    Solve the system written as an augmented matrix, last column the constants.

    The whole walk down to the echelon form is in `solution.log`, and the
    clearing that follows it is in `solution.substitutions`.
    """
    if augmented.rows < 1 or augmented.cols < 2:
        raise ValueError("A system needs at least one equation and one unknown.")

    unknowns = augmented.cols - 1
    reduction = to_ref(augmented)

    coefficient_rank = sum(1 for _row, col in reduction.pivots if col <= unknowns)
    free_columns = tuple(col for col in reduction.free_columns() if col <= unknowns)
    homogeneous = all(row[-1] == 0 for row in augmented.data)

    values: tuple[Scalar, ...] = ()
    substitutions: tuple[BackSubstitution, ...] = ()

    if reduction.rank > coefficient_rank:
        # A pivot landed on the constants column: some row reads 0 = k.
        kind = SystemKind.INCONSISTENT
    elif coefficient_rank < unknowns:
        # Fewer pivots than unknowns: the ones left over are free.
        kind = SystemKind.INFINITE
    else:
        kind = SystemKind.UNIQUE
        substitutions = _back_substitute(reduction, unknowns)
        cleared = {step.column: step.value for step in substitutions}
        values = tuple(cleared[col] for col in range(1, unknowns + 1))

    return Solution(
        kind, reduction, unknowns, values, free_columns, homogeneous, substitutions
    )

def _back_substitute(
    reduction: Elimination, unknowns: int
) -> tuple[BackSubstitution, ...]:
    """
    Walk the echelon form upwards, replacing the unknowns already cleared.

    Only ever called for a system with a unique solution, which is what lets it
    stay this short: every unknown holds a pivot, and every pivot is already 1
    because `to_ref` normalizes them. The steps come back in the order the work
    is done, so the last unknown is first.
    """
    echelon = reduction.result
    constants = unknowns + 1
    known: dict[int, Scalar] = {}
    cleared: list[BackSubstitution] = []

    for row, col in reversed(reduction.pivots):
        constant = echelon.elem(row, constants)
        terms = tuple(
            (echelon.elem(row, other), other)
            for other in range(col + 1, constants)
            if echelon.elem(row, other) != 0
        )
        value = constant - sum(
            (coefficient * known[other] for coefficient, other in terms),
            start=Scalar(0),
        )
        known[col] = value
        cleared.append(BackSubstitution(col, row, constant, terms, value))

    return tuple(cleared)