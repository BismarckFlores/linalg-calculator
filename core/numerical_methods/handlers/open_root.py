"""Validación compartida por los métodos abiertos."""

from ...scalar import NumberLike
from .real_function import RootInputError
from .root_bracket import read_root_number


def open_tolerance(tolerance: NumberLike, max_iterations: int) -> float:
    value = read_root_number(tolerance)
    if value <= 0:
        raise RootInputError("La tolerancia E debe ser mayor que cero.")
    if type(max_iterations) is not int or not 1 <= max_iterations <= 1000:
        raise RootInputError("El máximo de iteraciones debe ser un entero entre 1 y 1000.")
    return value
