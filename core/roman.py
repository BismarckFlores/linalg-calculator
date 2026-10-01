"""
Los numeros romanos, y la aritmetica que el curso pide con ellos.

Un numero romano es una suma de simbolos escritos de mayor a menor, con seis
parejas en las que un simbolo menor delante de uno mayor significa una resta:
IV, IX, XL, XC, CD y CM. Asi, XIV es X + IV, que es 10 + 4.

Los romanos no escribieron el cero ni los numeros negativos, ni tuvieron simbolo
por encima de M, asi que solo se puede escribir del 1 al 3999. Lo que quede
fuera no es un numero que exista, y esto lo dice en vez de inventarlo.

Sumar y restar se hace sobre los valores: se leen los dos numeros, se opera y la
respuesta se vuelve a escribir en romano. Multiplicar funciona igual, y ademas
conserva la suma repetida con que se ensena (X * V es X + X + X + X + X), un
sumando por cada unidad del numero de la derecha, para quien quiera verla.

Como el resto de core, esto no le dice nada a nadie. Devuelve el procedimiento y
lanza errores, y la ventana decide el castellano.
"""

from dataclasses import dataclass

# Cada pieza con que se construye un numero romano, de mayor a menor, con las
# seis parejas de resta incluidas. Leer y escribir recorren esta lista en orden,
# que es lo que hace que solo produzcan la escritura canonica.
PIECES = (
    ("M", 1000), ("CM", 900), ("D", 500), ("CD", 400),
    ("C", 100), ("XC", 90), ("L", 50), ("XL", 40),
    ("X", 10), ("IX", 9), ("V", 5), ("IV", 4), ("I", 1),
)

# Los siete simbolos, que es lo que significa un solo digito en la multiplicacion.
SYMBOLS = ("I", "V", "X", "L", "C", "D", "M")

# MMMCMXCIX. No hay simbolo para 5000, asi que nada mayor se puede escribir.
LARGEST = 3999

class RomanError(ValueError):
    """Algo no es un numero romano, o no se puede escribir como tal."""

class EmptyRoman(RomanError):
    """No hay nada que leer."""

class BadLetter(RomanError):
    """Un caracter que no es un simbolo romano. letter es ese caracter."""

    def __init__(self, letter: str) -> None:
        super().__init__(f"'{letter}' is not a Roman symbol.")
        self.letter = letter

class NotCanonical(RomanError):
    """
    Letras romanas que suman, pero no son como se escribe el numero.

    IIII son cuatro unos y VV son dos cincos; las dos dicen un numero que tiene
    su propio numeral, y canonical es ese numeral.
    """

    def __init__(self, numeral: str, canonical: str) -> None:
        super().__init__(f"'{numeral}' is written '{canonical}'.")
        self.numeral = numeral
        self.canonical = canonical

class BadOrder(RomanError):
    """
    Letras romanas en un orden que no escribe nada: IC, XM, VX.

    Las seis parejas de resta son el unico caso en que un simbolo menor va antes
    de uno mayor, y cualquier otro orden nunca fue un numero romano.
    """

    def __init__(self, numeral: str) -> None:
        super().__init__(f"'{numeral}' is not how a numeral is put together.")
        self.numeral = numeral

class OutOfRange(RomanError):
    """Un valor sin numero romano: cero, negativo, o mayor que LARGEST."""

    def __init__(self, value: int) -> None:
        super().__init__(f"{value} cannot be written in Roman numerals.")
        self.value = value

@dataclass(frozen=True)
class Piece:
    """Una pieza de un numero romano tal como se lee: IX vale 9, y resta."""

    text: str
    value: int

    @property
    def subtractive(self) -> bool:
        """Si esta pieza es una de las seis parejas, IX en vez de X."""
        return len(self.text) == 2

@dataclass(frozen=True)
class Taken:
    """Una pieza tomada al escribir un numero: 1994 toma M, y quedan 994."""

    text: str
    value: int
    before: int
    after: int

@dataclass(frozen=True)
class Written:
    """Un numero escrito en romano, y las piezas que se tomaron, en orden."""

    value: int
    numeral: str
    taken: tuple[Taken, ...]

@dataclass(frozen=True)
class Numeral:
    """Un numero romano, su valor, y las piezas en que se leyo."""

    text: str
    value: int
    pieces: tuple[Piece, ...]

