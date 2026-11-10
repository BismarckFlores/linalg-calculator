"""Bisección por el punto medio de un intervalo con cambio de signo."""

from .real_function import RealFunction, RootInputError, sample_function
from .root_bracket import (
    BracketResult, BracketStep, RootCriterion, RootStop, read_root_number, solve_bracket,
)
from .scalar import NumberLike

# Compatibilidad con quienes ya importaban estos nombres desde bisección.
BisectionCriterion = RootCriterion
BisectionError = RootInputError
BisectionResult = BracketResult
BisectionStep = BracketStep
BisectionStop = RootStop
bisection_number = read_root_number
sample_bisection = sample_function


def bisect(
    function: RealFunction | str,
    a: NumberLike,
    b: NumberLike,
    tolerance: NumberLike = "0.0001",
    *,
    criterion: RootCriterion = RootCriterion.WIDTH,
    max_iterations: int = 100,
) -> BracketResult:
    """Divide [a,b] y conserva cada fila; una cota en x supone continuidad."""
    return solve_bracket(
        function, a, b, tolerance, criterion, max_iterations,
        lambda left, right, _fa, _fb: left + (right - left) / 2,
    )
