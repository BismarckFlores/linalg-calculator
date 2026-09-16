"""
Whole numbers written in any base from 2 to 36, and the working that moves them.

Two directions. Towards a base, by repeated division: each remainder is a digit,
and the digits read from the last division to the first. Back to decimal, by
the linear combination the numeral stands for: every digit times its base raised
to its position, counted from 0 on the right.

Nothing is borrowed from Python for either direction: no `int(text, base)`, no
`bin`, `oct` or `hex`. The point of the assignment is the procedure, so the
procedure is what runs.

Like the rest of `core`, this says nothing to anybody. It returns the steps and
raises, and the window decides the Spanish.
"""

from dataclasses import dataclass

# The symbols a digit is written with: the ten figures, then the alphabet. One
# symbol per digit is what makes a numeral readable, so the alphabet running out
# is where the bases stop.
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWEST_BASE = 2
HIGHEST_BASE = len(DIGITS)

class NumeralError(ValueError):
    """The text is not a numeral of the base it was given in."""

class EmptyNumeral(NumeralError):
    """There is nothing to read."""

class BadDigit(NumeralError):
    """A character that is not a digit of the base. `digit` is the character."""

    def __init__(self, digit: str, base: int) -> None:
        super().__init__(f"'{digit}' is not a digit in base {base}.")
        self.digit = digit
        self.base = base

@dataclass(frozen=True)
class Division:
    """One division of the procedure: `dividend = base * quotient + remainder`."""

    dividend: int
    quotient: int
    remainder: int

@dataclass(frozen=True)
class ToBase:
    """A whole number written in another base, and the divisions that wrote it."""

    value: int
    base: int
    divisions: tuple[Division, ...]
    numeral: str

@dataclass(frozen=True)
class Term:
    """One term of the combination: `digit * base ** position`."""

    digit: str
    value: int
    position: int
    power: int
    amount: int

@dataclass(frozen=True)
class FromBase:
    """A numeral read back as the combination of powers of its base."""

    numeral: str
    base: int
    terms: tuple[Term, ...]
    value: int

def digit_value(character: str, base: int) -> int:
    """What one digit is worth: `7` is 7, `B` is 11. Raises `BadDigit`."""
    value = DIGITS.find(character.upper())
    if value < 0 or value >= base:
        raise BadDigit(character, base)
    return value

def to_base(value: int, base: int) -> ToBase:
    """
    Write a whole number in another base by dividing it again and again.

    `n = b*q1 + r1`, then `q1 = b*q2 + r2`, and so on until a quotient is 0.
    Each remainder is less than the base, so it is one digit, and the last one
    found is the leading digit: `n = r_k*b^k + ... + r2*b + r1`.
    """
    _check(base)
    if value < 0:
        raise ValueError("Only whole numbers that are not negative are converted.")

    divisions: list[Division] = []
    current = value
    while True:
        quotient, remainder = current // base, current % base
        divisions.append(Division(current, quotient, remainder))
        current = quotient
        if current == 0:
            break

    numeral = "".join(DIGITS[step.remainder] for step in reversed(divisions))
    return ToBase(value, base, tuple(divisions), numeral)

def from_base(text: str, base: int) -> FromBase:
    """
    Read a numeral as the linear combination of powers of its base.

    `d_k ... d_1 d_0 = d_k*b^k + ... + d_1*b^1 + d_0*b^0`. Spaces are ignored,
    so a long binary number can be typed in groups, and letters in either case.
    """
    _check(base)
    numeral = "".join(text.split()).upper()
    if not numeral:
        raise EmptyNumeral("There is no numeral to read.")

    top = len(numeral) - 1
    terms: list[Term] = []
    for index, character in enumerate(numeral):
        value = digit_value(character, base)
        position = top - index
        power = base**position
        terms.append(Term(character, value, position, power, value * power))

    return FromBase(numeral, base, tuple(terms), sum(term.amount for term in terms))

def _check(base: int) -> None:
    if not LOWEST_BASE <= base <= HIGHEST_BASE:
        raise ValueError(f"Base {base} is not between {LOWEST_BASE} and {HIGHEST_BASE}.")
