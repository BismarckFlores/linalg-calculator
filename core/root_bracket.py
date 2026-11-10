"""Validación, parada y traza comunes a los métodos con intervalo."""

import math
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from .real_function import RealFunction, RootInputError
from .scalar import NumberLike, to_scalar


class RootCriterion(Enum):
    """La magnitud que se compara estrictamente con la tolerancia."""

    WIDTH = "width"
    RESIDUAL = "residual"
    RELATIVE = "relative"


class RootStop(Enum):
    """Por que termino el recorrido; el limite no significa convergencia."""

    ZERO = "zero"
    TOLERANCE = "tolerance"
    LIMIT = "limit"
    STAGNATION = "stagnation"


def read_root_number(value: NumberLike) -> float:
    """Lee tambien comas decimales y fracciones, usando el lector existente."""
    if isinstance(value, str):
        if len(value) > 128:
            raise RootInputError("El número escrito es demasiado largo.")
        # Fraction materializa el exponente; no tiene sentido construir millones
        # de cifras para un valor que float no puede representar.
        for part in value.lower().split("/"):
            if "e" in part:
                try:
                    exponent = int(part.split("e", 1)[1])
                except ValueError:
                    break
                if abs(exponent) > 10000:
                    raise RootInputError("El exponente excede la representación numérica disponible.")
    try:
        result = float(to_scalar(value))
    except (ValueError, TypeError, OverflowError) as problem:
        raise RootInputError(f"Se necesita un número real finito: {value!r}.") from problem
    if not math.isfinite(result):
        raise RootInputError("Los parámetros deben ser números reales finitos.")
    if result == 0 and to_scalar(value) != 0:
        raise RootInputError("El número es demasiado pequeño para representarlo (underflow).")
    return result


@dataclass(frozen=True)
class BracketStep:
    """El intervalo antes del corte, la aproximacion y las medidas sin redondear."""

    index: int
    a: float
    b: float
    c: float
    fa: float
    fb: float
    fc: float
    relative_error: float | None

    @property
    def width(self) -> float:
        return self.b - self.a

    @property
    def bound(self) -> float:
        # max conserva una cota aun si el punto medio se redondeo hacia un lado.
        return max(self.c - self.a, self.b - self.c)

    @property
    def residual(self) -> float:
        return abs(self.fc)

    @property
    def keep_left(self) -> bool:
        # No se multiplican valores: su producto podria desbordar o hacerse cero.
        return (self.fa < 0) != (self.fc < 0)


@dataclass(frozen=True)
class BracketResult:
    """La respuesta y la traza que la produjo, tambien cuando no converge."""

    function: RealFunction
    initial_a: float
    initial_b: float
    tolerance: float
    criterion: RootCriterion
    steps: tuple[BracketStep, ...]
    stop: RootStop
    root: float
    value: float
    a: float
    b: float

    @property
    def converged(self) -> bool:
        return self.stop in (RootStop.ZERO, RootStop.TOLERANCE)

    @property
    def bound(self) -> float:
        return max(self.root - self.a, self.b - self.root)


def solve_bracket(
    function: RealFunction | str,
    a: NumberLike,
    b: NumberLike,
    tolerance: NumberLike,
    criterion: RootCriterion,
    max_iterations: int,
    estimate: Callable[[float, float, float, float], float],
) -> BracketResult:
    """Comparte validación, intervalo, condiciones de parada y registro."""
    if isinstance(function, str):
        function = RealFunction(function)
    a, b, tolerance = (read_root_number(v) for v in (a, b, tolerance))
    if a >= b:
        raise RootInputError("El extremo inferior a debe ser menor que b.")
    if not math.isfinite(b - a):
        raise RootInputError("El intervalo es demasiado ancho para representarlo.")
    if tolerance <= 0:
        raise RootInputError("La tolerancia E debe ser mayor que cero.")
    if type(max_iterations) is not int or not 1 <= max_iterations <= 1000:
        raise RootInputError("El máximo de iteraciones debe ser un entero entre 1 y 1000.")
    if not isinstance(criterion, RootCriterion):
        raise RootInputError("El criterio de parada no es válido.")
    initial_a, initial_b = a, b
    steps: list[BracketStep] = []

    def finish(stop: RootStop, c: float, fc: float) -> BracketResult:
        return BracketResult(
            function, initial_a, initial_b, tolerance, criterion,
            tuple(steps), stop, c, fc, a, b,
        )

    fa = function(a)
    if fa == 0:
        b = a
        return finish(RootStop.ZERO, a, fa)
    fb = function(b)
    if fb == 0:
        a = b
        return finish(RootStop.ZERO, b, fb)
    if (fa < 0) == (fb < 0):
        raise RootInputError(
            "f(a) y f(b) tienen el mismo signo. El método requiere un intervalo "
            "con cambio de signo."
        )

    previous: float | None = None
    for index in range(1, max_iterations + 1):
        c = estimate(a, b, fa, fb)
        fc = function(c)
        relative = abs((c - previous) / c) * 100 if previous is not None and c != 0 else None
        if relative is not None and not math.isfinite(relative):
            relative = None
        step = BracketStep(index, a, b, c, fa, fb, fc, relative)
        steps.append(step)
        if fc == 0:
            a = b = c
            return finish(RootStop.ZERO, c, fc)
        stagnant = c == a or c == b
        measure = {
            RootCriterion.WIDTH: step.width,
            RootCriterion.RESIDUAL: step.residual,
            RootCriterion.RELATIVE: relative,
        }[criterion]
        # El ancho o residuo pueden satisfacer ya E aunque no quede otro float
        # intermedio. Un cambio relativo nulo por estancamiento no prueba nada.
        if measure is not None and measure < tolerance and not (
            stagnant and criterion is RootCriterion.RELATIVE
        ):
            return finish(RootStop.TOLERANCE, c, fc)
        if stagnant:
            return finish(RootStop.STAGNATION, c, fc)
        if index == max_iterations:
            return finish(RootStop.LIMIT, c, fc)
        if step.keep_left:
            b, fb = c, fc
        else:
            a, fa = c, fc
        previous = c

    raise AssertionError("El bucle siempre termina con un resultado.")
