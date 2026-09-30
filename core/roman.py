"""
Roman numerals, and the arithmetic the course asks for on them.

A Roman numeral is a sum of symbols written from the largest to the smallest,
with six pairs where a smaller symbol in front of a larger one means a
subtraction: IV, IX, XL, XC, CD and CM. So XIV is X + IV, which is 10 + 4.

The Romans wrote no zero and no negative numbers, and no symbol above M, so
only 1 to 3999 can be written at all. Anything outside that is not a numeral
that exists, and this says so instead of inventing one.

Adding and subtracting work on the values: read both numerals, operate, and
write the answer back as a numeral. Multiplying works the same way, and also
keeps the repeated addition it was taught as — X * V is X + X + X + X + X —
one term per unit of the right-hand number, for whoever wants to see it.

Like the rest of `core`, this says nothing to anybody. It returns the working
and raises, and the window decides the Spanish.
"""

from dataclasses import dataclass

# Every piece a numeral is built from, largest first, with the six subtractive
# pairs among them. Reading and writing both walk this list in order, which is
# what makes the canonical form the only one either of them produces.
PIECES = (
    ("M", 1000), ("CM", 900), ("D", 500), ("CD", 400),
    ("C", 100), ("XC", 90), ("L", 50), ("XL", 40),
    ("X", 10), ("IX", 9), ("V", 5), ("IV", 4), ("I", 1),
)

# The seven symbols, which is what "one digit" means for the multiplication.
SYMBOLS = ("I", "V", "X", "L", "C", "D", "M")

# MMMCMXCIX. There is no symbol for 5000, so nothing above this can be written.
LARGEST = 3999

class RomanError(ValueError):
    """Something is not a Roman numeral, or cannot be written as one."""

class EmptyRoman(RomanError):
    """There is nothing to read."""

class BadLetter(RomanError):
    """A character that is not a Roman symbol. `letter` is that character."""

    def __init__(self, letter: str) -> None:
        super().__init__(f"'{letter}' is not a Roman symbol.")
        self.letter = letter

class NotCanonical(RomanError):
    """
    Roman letters that add up, but are not how the number is written.

    `IIII` is four ones and `VV` is two fives; both say a number that has a
    numeral of its own, and `canonical` is that numeral.
    """

    def __init__(self, numeral: str, canonical: str) -> None:
        super().__init__(f"'{numeral}' is written '{canonical}'.")
        self.numeral = numeral
        self.canonical = canonical

class BadOrder(RomanError):
    """
    Roman letters in an order that spells nothing: `IC`, `XM`, `VX`.

    The six subtractive pairs are the only case where a smaller symbol comes
    before a larger one, and anything else never was a numeral.
    """

    def __init__(self, numeral: str) -> None:
        super().__init__(f"'{numeral}' is not how a numeral is put together.")
        self.numeral = numeral

class OutOfRange(RomanError):
    """A value with no numeral: zero, negative, or above `LARGEST`."""

    def __init__(self, value: int) -> None:
        super().__init__(f"{value} cannot be written in Roman numerals.")
        self.value = value

@dataclass(frozen=True)
class Piece:
    """One piece of a numeral as it is read: `IX` is 9, and subtracts."""

    text: str
    value: int

    @property
    def subtractive(self) -> bool:
        """Whether this piece is one of the six pairs, `IX` rather than `X`."""
        return len(self.text) == 2

@dataclass(frozen=True)
class Numeral:
    """A numeral, its value, and the pieces it was read as."""

    text: str
    value: int
    pieces: tuple[Piece, ...]

@dataclass(frozen=True)
class Operation:
    """
    One operation done on two numerals, with everything it took to do it.

    `terms` is the repeated addition of a multiplication, one term per time the
    left number is added; a sum or a difference has none. `numeral` is
    the answer written in Roman, or empty when the answer has no numeral, which
    is the whole of what a zero or a negative result means here.
    """

    left: Numeral
    right: Numeral
    sign: str
    value: int
    numeral: str
    terms: tuple[str, ...] = ()

    @property
    def writable(self) -> bool:
        """Whether the answer is a number the Romans could write down."""
        return bool(self.numeral)

def to_value(text: str) -> int:
    """
    Read a numeral as the sum its symbols stand for. `XIV` is 10 + 4.

    Only the canonical spelling is accepted: the value is written back out and
    compared with what was read, so `IIII` is refused for `IV`, and `IC` for
    being an order that never spelled anything.
    """
    return read(text).value

def to_roman(value: int) -> str:
    """
    Write a number as a numeral, taking the largest piece that fits, again and
    again: 1994 takes M, then CM, then XC, then IV.
    """
    if not 1 <= value <= LARGEST:
        raise OutOfRange(value)

    numeral = ""
    left = value
    for text, amount in PIECES:
        while left >= amount:
            numeral += text
            left -= amount
    return numeral

def read(text: str) -> Numeral:
    """
    A numeral with its value and the pieces it was read as, for showing the
    working. Raises `EmptyRoman`, `BadLetter` or `NotCanonical`.
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

    # Walking the pieces in order only ever spells the canonical form. Letters
    # left over never fitted anywhere, so the order itself is wrong; letters
    # that all fitted but write back differently are a spelling nobody used.
    if position != len(numeral):
        raise BadOrder(numeral)
    if to_roman(value) != numeral:
        raise NotCanonical(numeral, to_roman(value))

    return Numeral(numeral, value, tuple(pieces))

def sum_of(left: str, right: str) -> Operation:
    """`XIV + IX`: both are read, the values are added, the sum is written back."""
    return _operate(read(left), read(right), "+")

def difference_of(left: str, right: str) -> Operation:
    """
    `XIV - IX`: the same, taking one value from the other.

    A difference of zero or less has no numeral, and the operation says so
    rather than raising: that the Romans wrote no zero is the answer.
    """
    return _operate(read(left), read(right), "-")

def product_of(left: str, right: str) -> Operation:
    """
    One numeral times another, keeping the repeated addition it stands for:
    `X * V` is X + X + X + X + X, which is L.

    `terms` carries one copy of the left numeral per unit of the right one, so
    it is the sum itself and not a picture of it. A large right-hand number
    makes a long list — `X * MMM` is three thousand terms — and it is for the
    caller to decide how much of it is worth showing.
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