@dataclass(frozen=True)
class Operation:
    """
    Una operacion hecha con dos numeros romanos, con todo lo que hizo falta.

    terms es la suma repetida de una multiplicacion, un sumando por cada vez que
    se suma el numero de la izquierda; una suma o una resta no tiene ninguno.
    numeral es la respuesta escrita en romano, o una cadena vacia cuando la
    respuesta no tiene numero romano, que es justo lo que significa un resultado
    cero o negativo.
    """

    left: Numeral
    right: Numeral
    sign: str
    value: int
    numeral: str
    terms: tuple[str, ...] = ()

    @property
    def writable(self) -> bool:
        """Si la respuesta es un numero que los romanos podian escribir."""
        return bool(self.numeral)

def to_value(text: str) -> int:
    """
    Lee un numero romano como la suma que representan sus simbolos. XIV es 10 + 4.

    Solo se acepta la escritura canonica: el valor se vuelve a escribir y se
    compara con lo leido, asi que IIII se rechaza a favor de IV, y IC por ser un
    orden que nunca escribio nada.
    """
    return read(text).value

def to_roman(value: int) -> str:
    """Solo el numero romano, para quien no necesita el procedimiento."""
    return write(value).numeral

def write(value: int) -> Written:
    """
    Escribe un numero en romano tomando la pieza mas grande que quepa, una y otra
    vez: 1994 toma M, luego CM, luego XC y luego IV.

    De cada pieza tomada se guarda lo que quedaba antes y lo que queda despues,
    que es la misma resta que se hace en papel y todo el motivo de que el
    resultado sea el que es.
    """
    if not 1 <= value <= LARGEST:
        raise OutOfRange(value)

    numeral = ""
    taken: list[Taken] = []
    left = value
    for text, amount in PIECES:
        while left >= amount:
            taken.append(Taken(text, amount, left, left - amount))
            numeral += text
            left -= amount
    return Written(value, numeral, tuple(taken))

def read(text: str) -> Numeral:
    """
    Un numero romano con su valor y las piezas en que se leyo, para mostrar el
    procedimiento. Lanza EmptyRoman, BadLetter, BadOrder o NotCanonical.
    """
    numeral = "".join(text.split()).upper()
    if not numeral:
        raise EmptyRoman("There is no numeral to read.")
    for letter in numeral:
        if letter not in SYMBOLS:
            raise BadLetter(letter)

    pieces: list[Piece] = []
    value = 0
    position = 0
    for piece, amount in PIECES:
        while numeral[position:position + len(piece)] == piece:
            pieces.append(Piece(piece, amount))
            value += amount
            position += len(piece)

    # Recorrer las piezas en orden solo escribe la forma canonica. Las letras que
    # sobran no encajaron en ninguna parte, asi que el orden esta mal; las letras
    # que encajaron pero se reescriben distinto son una escritura que nadie uso.
    if position != len(numeral):
        raise BadOrder(numeral)
    if to_roman(value) != numeral:
        raise NotCanonical(numeral, to_roman(value))

    return Numeral(numeral, value, tuple(pieces))

def sum_of(left: str, right: str) -> Operation:
    """XIV + IX: se leen los dos, se suman los valores y el total se escribe en romano."""
    return _operate(read(left), read(right), "+")

def difference_of(left: str, right: str) -> Operation:
    """
    XIV - IX: lo mismo, restando un valor del otro.

    Una diferencia de cero o menos no tiene numero romano, y la operacion lo dice
    en vez de lanzar un error: que los romanos no escribieran el cero es la
    respuesta.
    """
    return _operate(read(left), read(right), "-")

def product_of(left: str, right: str) -> Operation:
    """
    Un numero romano por otro, conservando la suma repetida que representa:
    X * V es X + X + X + X + X, que es L.

    terms lleva una copia del numero de la izquierda por cada unidad del de la
    derecha, asi que es la suma misma y no un dibujo de ella. Un numero grande a
    la derecha hace una lista larga (X * MMM son tres mil sumandos) y es quien
    llama quien decide cuanto vale la pena mostrar.
    """
    first, second = read(left), read(right)
    product = _operate(first, second, "*")
    return Operation(
        first, second, "*", product.value, product.numeral,
        tuple(first.text for _ in range(second.value)),
    )

def _operate(left: Numeral, right: Numeral, sign: str) -> Operation:
    value = {"+": left.value + right.value,
             "-": left.value - right.value,
             "*": left.value * right.value}[sign]
    numeral = to_roman(value) if 1 <= value <= LARGEST else ""
    return Operation(left, right, sign, value, numeral)
