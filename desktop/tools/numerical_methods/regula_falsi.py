"""Página del método de Regula Falsi."""

from core.numerical_methods.regula_falsi import regula_falsi
from core.numerical_methods.handlers.root_bracket import RootCriterion

from .core.bracket_page import RootBracketPage


class RegulaFalsiPage(RootBracketPage):
    title = "Regula Falsi"
    glyph = "RF"
    subtitle = "Aproxima una raíz por el cruce de la secante con el eje x."
    formula = "b − f(b)(a − b) / (f(a) − f(b))"
    criteria = (RootCriterion.RELATIVE, RootCriterion.RESIDUAL)
    solve = staticmethod(regula_falsi)
    presets = (
        ("Ejercicio de la guía", "x^3 - 4.23603x^2 - 2.73620x - 13.09037",
         "4.95", "5.5", "0.01", RootCriterion.RELATIVE),
        ("Raíz de 2", "x^2 - 2", "1", "2", "0.0001", RootCriterion.RESIDUAL),
        ("Potencia décima", "x^10 - 1", "0", "1.3", "0.0001", RootCriterion.RESIDUAL),
    )
