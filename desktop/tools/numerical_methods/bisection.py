"""Página del método de Bisección."""

from core.numerical_methods.bisection import bisect
from core.numerical_methods.handlers.root_bracket import RootCriterion

from .core.bracket_page import RootBracketPage


class BisectionPage(RootBracketPage):
    title = "Método de Bisección"
    glyph = "½"
    subtitle = "Encuentra una raíz de f(x) = 0 reduciendo un intervalo a la mitad."
    formula = "a + (b − a) / 2"
    criteria = (RootCriterion.WIDTH, RootCriterion.RESIDUAL, RootCriterion.RELATIVE)
    solve = staticmethod(bisect)
    presets = (
        ("Polinomio del Excel", "x^4 - 5x^3 + 0.5x^2 - 11x + 10", "0.6", "1", "0.0001", RootCriterion.RESIDUAL),
        ("Raíz de 2", "x^2 - 2", "1", "2", "0.0001", RootCriterion.WIDTH),
        ("Potencia décima", "x^10 - 1", "0", "1.3", "0.0001", RootCriterion.WIDTH),
        ("Fracción con raíz", "sqrt(x+1)/2 - 1", "2", "4", "0.0001", RootCriterion.WIDTH),
    )
