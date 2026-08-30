"""
Putting a solution back where it came from.

Solving is one thing; showing that the answer holds is another, and it is the
only check that does not trust the elimination at all. Every equation of the
*original* system is evaluated with the values found, and the two sides are
compared exactly — no tolerance, because nothing here was ever rounded.

This module knows nothing about how the solution was reached: hand it A, b and
a list of values and it will tell you, row by row, whether Ax = b.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from .matrix import Matrix
from .scalar import NumberLike, Scalar, to_scalar

@dataclass(frozen=True)
class RowCheck:
    """One equation of the original system with the values put back into it."""

    row: int
    terms: tuple[tuple[Scalar, Scalar, int], ...]
    left: Scalar
    right: Scalar

    @property
    def holds(self) -> bool:
        """Whether this equation came out true."""
        return self.left == self.right

@dataclass(frozen=True)
class Verification:
    """The same check across every equation of the system."""

    checks: tuple[RowCheck, ...]

    @property
    def holds(self) -> bool:
        """True only when every single equation came out true."""
        return all(check.holds for check in self.checks)

    def failures(self) -> tuple[RowCheck, ...]:
        """The equations that did not hold, if any did not."""
        return tuple(check for check in self.checks if not check.holds)

def verify(
    coefficients: Matrix, constants: Matrix, values: Sequence[NumberLike]
) -> Verification:
    """
    Evaluate A x = b row by row with the values found.

    `constants` is b as a single column, the same shape it has inside
    augmented matrix. Each `RowCheck` keeps its terms as
    (coefficient, value, column) so an interface can write the substitution out
    in full instead of only reporting the total.
    """
    if constants.cols != 1:
        raise ValueError(f"The constants must be a single column, got {constants.cols}.")
    if coefficients.rows != constants.rows:
        raise ValueError(
            f"A has {coefficients.rows} rows and b has {constants.rows}: they must match."
        )
    if len(values) != coefficients.cols:
        raise ValueError(
            f"A has {coefficients.cols} unknowns and {len(values)} values were given."
        )

    found = [to_scalar(value) for value in values]
    checks: list[RowCheck] = []

    for row in range(1, coefficients.rows + 1):
        terms = tuple(
            (coefficients.elem(row, col), found[col - 1], col)
            for col in range(1, coefficients.cols + 1)
        )
        left = sum((coefficient * value for coefficient, value, _col in terms), Scalar(0))
        checks.append(RowCheck(row, terms, left, constants.elem(row, 1)))

    return Verification(tuple(checks))