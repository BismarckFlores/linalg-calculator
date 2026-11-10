"""Configuración y ejemplos de la pantalla de Bisección."""

from core.bisection import bisect
from core.root_bracket import RootCriterion

from ..root_plot import RootPlot
from .root_bracket import RootBracketPage

BisectionPlot = RootPlot


BISECTION_CRITERIA = {
    "Ancho del intervalo": RootCriterion.WIDTH,
    "Residuo |f(c)|": RootCriterion.RESIDUAL,
    "Error relativo (%)": RootCriterion.RELATIVE,
}
BISECTION_POLYNOMIAL = "x^4 - 5x^3 + 0.5x^2 - 11x + 10"
BISECTION_EXAMPLES = {
    "Polinomio del Excel": (BISECTION_POLYNOMIAL, "0.6", "1", "0.0001", "Residuo |f(c)|"),
    "Raíz de 2": ("x^2 - 2", "1", "2", "0.0001", "Ancho del intervalo"),
    "Potencia décima": ("x^10 - 1", "0", "1.3", "0.0001", "Ancho del intervalo"),
}



class BisectionPage(RootBracketPage):
    """Bisección con estimación por punto medio."""

    _glyph = "½"
    _title = "Método de Bisección"
    _subtitle = "Encuentra una raíz de f(x) = 0 reduciendo un intervalo a la mitad."
    _initial_inputs = (BISECTION_POLYNOMIAL, "0.6", "1", "0.0001")
    _example_data = BISECTION_EXAMPLES
    _criteria = BISECTION_CRITERIA
    _criterion_help = (
        "Ancho: b − a < E · Residuo: |f(c)| < E · Relativo: |(c − c anterior)/c| × 100 < E.\n"
        "En el criterio relativo, E se escribe en porcentaje: 1 significa 1 %."
    )
    _step_caption = "punto medio y cambio de signo"
    _estimate_formula = "(a + b) / 2"
    _solve = staticmethod(bisect)
