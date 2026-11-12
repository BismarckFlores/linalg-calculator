"""Método abierto de Newton–Raphson con registro de aproximaciones."""

import math
from dataclasses import dataclass

from core.calculus import differentiate
from core.scalar import NumberLike

from .handlers.open_root import open_tolerance
from .handlers.real_function import RealFunction, RootInputError
from .handlers.root_bracket import RootStop, read_root_number


@dataclass(frozen=True)
class NewtonStep:
    index: int
    x: float
    fx: float
    dfx: float
    next_x: float
    next_fx: float

    @property
    def absolute_error(self) -> float:
        return abs(self.next_x - self.x)


@dataclass(frozen=True)
class NewtonResult:
    function: RealFunction
    initial_x: float
    tolerance: float
    steps: tuple[NewtonStep, ...]
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


def newton_raphson(
    function: RealFunction | str,
    x0: NumberLike,
    tolerance: NumberLike = "0.000001",
    *,
    max_iterations: int = 100,
) -> NewtonResult:
    """Aproxima una raíz y conserva los pasos completados aunque el método falle."""
    if isinstance(function, str):
        function = RealFunction(function)
    initial_x = x = read_root_number(x0)
    tolerance = open_tolerance(tolerance, max_iterations)
    fx = function(x)
    steps: list[NewtonStep] = []

    def finish(stop: RootStop, detail: str = "") -> NewtonResult:
        return NewtonResult(function, initial_x, tolerance, tuple(steps), stop, x, fx, detail)

    if fx == 0:
        return finish(RootStop.ZERO)
    derivative = differentiate(function)

    for index in range(1, max_iterations + 1):
        try:
            dfx = derivative(x)
        except (ValueError, ArithmeticError, NotImplementedError) as problem:
            return finish(RootStop.EVALUATION_ERROR, f"No se puede evaluar f′(x) en x = {x:.17g}: {problem}")
        if not math.isfinite(dfx):
            return finish(RootStop.EVALUATION_ERROR, f"La derivada no es finita en x = {x:.17g}.")
        if dfx == 0:
            return finish(RootStop.ZERO_DERIVATIVE, f"La derivada vale cero en x = {x:.17g}.")

        next_x = x - fx / dfx
        if not math.isfinite(next_x) or not math.isfinite(next_x - x):
            return finish(RootStop.NONFINITE_STEP, "La fórmula de Newton produjo un paso no finito.")
        if next_x == x:
            return finish(RootStop.STAGNATION, "La precisión numérica impide cambiar la aproximación.")
        try:
            next_fx = function(next_x)
        except RootInputError as problem:
            return finish(RootStop.EVALUATION_ERROR, str(problem))

        step = NewtonStep(index, x, fx, dfx, next_x, next_fx)
        steps.append(step)
        x, fx = next_x, next_fx
        if fx == 0:
            return finish(RootStop.ZERO)
        if step.absolute_error <= tolerance:
            return finish(RootStop.TOLERANCE)

    return finish(RootStop.LIMIT)
