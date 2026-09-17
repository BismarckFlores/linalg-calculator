"""
Whole numbers written in any base from 2 to 36, and the working that moves them.

Two directions. Towards a base, by repeated division: each remainder is a digit,
and the digits read from the last division to the first. Back to decimal, by
the linear combination the numeral stands for: every digit times its base raised
to its position, counted from 0 on the right.

A negative number keeps its sign apart from its digits, the way it is written
by hand in any base: -43 is -101011 in base 2 and -2B in base 16. The digits
are those of the absolute value, and the minus multiplies the whole thing. The
sign is never one of the digits, so this works the same in every base.

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
    """
    A whole number written in another base, and the divisions that wrote it.

    `value` keeps its sign. The divisions are those of its absolute value, and
    `numeral` is their digits with a minus in front when the number is negative.
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
    """One term of the combination: `digit * base ** position`."""

    digit: str
    value: int
    position: int
    power: int
    amount: int

@dataclass(frozen=True)
class FromBase:
    """
    A numeral read back as the combination of powers of its base.

    The terms are those of the digits alone. When the numeral has a minus in
    front, `negative` is true and `value` is minus their sum.
    """

    numeral: str
    base: int
    terms: tuple[Term, ...]
    value: int
    negative: bool = False

    @property
    def magnitude(self) -> int:
        """What the digits add up to, before the sign is applied."""
        return sum(term.amount for term in self.terms)

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

    A negative number divides its absolute value and puts the minus back in
    front of the digits: `-n` in base b is `-(n in base b)`.
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
    Read a numeral as the linear combination of powers of its base.

    `d_k ... d_1 d_0 = d_k*b^k + ... + d_1*b^1 + d_0*b^0`. Spaces are ignored,
    so a long binary number can be typed in groups, and letters in either case.

    A leading minus makes the number negative: the digits after it are read as
    above, and the sum is negated. A leading plus is accepted and changes
    nothing. Minus zero is zero, and is written without a sign.
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
