"""
Reading an equation the way it is written down: `2x + 3y - z = 5`.

What comes out is the same thing a row of an augmented matrix holds, so the
rest of the project never learns that any text was involved. Both sides are
read and then tidied into one: unknowns move left, constants move right, and an
unknown mentioned on both sides is subtracted rather than counted twice.

The unknowns are whatever the equations turn out to mention. Nobody declares
them in advance, which is the point: the person writes the system down and the
number of columns follows from it.

Like the rest of `core`, this says nothing to anybody. It raises, and
`ui/prompts.py` decides the Spanish.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from .matrix import Matrix
from .scalar import Scalar, to_scalar

# One term: an optional sign, an optional coefficient written plainly or inside
# parentheses, an optional `*`, and an optional name. Everything is optional
# because `x`, `2`, `-3y` and `(1/2)z` are all terms; a match with neither a
# number nor a name is the one combination that means nothing.
_TERM = re.compile(
    r"(?P<sign>[+-])?"
    r"(?:\((?P<grouped>[^()]*)\)|(?P<number>\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?))?"
    r"\*?"
    r"(?P<name>[a-z_][a-z0-9_]*)?"
)

# A name split into its letters and its trailing digits, for sorting.
_NAME = re.compile(r"([a-z_]+)(\d*)")

class EquationError(ValueError):
    """Something in the text of an equation cannot be read."""

class MissingEquals(EquationError):
    """The text does not hold exactly one `=`."""

class UnreadableTerm(EquationError):
    """A fragment of a side is not a term. `text` is the fragment itself."""

    def __init__(self, text: str) -> None:
        super().__init__(f"'{text}' is not a term.")
        self.text = text

@dataclass(frozen=True)
class Equation:
    """One equation, tidied: `terms = constant`, with nothing left on the right."""

    terms: dict[str, Scalar]
    constant: Scalar
    text: str

def parse_equation(text: str) -> Equation:
    """
    Read one written equation.

    Whatever is on the right moves left and whatever is constant moves right, so
    `2x = 3y + 1` and `2x - 3y = 1` come back identical. A coefficient that
    cancels to zero is dropped: after `x + y = x + 2` the system does not mention
    x at all, and pretending otherwise would invent a column.
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
    Every unknown the equations mention, in the order they become columns.

    Alphabetical, with trailing digits compared as numbers so that x2 comes
    before x10. Alphabetical and not order of appearance, because `2y + 3x = 5`
    should still put x in the first column: that is where a reader looks for it.
    """
    found = {name for equation in equations for name in equation.terms}
    return sorted(found, key=_sort_key)

def to_augmented(equations: Sequence[Equation], names: Sequence[str]) -> Matrix:
    """
    Lay the equations out as [A | b] against those names.

    An unknown that an equation never mentions is a zero in that row, which is
    what lets somebody write `x + z = 1` and `y = 2` and still get a system of
    three columns out of it.
    """
    return Matrix([
        [equation.terms.get(name, Scalar(0)) for name in names] + [equation.constant]
        for equation in equations
    ])

def _parse_side(text: str) -> tuple[dict[str, Scalar], Scalar]:
    """
    Read one side into its coefficients and its constant.

    Whitespace goes first, so `2 x` and `2x` are the same thing, and the text is
    lowercased, so `X` and `x` are the same unknown. Then terms are taken left to
    right until the side is used up; anything the pattern cannot consume is
    reported with the fragment that stopped it.
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
            # A lone sign. What went wrong is whatever comes after it.
            raise UnreadableTerm(packed[match.end():] or packed[position:])

        try:
            # A written coefficient is read by `to_scalar`, so `1/3`, `2.5` and
            # `2,5` mean here exactly what they mean everywhere else.
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
    """Letters first, then trailing digits as a number: x, x1, x2, x10, y."""
    match = _NAME.fullmatch(name)
    if match is None:
        return (name, 0)
    head, digits = match.groups()
    return (head, int(digits) if digits else 0)
