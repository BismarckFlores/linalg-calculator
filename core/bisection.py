"""
Biseccion de una funcion real, con el intervalo de cada iteracion guardado.

Este calculo es aproximado: usa float, no los racionales de las matrices.
El ancho, el residuo y el cambio relativo son medidas distintas y nunca se
redondean para decidir la parada. La existencia de una raiz exige continuidad
en todo el intervalo; evaluar unos cuantos puntos no puede demostrarla.
"""

import ast
import math
import operator
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .scalar import NumberLike, to_scalar


class BisectionError(ValueError):
    """Una expresion, evaluacion o parametro no permite continuar."""


class BisectionCriterion(Enum):
    """La magnitud que se compara estrictamente con la tolerancia."""

    WIDTH = "width"
    RESIDUAL = "residual"
    RELATIVE = "relative"


class BisectionStop(Enum):
    """Por que termino el recorrido; el limite no significa convergencia."""

    ZERO = "zero"
    TOLERANCE = "tolerance"
    LIMIT = "limit"
    STAGNATION = "stagnation"


_BISECTION_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow,
}
_BISECTION_FUNCTIONS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "exp": math.exp, "ln": math.log, "log": math.log,
    "log10": math.log10, "sqrt": math.sqrt, "abs": abs,
}
_BISECTION_CONSTANTS = {"pi": math.pi, "e": math.e}


def bisection_number(value: NumberLike) -> float:
    """Lee tambien comas decimales y fracciones, usando el lector existente."""
    if isinstance(value, str):
        if len(value) > 128:
            raise BisectionError("El número escrito es demasiado largo.")
        # Fraction materializa el exponente; no tiene sentido construir millones
        # de cifras para un valor que float no puede representar.
        for part in value.lower().split("/"):
            if "e" in part:
                try:
                    exponent = int(part.split("e", 1)[1])
                except ValueError:
                    break
                if abs(exponent) > 10000:
                    raise BisectionError("El exponente excede la representación numérica disponible.")
    try:
        result = float(to_scalar(value))
    except (ValueError, TypeError, OverflowError) as problem:
        raise BisectionError(f"Se necesita un número real finito: {value!r}.") from problem
    if not math.isfinite(result):
        raise BisectionError("Los parámetros deben ser números reales finitos.")
    if result == 0 and to_scalar(value) != 0:
        raise BisectionError("El número es demasiado pequeño para representarlo (underflow).")
    return result


class RealFunction:
    """Expresion en x: un arbol aritmetico permitido, sin eval ni codigo ejecutable."""

    def __init__(self, text: str) -> None:
        self.text = text.strip()
        if not self.text or len(self.text) > 1024:
            raise BisectionError("Escribe f(x) con entre 1 y 1024 caracteres.")
        normalized = self.text.replace("^", "**").replace("−", "-").replace("×", "*")
        self._source = normalized
        try:
            self._tree = ast.parse(normalized, mode="eval").body
        except (SyntaxError, RecursionError) as problem:
            raise BisectionError("No se puede leer f(x). Usa x, paréntesis y * para multiplicar.") from problem
        if sum(1 for _ in ast.walk(self._tree)) > 160:
            raise BisectionError("La expresión es demasiado larga.")
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
                        raise BisectionError("Una constante se pierde por underflow; cambia su escala.")
                return
        elif isinstance(node, ast.Name) and node.id in {"x", *_BISECTION_CONSTANTS}:
            return
        elif isinstance(node, ast.BinOp) and type(node.op) in _BISECTION_OPERATORS:
            self._validate(node.left)
            self._validate(node.right)
            return
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            self._validate(node.operand)
            return
        elif (
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in _BISECTION_FUNCTIONS
            and len(node.args) == 1 and not node.keywords
        ):
            self._validate(node.args[0])
            return
        raise BisectionError(
            "Expresión no admitida. Usa x, números, + - * / ^, pi, e y "
            "sin, cos, tan, exp, ln, log, log10, sqrt o abs con un argumento."
        )

    def __call__(self, x: float) -> float:
        if not math.isfinite(x):
            raise BisectionError("x debe ser finito.")
        try:
            return self._evaluate(self._tree, x)
        except (ValueError, ArithmeticError, TypeError) as problem:
            raise BisectionError(
                f"No se puede evaluar f(x) en x = {x:.17g}: {problem}"
            ) from problem

    def _evaluate(self, node: ast.expr, x: float) -> float:
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            return x if node.id == "x" else _BISECTION_CONSTANTS[node.id]
        if isinstance(node, ast.UnaryOp):
            value = self._evaluate(node.operand, x)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp):
            left = self._evaluate(node.left, x)
            right = self._evaluate(node.right, x)
            if isinstance(node.op, ast.Pow) and abs(right) > 1024:
                raise ValueError("El exponente debe estar entre -1024 y 1024.")
            value = _BISECTION_OPERATORS[type(node.op)](left, right)
            underflow = (
                value == 0 and left != 0
                and (isinstance(node.op, (ast.Div, ast.Pow))
                     or isinstance(node.op, ast.Mult) and right != 0)
            )
        else:
            assert isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            value = _BISECTION_FUNCTIONS[node.func.id](self._evaluate(node.args[0], x))
            underflow = node.func.id == "exp" and value == 0
        if isinstance(value, complex) or not math.isfinite(value):
            raise ValueError("El resultado no es un número real finito (dominio u overflow).")
        if underflow:
            raise ValueError("El resultado se pierde por underflow; cambia la escala de f(x).")
        return float(value)


