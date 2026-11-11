"""Página de derivadas e integrales."""

import sympy as sp

from core.calculus import differentiate, integrate, read_calculus_point
from desktop.core.forms import Result, ToolPage
from desktop.core.math_input import MathInput
from desktop.core.widgets import SegmentedControl


def calculus_page() -> ToolPage:
    mode = SegmentedControl("Derivada", "Integral indefinida", "Integral definida")
    mode.setAccessibleName("Operación de cálculo")
    function = MathInput("x^3 - x - 2", "Función f(x)")
    point = MathInput("", "Evaluar en x (opcional)", "number")
    lower = MathInput("0", "Límite inferior", "number")
    upper = MathInput("1", "Límite superior", "number")

    def show_fields() -> None:
        index = mode.currentIndex()
        point.setVisible(index == 0)
        lower.parentWidget().setVisible(index == 2)

    def calculate() -> Result:
        index = mode.currentIndex()
        if index == 0:
            derivative = differentiate(function.value())
            text = [f"f′(x) = {derivative.expression}"]
            latex = [rf"f'(x) = {sp.latex(derivative.expression)}"]
            if point.value().strip():
                at = read_calculus_point(point.value())
                value = derivative.at(at)
                text.append(f"f′({at}) = {value}")
                latex.append(rf"f'\left({sp.latex(at)}\right) = {sp.latex(value)}")
            return Result("\n".join(text), title="Derivada", latex=tuple(latex))
        if index == 1:
            expression = integrate(function.value())
            return Result(f"F(x) = {expression} + C", title="Antiderivada",
                          latex=(rf"F(x) = {sp.latex(expression)} + C",))
        start = read_calculus_point(lower.value())
        end = read_calculus_point(upper.value())
        expression = integrate(function.value(), (start, end))
        return Result(f"Integral de {start} a {end} = {expression}", title="Integral definida",
                      latex=(rf"\int_{{{sp.latex(start)}}}^{{{sp.latex(end)}}} f(x)\,dx = {sp.latex(expression)}",))

    page = ToolPage("∫", "Derivadas e integrales",
                    "Deriva una función, encuentra su antiderivada o intégrala entre dos límites.",
                    [function, point, (lower, upper)], "Calcular", calculate, above=(mode,))
    mode.currentIndexChanged.connect(show_fields)
    show_fields()
    return page
