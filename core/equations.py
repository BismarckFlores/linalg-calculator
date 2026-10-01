"""
Leer una ecuacion tal como se escribe: 2x + 3y - z = 5.

Lo que sale es lo mismo que guarda una fila de la matriz aumentada, asi que el
resto del proyecto nunca se entera de que hubo un texto de por medio. Se leen
los dos lados y despues se ordenan en uno: las incognitas pasan a la izquierda,
las constantes a la derecha, y una incognita que aparece en los dos lados se
resta en vez de contarse dos veces.

Las incognitas son las que resulten mencionar las ecuaciones. Nadie las declara
de antemano, y ese es el sentido: la persona escribe el sistema y el numero de
columnas sale de ahi.

Como el resto de core, esto no le dice nada a nadie. Lanza errores, y
ui/prompts.py decide el castellano.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from .matrix import Matrix
from .scalar import Scalar, to_scalar

# Un termino: un signo opcional, un coeficiente opcional escrito tal cual o entre
# parentesis, un * opcional y un nombre opcional. Todo es opcional porque
# x, 2, -3y y (1/2)z son todos terminos; una coincidencia que no tiene ni
# numero ni nombre es la unica combinacion que no significa nada.
_TERM = re.compile(
    r"(?P<sign>[+-])?"
    r"(?:\((?P<grouped>[^()]*)\)|(?P<number>\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?))?"
    r"\*?"
    r"(?P<name>[a-z_][a-z0-9_]*)?"
)

# Un nombre partido en sus letras y sus digitos finales, para poder ordenarlo.
_NAME = re.compile(r"([a-z_]+)(\d*)")

class EquationError(ValueError):
    """Hay algo en el texto de una ecuacion que no se puede leer."""

class MissingEquals(EquationError):
    """El texto no tiene exactamente un =."""

class UnreadableTerm(EquationError):
    """Un trozo de un lado no es un termino. text es el trozo en cuestion."""

    def __init__(self, text: str) -> None:
        super().__init__(f"'{text}' is not a term.")
        self.text = text

@dataclass(frozen=True)
class Equation:
    """Una ecuacion ya ordenada: terminos = constante, sin nada suelto a la derecha."""

    terms: dict[str, Scalar]
    constant: Scalar
    text: str

def parse_equation(text: str) -> Equation:
    """
    Lee una ecuacion escrita.

    Lo que esta a la derecha pasa a la izquierda y lo que es constante pasa a
    la derecha, de modo que 2x = 3y + 1 y 2x - 3y = 1 salen identicas. Un
    coeficiente que se cancela a cero se descarta: despues de x + y = x + 2 el
    sistema no menciona x, y fingir lo contrario seria inventarse una columna.
    """
    if text.count("=") != 1:
        raise MissingEquals("An equation needs exactly one '='.")

    left_text, right_text = text.split("=")
    left_terms, left_constant = _parse_side(left_text)
    right_terms, right_constant = _parse_side(right_text)

    terms = dict(left_terms)
    for name, coefficient in right_terms.items():
        moved = terms.get(name, Scalar(0)) - coefficient
        if moved == 0:
            terms.pop(name, None)
        else:
            terms[name] = moved

    return Equation(terms, right_constant - left_constant, text.strip())

def unknown_names(equations: Sequence[Equation]) -> list[str]:
    """
    Todas las incognitas que mencionan las ecuaciones, en el orden en que van a
    ser columnas.

    Por orden alfabetico, con los digitos finales comparados como numeros para
    que x2 vaya antes que x10. Alfabetico y no por orden de aparicion, porque
    2y + 3x = 5 tiene que seguir poniendo x en la primera columna: ahi es donde
    la busca quien lo lee.
    """
    found = {name for equation in equations for name in equation.terms}
    return sorted(found, key=_sort_key)

def to_augmented(equations: Sequence[Equation], names: Sequence[str]) -> Matrix:
    """
    Coloca las ecuaciones como [A | b] frente a esos nombres.

    Una incognita que una ecuacion no menciona es un cero en esa fila, que es
    lo que permite escribir x + z = 1 e y = 2 y obtener aun asi un sistema de
    tres columnas.
    """
    return Matrix([
        [equation.terms.get(name, Scalar(0)) for name in names] + [equation.constant]
        for equation in equations
    ])

def _parse_side(text: str) -> tuple[dict[str, Scalar], Scalar]:
    """
    Lee un lado y lo separa en sus coeficientes y su constante.

    Primero se quitan los espacios, para que 2 x y 2x sean lo mismo, y se pasa
    todo a minusculas, para que X y x sean la misma incognita. Despues se van
    tomando terminos de izquierda a derecha hasta agotar el lado; lo que el
    patron no consigue leer se informa junto al trozo que lo detuvo.
    """
    packed = re.sub(r"\s+", "", text).lower()
    terms: dict[str, Scalar] = {}
    constant = Scalar(0)
    position = 0

    while position < len(packed):
        match = _TERM.match(packed, position)
        if match is None or match.end() == position:
            raise UnreadableTerm(packed[position:])

        sign = -1 if match["sign"] == "-" else 1
        written = match["grouped"] if match["grouped"] is not None else match["number"]
        name = match["name"]

        if written is None and name is None:
            # Un signo suelto. Lo que esta mal es lo que venga detras de el.
            raise UnreadableTerm(packed[match.end():] or packed[position:])

        try:
            # Un coeficiente escrito lo lee to_scalar, asi que 1/3, 2.5 y 2,5
            # significan aqui exactamente lo mismo que en todo lo demas.
            magnitude = to_scalar(written) if written is not None else Scalar(1)
        except (TypeError, ValueError):
            raise UnreadableTerm(match.group(0)) from None

        coefficient = sign * magnitude
        if name is None:
            constant += coefficient
        else:
            terms[name] = terms.get(name, Scalar(0)) + coefficient

        position = match.end()

    return {name: value for name, value in terms.items() if value != 0}, constant

def _sort_key(name: str) -> tuple[str, int]:
    """Primero las letras, y luego los digitos finales como numero: x, x1, x2, x10, y."""
    match = _NAME.fullmatch(name)
    if match is None:
        return (name, 0)
    head, digits = match.groups()
    return (head, int(digits) if digits else 0)