@dataclass(frozen=True)
class BisectionStep:
    """El intervalo antes del corte, su punto medio y las medidas sin redondear."""

    index: int
    a: float
    b: float
    c: float
    fa: float
    fb: float
    fc: float
    relative_error: float | None

    @property
    def width(self) -> float:
        return self.b - self.a

    @property
    def bound(self) -> float:
        # max conserva una cota aun si el punto medio se redondeo hacia un lado.
        return max(self.c - self.a, self.b - self.c)

    @property
    def residual(self) -> float:
        return abs(self.fc)

    @property
    def keep_left(self) -> bool:
        # No se multiplican valores: su producto podria desbordar o hacerse cero.
        return (self.fa < 0) != (self.fc < 0)


@dataclass(frozen=True)
class BisectionResult:
    """La respuesta y la traza que la produjo, tambien cuando no converge."""

    function: RealFunction
    initial_a: float
    initial_b: float
    tolerance: float
    criterion: BisectionCriterion
    steps: tuple[BisectionStep, ...]
    stop: BisectionStop
    root: float
    value: float
    a: float
    b: float

    @property
    def converged(self) -> bool:
        return self.stop in (BisectionStop.ZERO, BisectionStop.TOLERANCE)

    @property
    def bound(self) -> float:
        return max(self.root - self.a, self.b - self.root)


def bisect(
    function: RealFunction | str,
    a: NumberLike,
    b: NumberLike,
    tolerance: NumberLike = "0.0001",
    *,
    criterion: BisectionCriterion = BisectionCriterion.WIDTH,
    max_iterations: int = 100,
) -> BisectionResult:
    """Divide [a,b] y conserva cada fila; una cota en x supone continuidad."""
    if isinstance(function, str):
        function = RealFunction(function)
    a, b, tolerance = (bisection_number(v) for v in (a, b, tolerance))
    if a >= b:
        raise BisectionError("El extremo inferior a debe ser menor que b.")
    if not math.isfinite(b - a):
        raise BisectionError("El intervalo es demasiado ancho para representarlo.")
    if tolerance <= 0:
        raise BisectionError("La tolerancia E debe ser mayor que cero.")
    if type(max_iterations) is not int or not 1 <= max_iterations <= 1000:
        raise BisectionError("El máximo de iteraciones debe ser un entero entre 1 y 1000.")
    if not isinstance(criterion, BisectionCriterion):
        raise BisectionError("El criterio de parada no es válido.")
    initial_a, initial_b = a, b
    steps: list[BisectionStep] = []

    def finish(stop: BisectionStop, c: float, fc: float) -> BisectionResult:
        return BisectionResult(
            function, initial_a, initial_b, tolerance, criterion,
            tuple(steps), stop, c, fc, a, b,
        )

    fa = function(a)
    if fa == 0:
        b = a
        return finish(BisectionStop.ZERO, a, fa)
    fb = function(b)
    if fb == 0:
        a = b
        return finish(BisectionStop.ZERO, b, fb)
    if (fa < 0) == (fb < 0):
        raise BisectionError(
            "f(a) y f(b) tienen el mismo signo. Este intervalo no permite aplicar "
            "bisección; eso no demuestra que la función carezca de raíces."
        )

    previous: float | None = None
    for index in range(1, max_iterations + 1):
        c = a + (b - a) / 2
        fc = function(c)
        relative = abs((c - previous) / c) * 100 if previous is not None and c != 0 else None
        if relative is not None and not math.isfinite(relative):
            relative = None
        step = BisectionStep(index, a, b, c, fa, fb, fc, relative)
        steps.append(step)
        if fc == 0:
            a = b = c
            return finish(BisectionStop.ZERO, c, fc)
        stagnant = c == a or c == b
        measure = {
            BisectionCriterion.WIDTH: step.width,
            BisectionCriterion.RESIDUAL: step.residual,
            BisectionCriterion.RELATIVE: relative,
        }[criterion]
        # El ancho o residuo pueden satisfacer ya E aunque no quede otro float
        # intermedio. Un cambio relativo nulo por estancamiento no prueba nada.
        if measure is not None and measure < tolerance and not (
            stagnant and criterion is BisectionCriterion.RELATIVE
        ):
            return finish(BisectionStop.TOLERANCE, c, fc)
        if stagnant:
            return finish(BisectionStop.STAGNATION, c, fc)
        if index == max_iterations:
            return finish(BisectionStop.LIMIT, c, fc)
        if step.keep_left:
            b, fb = c, fc
        else:
            a, fa = c, fc
        previous = c

    raise AssertionError("El bucle siempre termina con un resultado.")


def sample_bisection(
    function: RealFunction, a: float, b: float, count: int = 401,
) -> tuple[tuple[float, float | None], ...]:
    """Muestreo para dibujar: un punto fuera del dominio deja un hueco."""
    if not 2 <= count <= 2001:
        raise BisectionError("El muestreo necesita entre 2 y 2001 puntos.")
    points = []
    for index in range(count):
        x = a + (b - a) * (index / (count - 1))
        try:
            y = function(x)
        except BisectionError:
            y = None
        points.append((x, y))
    return tuple(points)
