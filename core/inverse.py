"""
The inverse of a square matrix, found by the elimination already here.

A⁻¹ is the matrix that undoes A: `A A⁻¹ = A⁻¹ A = I`. It is found by reducing
`[A | I]` to its reduced row echelon form. Every row operation that turns A
into I does the same thing to I, and what I becomes is exactly A⁻¹. If the left
block cannot reach I, the matrix has fewer than n pivots and no inverse exists.

Once there is an inverse, `A x = b` is solved by multiplying: `x = A⁻¹ b`. That
is a different road to the answer than the elimination takes, and it only works
when A is invertible, so a singular system still belongs to `core/systems.py`.

Nothing here is trusted on its own word: both products are worked out and
compared with the identity, and the solution is put back into `A x`.

Like the rest of `core`, this says nothing to anybody. It returns the matrices
and raises; the window decides the Spanish.
"""

from dataclasses import dataclass

from .elimination import Elimination, to_rref
from .matrix import Matrix


class SingularMatrix(ValueError):
    """A square matrix with fewer than n pivots, which has no inverse."""


@dataclass(frozen=True)
class InverseResult:
    """
    An inverse and everything it took to find it.

    `reduction` is the walk from `[A | I]` to `[I | A⁻¹]`, so the step by step
    and the answer are two readings of the same elimination. `left_check` and
    `right_check` are the two products, kept rather than thrown away, because
    showing them is what proves the answer.
    """

    original: Matrix
    inverse: Matrix
    reduction: Elimination
    left_check: Matrix
    right_check: Matrix


@dataclass(frozen=True)
class InverseSystem:
    """A system solved by the inverse: `x = A⁻¹ b`, and `A x` put back."""

    inverse_result: InverseResult
    constants: Matrix
    solution: Matrix
    check: Matrix


def invert(matrix: Matrix) -> InverseResult:
    """
    Reduce `[A | I]` and read A⁻¹ off the right half.

    The left half reaching I is the invertible matrix theorem in practice: it
    happens exactly when A has n pivot positions. When it does not, the matrix
    is singular and there is nothing to return.
    """
    if matrix.rows == 0 or matrix.cols == 0 or not matrix.is_square():
        raise ValueError("The matrix must be nonempty and square.")

    # I is augmented on the right, so every operation that works on A works on
    # it at the same time. That is the whole method: A becomes I, I becomes A⁻¹.
    identity = Matrix.identity(matrix.rows)
    reduction = to_rref(matrix.augment(identity))

    if reduction.result.take_columns(1, matrix.rows) != identity:
        raise SingularMatrix("The matrix is singular.")

    inverse = reduction.result.take_columns(matrix.rows + 1, 2 * matrix.rows)
    left_check = matrix * inverse
    right_check = inverse * matrix

    # Both products, not one. AB = I alone is enough for a square matrix by the
    # theorem, but checking the pair costs one multiplication and answers the
    # definition instead of relying on it.
    if left_check != identity or right_check != identity:
        raise ArithmeticError("The inverse failed verification.")

    return InverseResult(matrix, inverse, reduction, left_check, right_check)


def solve_with_inverse(matrix: Matrix, constants: Matrix) -> InverseSystem:
    """
    Solve `A x = b` as `x = A⁻¹ b`, and check it in the original A.

    Multiplying both sides of `A x = b` by A⁻¹ on the left gives `x = A⁻¹ b`,
    and since A is invertible that x is the only solution. The check multiplies
    A by it and compares with b, which trusts neither the inverse nor the
    elimination that produced it.
    """
    if constants.size() != (matrix.rows, 1):
        raise ValueError("The constants must be a column with one entry per row.")

    result = invert(matrix)
    solution = result.inverse * constants
    check = matrix * solution

    if check != constants:
        raise ArithmeticError("The solution failed verification.")

    return InverseSystem(result, constants, solution, check)
