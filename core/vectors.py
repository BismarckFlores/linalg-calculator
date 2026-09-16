"""
Vectors of R^n, and whether one of them is a combination of others.

A vector is a tuple of exact numbers, and its length is its dimension n.
Nothing here fixes n in advance: it is whatever the vectors typed turn out to
have, and every vector of one calculation has to agree with the others.

The operations are the component-wise ones:

    u + v = (u1 + v1, ..., un + vn)
    u - v = (u1 - v1, ..., un - vn)
    k u   = (k u1, ..., k un)

A vector b is a linear combination of v1, ..., vk when some scalars make
c1 v1 + ... + ck vk = b. Written component by component that is a system of n
equations in the k scalars, and its augmented matrix has the vectors standing
as columns:

    [ v1 v2 ... vk | b ]

So the question is answered by solving that system, with the same elimination
as every other system here. One solution is one way of combining them,
infinitely many are infinitely many ways, and none means b is not a
combination of them at all.

Like the rest of `core`, this says nothing to anybody.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from .elimination import to_rref
from .matrix import Matrix
from .parametric import General, general_solution
from .scalar import Scalar, to_scalar
from .systems import Solution, SystemKind, solve

Vector = tuple[Scalar, ...]

# Components are separated by commas, semicolons or spaces. A decimal takes a
# point, because a comma already means the next component.
_SEPARATORS = re.compile(r"[,;\s]+")

class VectorError(ValueError):
    """Something typed is not a vector, or the vectors do not fit together."""

class EmptyVector(VectorError):
    """There are no components to read."""

class UnreadableComponent(VectorError):
    """A component that is not a number. `text` is the piece that was typed."""

    def __init__(self, text: str) -> None:
        super().__init__(f"'{text}' is not a number.")
        self.text = text

class DimensionMismatch(VectorError):
    """Two vectors that do not live in the same R^n."""

    def __init__(self, first: int, second: int) -> None:
        super().__init__(f"A vector of R^{first} and one of R^{second} do not combine.")
        self.first = first
        self.second = second

def parse_vector(text: str) -> Vector:
    """
    Read `(1, -2, 1/3)` as a vector of R^3.

    The brackets around the whole vector are optional, and so are brackets
    around a single component. The dimension is however many components there
    turn out to be.
    """
    inside = text.strip()
    if len(inside) >= 2 and inside[0] in "([⟨<" and inside[-1] in ")]⟩>":
        inside = inside[1:-1]
    pieces = [piece for piece in _SEPARATORS.split(inside) if piece]
    if not pieces:
        raise EmptyVector("There is no vector to read.")
    return tuple(_component(piece) for piece in pieces)

def add(u: Vector, v: Vector) -> Vector:
    """u + v: the components in the same position added together."""
    _same_dimension(u, v)
    return tuple(a + b for a, b in zip(u, v))

def subtract(u: Vector, v: Vector) -> Vector:
    """u - v: the components of v taken from those of u, position by position."""
    _same_dimension(u, v)
    return tuple(a - b for a, b in zip(u, v))

def scale(k: Scalar, u: Vector) -> Vector:
    """k u: every component multiplied by the same scalar."""
    return tuple(k * a for a in u)

def linear_sum(weights: Sequence[Scalar], vectors: Sequence[Vector]) -> Vector:
    """
    c1 v1 + ... + ck vk, worked out as the definition says: scale each vector,
    then add them one after another.
    """
    if len(weights) != len(vectors):
        raise ValueError(f"{len(weights)} scalars were given for {len(vectors)} vectors.")
    if not vectors:
        raise EmptyVector("There are no vectors to add up.")
    total: Vector = tuple(Scalar(0) for _ in vectors[0])
    for weight, vector in zip(weights, vectors):
        total = add(total, scale(weight, vector))
    return total

def combination_matrix(vectors: Sequence[Vector], target: Vector) -> Matrix:
    """[ v1 ... vk | b ]: the vectors standing as columns, and b as the last one."""
    if not vectors:
        raise EmptyVector("At least one vector is needed to form a combination.")
    for vector in vectors:
        _same_dimension(vector, target)
    return Matrix([
        [vector[row] for vector in vectors] + [target[row]]
        for row in range(len(target))
    ])

@dataclass(frozen=True)
class Combination:
    """Whether b is a combination of the vectors, and the system that decided it."""

    vectors: tuple[Vector, ...]
    target: Vector
    solution: Solution
    general: General | None

    @property
    def is_combination(self) -> bool:
        """True unless the system has no solution."""
        return self.solution.kind is not SystemKind.INCONSISTENT

    @property
    def weights(self) -> Vector | None:
        """
        One choice of scalars that works, or None when there is none.

        With a single solution that is the solution. With infinitely many it is
        the one that sets every free scalar to 0, which leaves each basic scalar
        equal to the constant of its row in the reduced form.
        """
        if self.solution.kind is SystemKind.UNIQUE:
            return self.solution.values
        if self.general is None:
            return None
        weights = [Scalar(0)] * len(self.vectors)
        for basic in self.general.basic:
            weights[basic.column - 1] = basic.constant
        return tuple(weights)

def combine(vectors: Sequence[Vector], target: Vector) -> Combination:
    """
    Decide whether `target` is a linear combination of `vectors`.

    Builds [ v1 ... vk | b ] and solves it. When there are infinitely many
    solutions the family is written out as well, read off the reduced form.
    """
    augmented = combination_matrix(vectors, target)
    solution = solve(augmented)
    general = None
    if solution.kind is SystemKind.INFINITE:
        general = general_solution(to_rref(augmented), len(vectors))
    return Combination(tuple(vectors), target, solution, general)

def _component(text: str) -> Scalar:
    bare = text[1:-1] if text.startswith("(") and text.endswith(")") else text
    try:
        return to_scalar(bare)
    except (ValueError, TypeError):
        raise UnreadableComponent(text) from None

def _same_dimension(u: Vector, v: Vector) -> None:
    if len(u) != len(v):
        raise DimensionMismatch(len(u), len(v))
