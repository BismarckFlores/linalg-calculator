"""
Numeros enteros escritos en cualquier base del 2 al 36, y el procedimiento que
los mueve de una a otra.

Dos sentidos. Hacia otra base, por divisiones sucesivas: cada residuo es una
cifra, y las cifras se leen de la ultima division a la primera. De vuelta a
decimal, por la combinacion lineal que representa el numero: cada cifra por la
base elevada a su posicion, contando desde 0 por la derecha.

Un numero negativo mantiene el signo aparte de las cifras, como se escribe a
mano en cualquier base: -43 es -101011 en base 2 y -2B en base 16. Las cifras
son las del valor absoluto, y el menos multiplica a todo. El signo nunca es una
cifra, asi que esto funciona igual en todas las bases.

No se toma nada prestado de Python en ninguno de los dos sentidos: ni
int(texto, base), ni bin, oct o hex. Lo que pide la tarea es el procedimiento,
asi que el procedimiento es lo que se ejecuta.

Como el resto de core, esto no le dice nada a nadie. Devuelve los pasos y lanza
errores, y la ventana decide el castellano.
"""

from dataclasses import dataclass

# Los simbolos con que se escribe una cifra: las diez cifras y luego el alfabeto.
# Un simbolo por cifra es lo que hace legible un numero, asi que las bases
# terminan donde se acaba el alfabeto.
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWEST_BASE = 2
HIGHEST_BASE = len(DIGITS)

class NumeralError(ValueError):
    """El texto no es un numero de la base que se indico."""

class EmptyNumeral(NumeralError):
    """No hay nada que leer."""

class BadDigit(NumeralError):
    """Un caracter que no es cifra de la base. digit es ese caracter."""

    def __init__(self, digit: str, base: int) -> None:
        super().__init__(f"'{digit}' is not a digit in base {base}.")
        self.digit = digit
        self.base = base

@dataclass(frozen=True)
class Division:
    """Una division del procedimiento: dividendo = base * cociente + residuo."""

    dividend: int
    quotient: int
    remainder: int

@dataclass(frozen=True)
class ToBase:
    """
    Un numero entero escrito en otra base, y las divisiones que lo escribieron.

    value conserva su signo. Las divisiones son las de su valor absoluto, y
    numeral son sus cifras, con un menos delante cuando el numero es negativo.
    """

    value: int
    base: int
    divisions: tuple[Division, ...]
    numeral: str

    @property
    def negative(self) -> bool:
        return self.value < 0

@dataclass(frozen=True)
class Term:
    """Un termino de la combinacion: cifra * base ** posicion."""

    digit: str
    value: int
    position: int
    power: int
    amount: int

@dataclass(frozen=True)
class FromBase:
    """
    Un numero leido de vuelta como la combinacion de potencias de su base.

    Los terminos son solo los de las cifras. Cuando el numero lleva un menos
    delante, negative es verdadero y value es menos la suma de los terminos.
    """

    numeral: str
    base: int
    terms: tuple[Term, ...]
    value: int
    negative: bool = False

    @property
    def magnitude(self) -> int:
        """Lo que suman las cifras, antes de aplicar el signo."""
        return sum(term.amount for term in self.terms)

def digit_value(character: str, base: int) -> int:
    """Lo que vale una cifra: 7 vale 7, B vale 11. Lanza BadDigit si no es cifra."""
    value = DIGITS.find(character.upper())
    if value < 0 or value >= base:
        raise BadDigit(character, base)
    return value

def to_base(value: int, base: int) -> ToBase:
    """
    Escribe un numero entero en otra base dividiendolo una y otra vez.

    n = b*q1 + r1, luego q1 = b*q2 + r2, y asi hasta que un cociente es 0.
    Cada residuo es menor que la base, asi que es una sola cifra, y el ultimo
    que se obtiene es la cifra de mas peso: n = r_k*b^k + ... + r2*b + r1.

    Un numero negativo divide su valor absoluto y vuelve a poner el menos
    delante de las cifras: -n en base b es -(n en base b).
    """
    _check(base)

    divisions: list[Division] = []
    current = -value if value < 0 else value
    while True:
        quotient, remainder = current // base, current % base
        divisions.append(Division(current, quotient, remainder))
        current = quotient
        if current == 0:
            break

    digits = "".join(DIGITS[step.remainder] for step in reversed(divisions))
    return ToBase(value, base, tuple(divisions), ("-" if value < 0 else "") + digits)

def from_base(text: str, base: int) -> FromBase:
    """
    Lee un numero como la combinacion lineal de potencias de su base.

    d_k ... d_1 d_0 = d_k*b^k + ... + d_1*b^1 + d_0*b^0. Los espacios se
    ignoran, para poder escribir un binario largo por grupos, y las letras
    valen en mayuscula o en minuscula.

    Un menos al principio hace negativo el numero: las cifras que le siguen se
    leen igual y la suma cambia de signo. Un mas al principio se acepta y no
    cambia nada. Menos cero es cero, y se escribe sin signo.
    """
    _check(base)
    numeral = "".join(text.split()).upper()
    negative = numeral.startswith("-")
    if numeral[:1] in ("-", "+"):
        numeral = numeral[1:]
    if not numeral:
        raise EmptyNumeral("There is no numeral to read.")

    top = len(numeral) - 1
    terms: list[Term] = []
    for index, character in enumerate(numeral):
        value = digit_value(character, base)
        position = top - index
        power = base**position
        terms.append(Term(character, value, position, power, value * power))

    total = sum(term.amount for term in terms)
    negative = negative and total != 0
    return FromBase(
        ("-" if negative else "") + numeral,
        base,
        tuple(terms),
        -total if negative else total,
        negative,
    )

def _check(base: int) -> None:
    if not LOWEST_BASE <= base <= HIGHEST_BASE:
        raise ValueError(f"Base {base} is not between {LOWEST_BASE} and {HIGHEST_BASE}.")
