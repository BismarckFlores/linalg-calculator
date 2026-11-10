"""Lector seguro y muestreo de funciones reales de una variable."""

import ast
import math
import operator
from decimal import Decimal

from .notation import explicit_products


class RootInputError(ValueError):
    """Una expresion, evaluacion o parametro no permite continuar."""


_ROOT_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow,
}
_ROOT_FUNCTIONS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "exp": math.exp, "ln": math.log, "log": math.log,
    "log10": math.log10, "sqrt": math.sqrt, "abs": abs,
}
_ROOT_CONSTANTS = {"pi": math.pi, "e": math.e}


class RealFunction:
    """Expresion en x: un arbol aritmetico permitido, sin eval ni codigo ejecutable."""

    def __init__(self, text: str) -> None:
        self.text = text.strip()
        if not self.text or len(self.text) > 1024:
            raise RootInputError("Escribe f(x) con entre 1 y 1024 caracteres.")
        normalized = self.text.replace("^", "**").replace("−", "-").replace("×", "*")
        normalized = explicit_products(normalized, _ROOT_FUNCTIONS)
        self._source = normalized
        try:
            self._tree = ast.parse(normalized, mode="eval").body
        except (SyntaxError, RecursionError) as problem:
            raise RootInputError("No se puede leer f(x). Prueba con 5x^3, 2(x+1) o sin(x).") from problem
        if sum(1 for _ in ast.walk(self._tree)) > 160:
            raise RootInputError("La expresión es demasiado larga.")
        self._validate(self._tree)

    def _validate(self, node: ast.expr) -> None:
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            try:
                valid = math.isfinite(float(node.value))
            except OverflowError:
                valid = False
            if valid:
                if type(node.value) is float and node.value == 0:
                    literal = ast.get_source_segment(self._source, node)
                    if literal is not None and Decimal(literal.replace("_", "")) != 0:
                        raise RootInputError("Una constante se pierde por underflow; cambia su escala.")
                return
        elif isinstance(node, ast.Name) and node.id in {"x", *_ROOT_CONSTANTS}:
            return
        elif isinstance(node, ast.BinOp) and type(node.op) in _ROOT_OPERATORS:
            self._validate(node.left)
            self._validate(node.right)
            return
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            self._validate(node.operand)
            return
        elif (
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in _ROOT_FUNCTIONS
            and len(node.args) == 1 and not node.keywords
        ):
            self._validate(node.args[0])
            return
        raise RootInputError(
            "Expresión no admitida. Usa x, números, + - * / ^, pi, e y "
            "sin, cos, tan, exp, ln, log, log10, sqrt o abs con un argumento."
        )

    def __call__(self, x: float) -> float:
        if not math.isfinite(x):
            raise RootInputError("x debe ser finito.")
        try:
            return self._evaluate(self._tree, x)
        except (ValueError, ArithmeticError, TypeError) as problem:
            raise RootInputError(
                f"No se puede evaluar f(x) en x = {x:.17g}: {problem}"
            ) from problem

    def _evaluate(self, node: ast.expr, x: float) -> float:
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            return x if node.id == "x" else _ROOT_CONSTANTS[node.id]
        if isinstance(node, ast.UnaryOp):
            value = self._evaluate(node.operand, x)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp):
            left = self._evaluate(node.left, x)
            right = self._evaluate(node.right, x)
            if isinstance(node.op, ast.Pow) and abs(right) > 1024:
                raise ValueError("El exponente debe estar entre -1024 y 1024.")
            value = _ROOT_OPERATORS[type(node.op)](left, right)
            underflow = (
                value == 0 and left != 0
                and (isinstance(node.op, (ast.Div, ast.Pow))
                     or isinstance(node.op, ast.Mult) and right != 0)
            )
        else:
            assert isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            value = _ROOT_FUNCTIONS[node.func.id](self._evaluate(node.args[0], x))
            underflow = node.func.id == "exp" and value == 0
        if isinstance(value, complex) or not math.isfinite(value):
            raise ValueError("El resultado no es un número real finito (dominio u overflow).")
        if underflow:
            raise ValueError("El resultado se pierde por underflow; cambia la escala de f(x).")
        return float(value)


def sample_function(
    function: RealFunction, a: float, b: float, count: int = 401,
) -> tuple[tuple[float, float | None], ...]:
    """Muestreo para dibujar: un punto fuera del dominio deja un hueco."""
    if not 2 <= count <= 2001:
        raise RootInputError("El muestreo necesita entre 2 y 2001 puntos.")
    points = []
    for index in range(count):
        x = a + (b - a) * (index / (count - 1))
        try:
            y = function(x)
        except RootInputError:
            y = None
        points.append((x, y))
    return tuple(points)
