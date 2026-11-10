"""Lector seguro y muestreo de funciones reales de una variable."""

import ast
import math
import operator
import re
from collections.abc import Callable
from decimal import Decimal

from ...notation import explicit_products


class RootInputError(ValueError):
    """Una expresion, evaluacion o parametro no permite continuar."""


_ROOT_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow,
}


def _trig_away_from_pole(angle: float, function: Callable[[float], float], pole: float) -> float:
    if abs(math.remainder(angle, math.pi)) == pole:
        raise ValueError("La función trigonométrica no está definida en ese ángulo.")
    return function(angle)


TRIG_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": lambda angle: _trig_away_from_pole(angle, math.tan, math.pi / 2),
    "sec": lambda angle: 1 / _trig_away_from_pole(angle, math.cos, math.pi / 2),
    "csc": lambda angle: 1 / _trig_away_from_pole(angle, math.sin, 0),
    "cot": lambda angle: math.cos(angle) / _trig_away_from_pole(angle, math.sin, 0),
}
INVERSE_TRIG_NAMES = {name: f"arc{name}" for name in TRIG_FUNCTIONS}
_INVERSE_TRIG_FUNCTIONS = {
    "arcsin": math.asin, "arccos": math.acos, "arctan": math.atan,
    "arcsec": lambda value: math.acos(1 / value),
    "arccsc": lambda value: math.asin(1 / value),
    "arccot": lambda value: math.atan2(1, value),
}
_ROOT_FUNCTIONS = {
    **TRIG_FUNCTIONS, **_INVERSE_TRIG_FUNCTIONS,
    "exp": math.exp, "ln": math.log, "log": math.log,
    "log10": math.log10, "sqrt": math.sqrt, "abs": abs,
}
_ROOT_CONSTANTS = {"pi": math.pi, "e": math.e}
_TRIG_POWER = re.compile(
    rf"(?<![A-Za-z_])({'|'.join(TRIG_FUNCTIONS)})\s*\*\*\s*(\(|[+-]?\s*(?:\d+(?:\.\d*)?|\.\d+))"
)
_SUPERSCRIPT = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+")
_SUPERSCRIPT_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")


def _closing_parenthesis(text: str, opening: int) -> int | None:
    depth = 1
    for index in range(opening + 1, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def _expand_trig_powers(text: str) -> str:
    """Traduce cos^2(x) y sin^(-1)(x) a llamadas válidas para el lector."""
    pieces = []
    offset = 0
    for match in _TRIG_POWER.finditer(text):
        if match.start() < offset:
            continue
        name, power = match.groups()
        after_power = match.end()
        if power == "(":
            close = _closing_parenthesis(text, match.start(2))
            if close is None:
                continue
            power = text[after_power:close]
            after_power = close + 1
        argument_start = after_power
        while argument_start < len(text) and text[argument_start].isspace():
            argument_start += 1
        if text[argument_start:argument_start + 1] != "(":
            continue
        argument_end = _closing_parenthesis(text, argument_start)
        if argument_end is None:
            continue
        argument = _expand_trig_powers(text[argument_start + 1:argument_end])
        pieces.append(text[offset:match.start()])
        if re.fullmatch(r"-\s*1", power.strip()):
            pieces.append(f"{INVERSE_TRIG_NAMES[name]}({argument})")
        else:
            exponent = _expand_trig_powers(power)
            pieces.append(f"({name}({argument})**({exponent}))")
        offset = argument_end + 1
    pieces.append(text[offset:])
    return "".join(pieces)


class RealFunction:
    """Expresion en x: un arbol aritmetico permitido, sin eval ni codigo ejecutable."""

    def __init__(self, text: str) -> None:
        self.text = text.strip()
        if not self.text or len(self.text) > 1024:
            raise RootInputError("Escribe f(x) con entre 1 y 1024 caracteres.")
        normalized = self.text.replace("^", "**").replace("−", "-").replace("×", "*")
        normalized = _SUPERSCRIPT.sub(lambda match: "**" + match[0].translate(_SUPERSCRIPT_DIGITS), normalized)
        normalized = _expand_trig_powers(normalized)
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
            and (len(node.args) == 1 or node.func.id == "log" and len(node.args) == 2)
            and not node.keywords
        ):
            for argument in node.args:
                self._validate(argument)
            return
        raise RootInputError(
            "Expresión no admitida. Usa x, números, + - * / ^, pi, e y "
            "sin, cos, tan, sec, csc, cot, sus inversas (arcsin, etc.), "
            "exp, ln, log, log10, sqrt o abs con un argumento, "
            "o log(base, argumento) para indicar la base."
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
            name = node.func.id
            arguments = [self._evaluate(argument, x) for argument in node.args]
            if name == "log" and len(arguments) == 2:
                base, argument = arguments
                value = math.log(argument, base)
            else:
                value = _ROOT_FUNCTIONS[name](arguments[0])
            underflow = name == "exp" and value == 0
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
