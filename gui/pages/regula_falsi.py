"""Configuración y ejemplos de la pantalla de Regula Falsi."""

from core.regula_falsi import regula_falsi
from core.root_bracket import RootCriterion

from .root_bracket import RootBracketPage


class RegulaFalsiPage(RootBracketPage):
    """Usa la secante para estimar c y conserva la misma pantalla de intervalos."""

    _glyph = "RF"
    _title = "Regula Falsi"
    _subtitle = "Aproxima una raíz por el cruce de la secante con el eje x."
    _initial_inputs = ("x^3 - 4.23603x^2 - 2.73620x - 13.09037", "4.95", "5.5", "0.01")
    _example_data = {
        "Ejercicio de la guía": (*_initial_inputs, "Error relativo (%)"),
        "Raíz de 2": ("x^2 - 2", "1", "2", "0.0001", "Residuo |f(c)|"),
        "Potencia décima": ("x^10 - 1", "0", "1.3", "0.0001", "Residuo |f(c)|"),
    }
    _criteria = {
        "Error relativo (%)": RootCriterion.RELATIVE,
        "Residuo |f(c)|": RootCriterion.RESIDUAL,
    }
    _criterion_help = (
        "c es el cruce de la secante con el eje x. Se conserva el intervalo con cambio de signo.\n"
        "Relativo: |(c − c anterior)/c| × 100 < E. En este criterio, 1 significa 1 %.\n"
        "Residuo: |f(c)| < E. Un cambio relativo pequeño puede ocurrir aunque el residuo siga siendo grande."
    )
    _step_caption = "cruce de la secante y cambio de signo"
    _estimate_formula = "b − f(b)(a − b) / (f(a) − f(b))"
    _solve = staticmethod(regula_falsi)
