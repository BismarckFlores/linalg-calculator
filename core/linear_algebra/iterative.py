"""Jacobi y Gauss–Seidel con aritmética exacta y traza por iteración."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from core.scalar import NumberLike, Scalar, to_scalar
from .handlers.matrix import Matrix


class IterativeMethod(Enum):
    JACOBI = "Jacobi"
    GAUSS_SEIDEL = "Gauss–Seidel"


class IterativeCriterion(Enum):
    ABSOLUTE = "Cambio absoluto"
    RESIDUAL = "Residuo"


class IterativeStop(Enum):
    EXACT = "exact"
    TOLERANCE = "tolerance"
    LIMIT = "limit"
    RANGE = "range"


@dataclass(frozen=True)
class IterativeStep:
    index: int
    previous: tuple[Scalar, ...]
    values: tuple[Scalar, ...]
    error: Scalar
    residual: Scalar


@dataclass(frozen=True)
class IterativeResult:
    method: IterativeMethod
    initial: tuple[Scalar, ...]
    values: tuple[Scalar, ...]
    dominance: tuple[tuple[Scalar, Scalar], ...]
    steps: tuple[IterativeStep, ...]
    stop: IterativeStop
    residual: Scalar

    @property
    def strictly_dominant(self) -> bool:
        return all(diagonal > others for diagonal, others in self.dominance)


def solve_iterative(
    coefficients: Matrix,
    constants: Sequence[NumberLike],
    *,
    method: IterativeMethod = IterativeMethod.JACOBI,
    criterion: IterativeCriterion = IterativeCriterion.ABSOLUTE,
    initial: Sequence[NumberLike] | None = None,
    tolerance: NumberLike = "0.0001",
    max_iterations: int = 50,
) -> IterativeResult:
    """Resuelve Ax=b conservando orden de ecuaciones y pasos completos."""
    n = coefficients.rows
    if n == 0 or coefficients.cols != n:
        raise ValueError("Jacobi y Gauss–Seidel requieren una matriz cuadrada no vacía.")
    if not isinstance(method, IterativeMethod):
        raise ValueError("Selecciona Jacobi o Gauss–Seidel.")
    if not isinstance(criterion, IterativeCriterion):
        raise ValueError("Selecciona un criterio de parada válido.")
    b = tuple(to_scalar(value) for value in constants)
    x = tuple(to_scalar(value) for value in initial) if initial is not None else (to_scalar(0),) * n
    if len(b) != n or len(x) != n:
        raise ValueError("A, b y el vector inicial deben tener dimensiones compatibles.")
    tolerance = to_scalar(tolerance)
    if tolerance <= 0:
        raise ValueError("La tolerancia debe ser mayor que cero.")
    if type(max_iterations) is not int or not 1 <= max_iterations <= 1000:
        raise ValueError("El máximo de iteraciones debe ser un entero entre 1 y 1000.")
    a = coefficients.data
    if any(a[i][i] == 0 for i in range(n)):
        raise ValueError("La diagonal contiene un cero. Reordena las ecuaciones para despejar cada variable.")
    try:
        if not all(math.isfinite(float(value)) for value in (*b, *x, tolerance, *(v for row in a for v in row))):
            raise OverflowError
    except OverflowError:
        raise ValueError("Los datos exceden el rango numérico de la presentación.") from None

    dominance = tuple((abs(a[i][i]), sum(abs(a[i][j]) for j in range(n) if i != j)) for i in range(n))
    start = x
    steps: list[IterativeStep] = []

    def residual(values: tuple[Scalar, ...]) -> Scalar:
        return max(abs(b[i] - sum(a[i][j] * values[j] for j in range(n))) for i in range(n))

    current_residual = residual(x)
    try:
        float(current_residual)
    except OverflowError:
        raise ValueError("El residuo inicial excede el rango numérico de la presentación.") from None

    def finish(stop: IterativeStop) -> IterativeResult:
        return IterativeResult(method, start, x, dominance, tuple(steps), stop, current_residual)

    if current_residual == 0:
        return finish(IterativeStop.EXACT)
    for index in range(1, max_iterations + 1):
        updated = list(x)
        for i in range(n):
            source = x if method is IterativeMethod.JACOBI else updated
            total = sum(a[i][j] * source[j] for j in range(n) if j != i)
            updated[i] = (b[i] - total) / a[i][i]
        values = tuple(updated)
        error = max(abs(new - old) for new, old in zip(values, x))
        next_residual = residual(values)
        try:
            if not all(math.isfinite(float(value)) for value in (*values, error, next_residual)):
                raise OverflowError
        except OverflowError:
            return finish(IterativeStop.RANGE)
        steps.append(IterativeStep(index, x, values, error, next_residual))
        x, current_residual = values, next_residual
        if current_residual == 0:
            return finish(IterativeStop.EXACT)
        measure = error if criterion is IterativeCriterion.ABSOLUTE else current_residual
        if measure < tolerance:
            return finish(IterativeStop.TOLERANCE)
    return finish(IterativeStop.LIMIT)
