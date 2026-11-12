"""Método abierto de la secante con registro de aproximaciones."""

import math
from dataclasses import dataclass

from core.scalar import NumberLike

from .handlers.open_root import open_tolerance
from .handlers.real_function import RealFunction, RootInputError
from .handlers.root_bracket import RootStop, read_root_number


@dataclass(frozen=True)
class SecantStep:
    index: int
    previous: float
    x: float
    previous_fx: float
    fx: float
    next_x: float
    next_fx: float

    @property
    def absolute_error(self) -> float:
        return abs(self.next_x - self.x)


@dataclass(frozen=True)
class SecantResult:
    function: RealFunction
    initial_x: float
    second_x: float
    tolerance: float
    steps: tuple[SecantStep, ...]
    stop: RootStop
    root: float
    value: float
    detail: str = ""

    @property
    def iterations(self) -> int:
        return len(self.steps)

    @property
    def converged(self) -> bool:
        return self.stop in (RootStop.ZERO, RootStop.TOLERANCE)


def secant(
    function: RealFunction | str,
    x0: NumberLike,
    x1: NumberLike,
    tolerance: NumberLike = "0.000001",
    *,
    max_iterations: int = 100,
) -> SecantResult:
    """Desplaza las dos últimas aproximaciones sin exigir cambio de signo."""
    if isinstance(function, str):
        function = RealFunction(function)
    initial_x = previous = read_root_number(x0)
    second_x = x = read_root_number(x1)
    tolerance = open_tolerance(tolerance, max_iterations)
    if previous == x:
        raise RootInputError("Las aproximaciones iniciales x₀ y x₁ deben ser distintas.")
    previous_fx = function(previous)
    steps: list[SecantStep] = []
    if previous_fx == 0:
        return SecantResult(function, initial_x, second_x, tolerance, (), RootStop.ZERO, previous, previous_fx)
    fx = function(x)

    def finish(stop: RootStop, detail: str = "") -> SecantResult:
        return SecantResult(function, initial_x, second_x, tolerance, tuple(steps), stop, x, fx, detail)

    if fx == 0:
        return finish(RootStop.ZERO)

    for index in range(1, max_iterations + 1):
        denominator = fx - previous_fx
        if denominator == 0:
            return finish(RootStop.ZERO_DENOMINATOR, "La secante tiene denominador cero: ambas evaluaciones coinciden.")
        if math.isfinite(denominator):
            ratio = fx / denominator
        else:
            # La razón se conserva al escalar ambas ordenadas por el mismo valor.
            scale = max(abs(fx), abs(previous_fx))
            ratio = (fx / scale) / (fx / scale - previous_fx / scale)
        next_x = x - ratio * (x - previous)
        if not math.isfinite(next_x) or not math.isfinite(next_x - x):
            return finish(RootStop.NONFINITE_STEP, "La fórmula de la secante produjo un paso no finito.")
        if next_x == x:
            return finish(RootStop.STAGNATION, "La precisión numérica impide cambiar la aproximación.")
        try:
            next_fx = function(next_x)
        except RootInputError as problem:
            return finish(RootStop.EVALUATION_ERROR, str(problem))

        step = SecantStep(index, previous, x, previous_fx, fx, next_x, next_fx)
        steps.append(step)
        previous, previous_fx = x, fx
        x, fx = next_x, next_fx
        if fx == 0:
            return finish(RootStop.ZERO)
        if step.absolute_error <= tolerance:
            return finish(RootStop.TOLERANCE)

    return finish(RootStop.LIMIT)
