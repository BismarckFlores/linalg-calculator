"""Motor matemático de la calculadora."""

from sys import modules as _modules

from .linear_algebra import determinant, echelon, inverse, lu, systems, vectors
from .linear_algebra.handlers import elimination, equations, matrix, parametric, steps, verification, worksheet
from .number_systems import bases, roman
from .numerical_methods import bisection, regula_falsi
from .numerical_methods.handlers import real_function, root_bracket

# Las rutas anteriores resuelven al mismo módulo que su ruta por área.
for _module in (
    bases, bisection, determinant, echelon, elimination, equations, inverse, lu,
    matrix, parametric, real_function, regula_falsi, roman, root_bracket, steps,
    systems, vectors, verification, worksheet,
):
    _modules[f"{__name__}.{_module.__name__.rsplit('.', 1)[-1]}"] = _module
del _module, _modules
