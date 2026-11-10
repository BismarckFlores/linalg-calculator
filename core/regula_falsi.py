"""Regla falsa clásica por el cruce de la secante con el eje x."""

from .real_function import RealFunction
from .root_bracket import BracketResult, RootCriterion, solve_bracket
from .scalar import NumberLike


def regula_falsi(
    function: RealFunction | str,
    a: NumberLike,
    b: NumberLike,
    tolerance: NumberLike = "0.01",
    *,
    criterion: RootCriterion = RootCriterion.RELATIVE,
    max_iterations: int = 100,
) -> BracketResult:
    """Regla falsa clásica sobre un intervalo con cambio de signo."""
    return solve_bracket(function, a, b, tolerance, criterion, max_iterations, _false_position)


def _false_position(a: float, b: float, fa: float, fb: float) -> float:
    """Intersección de la secante con y = 0, con ordenadas de signos opuestos."""
    # Calcular desde el extremo más cercano a la intersección. El cociente
    # queda entre 0 y 1, sin restar dos ordenadas grandes de signo contrario.
    if abs(fa) <= abs(fb):
        ratio = abs(fa) / abs(fb)
        return a + (b - a) * (ratio / (1 + ratio))
    ratio = abs(fb) / abs(fa)
    return b - (b - a) * (ratio / (1 + ratio))
