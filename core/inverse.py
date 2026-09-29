from dataclasses import dataclass

from .elimination import Elimination, to_rref
from .matrix import Matrix


class SingularMatrix(ValueError):
    pass


@dataclass(frozen=True)
class InverseResult:
    original: Matrix
    inverse: Matrix
    reduction: Elimination
    left_check: Matrix
    right_check: Matrix


@dataclass(frozen=True)
class InverseSystem:
    inverse_result: InverseResult
    constants: Matrix
    solution: Matrix
    check: Matrix


def invert(matrix: Matrix) -> InverseResult:
    if matrix.rows == 0 or matrix.cols == 0 or not matrix.is_square():
        raise ValueError("The matrix must be nonempty and square.")

    identity = Matrix.identity(matrix.rows)
    reduction = to_rref(matrix.augment(identity))

    if reduction.result.take_columns(1, matrix.rows) != identity:
        raise SingularMatrix("The matrix is singular.")

    inverse = reduction.result.take_columns(matrix.rows + 1, 2 * matrix.rows)
    left_check = matrix * inverse
    right_check = inverse * matrix

    if left_check != identity or right_check != identity:
        raise ArithmeticError("The inverse failed verification.")

    return InverseResult(matrix, inverse, reduction, left_check, right_check)


def solve_with_inverse(matrix: Matrix, constants: Matrix) -> InverseSystem:
    if constants.size() != (matrix.rows, 1):
        raise ValueError("The constants must be a column with one entry per row.")

    result = invert(matrix)
    solution = result.inverse * constants
    check = matrix * solution

    if check != constants:
        raise ArithmeticError("The solution failed verification.")

    return InverseSystem(result, constants, solution, check)
