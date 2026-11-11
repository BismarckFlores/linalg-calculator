"""Derivación e integración simbólicas de funciones reales en x."""

import ast
import operator
from dataclasses import dataclass

import sympy as sp
from sympy.calculus.util import continuous_domain

from .numerical_methods.handlers.real_function import RealFunction, RootInputError


X = sp.Symbol("x", real=True)
_NAMES = {"x": X, "pi": sp.pi, "e": sp.E}
_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
}
_FUNCTIONS = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "sec": sp.sec, "csc": sp.csc, "cot": sp.cot,
    "arcsin": sp.asin, "arccos": sp.acos, "arctan": sp.atan,
    "arcsec": sp.asec, "arccsc": sp.acsc,
    "arccot": lambda value: sp.pi / 2 - sp.atan(value),
    "exp": sp.exp, "ln": sp.log, "log": lambda value, base=sp.E: sp.log(value, base),
    "log10": lambda value: sp.log(value, 10), "sqrt": sp.sqrt, "abs": sp.Abs,
}


def _require_real(value: sp.Expr, message: str) -> sp.Expr:
    if value.is_real is not True or value.is_finite is not True:
        raise RootInputError(message)
    return value


def _translate(
    function: RealFunction, node: ast.expr, domain_terms: list[sp.Expr],
) -> sp.Expr:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int):
            return sp.Integer(node.value)
        literal = ast.get_source_segment(function._source, node)
        return sp.Rational(literal.replace("_", ""))
    if isinstance(node, ast.Name):
        return _NAMES[node.id]
    if isinstance(node, ast.UnaryOp):
        value = _translate(function, node.operand, domain_terms)
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.BinOp):
        left = _translate(function, node.left, domain_terms)
        right = _translate(function, node.right, domain_terms)
        if isinstance(node.op, ast.Pow) and right.is_number and abs(right) > 1024:
            raise RootInputError("El exponente debe estar entre -1024 y 1024.")
        if isinstance(node.op, ast.Div):
            domain_terms.append(1 / right)
        result = _OPERATORS[type(node.op)](left, right)
        if isinstance(node.op, ast.Pow):
            domain_terms.append(result)
        return result
    arguments = [_translate(function, argument, domain_terms) for argument in node.args]
    if node.func.id == "log" and len(arguments) == 2:
        arguments.reverse()
    result = _FUNCTIONS[node.func.id](*arguments)
    domain_terms.append(result)
    return result


def _expression(function: RealFunction, domain_terms: list[sp.Expr] | None = None) -> sp.Expr:
    terms = domain_terms if domain_terms is not None else []
    expression = _translate(function, function._tree, terms)
    if any(term.has(sp.nan, sp.zoo, sp.oo, -sp.oo) or term.is_real is False
           for term in (expression, *terms)):
        raise RootInputError("La expresión debe representar una función real.")
    return expression


def read_calculus_point(text: str) -> sp.Expr:
    """Lee un punto o límite exacto, por ejemplo 1/3 o pi/2."""
    text = text.strip().replace(",", ".")
    value = _expression(RealFunction(text))
    if value.free_symbols:
        raise RootInputError("Escribe un número sin la variable x.")
    return _require_real(value, "El valor debe ser real y finito.")


@dataclass(frozen=True)
class Derivative:
    function: RealFunction
    original: sp.Expr
    expression: sp.Expr

    def at(self, point: sp.Expr) -> sp.Expr:
        """Evalúa la derivada dentro del dominio real de la función original."""
        _require_real(point, "El punto debe ser real y finito.")
        self.function(float(point))
        value = self.expression.subs(X, point)
        message = "La derivada no está definida en ese punto."
        if any(term.args[0].subs(X, point).is_zero for term in self.expression.atoms(sp.sign)):
            quotient = (self.original - self.original.subs(X, point)) / (X - point)
            left = sp.limit(quotient, X, point, dir="-")
            right = sp.limit(quotient, X, point, dir="+")
            if left != right:
                raise RootInputError(message)
            value = right
        return _require_real(value, message)

    def __call__(self, x: float) -> float:
        return float(self.at(sp.Float(x)))


def differentiate(function: RealFunction | str) -> Derivative:
    """Obtiene una expresión para f′(x) que también se puede evaluar."""
    function = RealFunction(function) if isinstance(function, str) else function
    original = _expression(function)
    expression = sp.diff(original, X)
    if expression.has(sp.I) and expression.is_real is not True:
        raise RootInputError("No se encontró una expresión real para la derivada.")
    return Derivative(function, original, expression)


def integrate(function: str, bounds: tuple[sp.Expr, sp.Expr] | None = None) -> sp.Expr:
    """Calcula una antiderivada o una integral definida en un intervalo continuo."""
    original = RealFunction(function)
    terms: list[sp.Expr] = []
    expression = _expression(original, terms)
    if bounds is None:
        result = sp.integrate(expression, X)
        # En el dominio real, las primitivas de 1/u contienen ln|u|.
        result = result.replace(
            lambda term: term.func == sp.log and term.args[0].is_real is True,
            lambda term: sp.log(sp.Abs(term.args[0])),
        )
    else:
        start, end = bounds
        for point in bounds:
            _require_real(point, "Los límites deben ser reales y finitos.")
            original(float(point))
        if start == end:
            return sp.S.Zero
        interval = sp.Interval(min(start, end), max(start, end))
        try:
            continuous = all(continuous_domain(term, X, interval) == interval
                             for term in dict.fromkeys([*terms, expression]))
        except NotImplementedError:
            raise RootInputError("No se pudo verificar el dominio en el intervalo.") from None
        if not continuous:
            raise RootInputError("La función debe ser real y continua en todo el intervalo.")
        result = sp.integrate(expression, (X, start, end))
        if not result.has(sp.Integral):
            _require_real(result, "La integral no produjo un valor real finito.")
    if result.has(sp.Integral):
        raise RootInputError("No se encontró un resultado simbólico para esta integral.")
    if result.has(sp.I) and result.is_real is not True:
        raise RootInputError("No se encontró una expresión real para esta integral.")
    return result
