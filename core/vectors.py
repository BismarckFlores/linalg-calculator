"""
Los vectores de R^n, y si uno de ellos es combinacion de los demas.

Un vector es una tupla de numeros exactos, y su longitud es su dimension n.
Aqui nada fija n de antemano: es la que tengan los vectores que se escriban, y
todos los de un mismo calculo tienen que coincidir.

Las operaciones son las que se hacen componente a componente:

    u + v = (u1 + v1, ..., un + vn)
    u - v = (u1 - v1, ..., un - vn)
    k u   = (k u1, ..., k un)

Un vector b es combinacion lineal de v1, ..., vk cuando hay escalares con
c1 v1 + ... + ck vk = b. Escrito componente a componente, eso es un sistema de n
ecuaciones con k escalares, y su matriz aumentada lleva los vectores como
columnas:

    [ v1 v2 ... vk | b ]

Asi que la pregunta se responde resolviendo ese sistema, con la misma
eliminacion que cualquier otro de aqui. Una solucion es una manera de
combinarlos, infinitas son infinitas maneras, y ninguna quiere decir que b no es
combinacion de ellos.

Como el resto de core, esto no le dice nada a nadie.
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

# Las componentes se separan con comas, punto y coma o espacios. Un decimal lleva
# punto, porque la coma ya significa que empieza la siguiente componente.
_SEPARATORS = re.compile(r"[,;\s]+")

class VectorError(ValueError):
    """Lo escrito no es un vector, o los vectores no encajan entre si."""

class EmptyVector(VectorError):
    """No hay componentes que leer."""

class UnreadableComponent(VectorError):
    """Una componente que no es un numero. text es el trozo que se escribio."""

    def __init__(self, text: str) -> None:
        super().__init__(f"'{text}' is not a number.")
        self.text = text

class DimensionMismatch(VectorError):
    """Dos vectores que no estan en el mismo Rn."""

    def __init__(self, first: int, second: int) -> None:
        super().__init__(f"A vector of R^{first} and one of R^{second} do not combine.")
        self.first = first
        self.second = second

def parse_vector(text: str) -> Vector:
    """
    Lee (1, -2, 1/3) como un vector de R3.

    Los parentesis alrededor del vector son opcionales, y tambien los de una
    componente suelta. La dimension es la cantidad de componentes que resulten.
    """
    inside = text.strip()
    if len(inside) >= 2 and inside[0] in "([⟨<" and inside[-1] in ")]⟩>":
        inside = inside[1:-1]
    pieces = [piece for piece in _SEPARATORS.split(inside) if piece]
    if not pieces:
        raise EmptyVector("There is no vector to read.")
    return tuple(_component(piece) for piece in pieces)

def add(u: Vector, v: Vector) -> Vector:
    """u + v: se suman las componentes que estan en la misma posicion."""
    _same_dimension(u, v)
    return tuple(a + b for a, b in zip(u, v))

def subtract(u: Vector, v: Vector) -> Vector:
    """u - v: a cada componente de u se le resta la de v en la misma posicion."""
    _same_dimension(u, v)
    return tuple(a - b for a, b in zip(u, v))

def scale(k: Scalar, u: Vector) -> Vector:
    """k u: cada componente multiplicada por el mismo escalar."""
    return tuple(k * a for a in u)

def linear_sum(weights: Sequence[Scalar], vectors: Sequence[Vector]) -> Vector:
    """
    c1 v1 + ... + ck vk, calculado como dice la definicion: se multiplica cada
    vector por su escalar y despues se suman uno tras otro.
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
    """[ v1 ... vk | b ]: los vectores puestos como columnas, y b como la ultima."""
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
    """Si b es combinacion de los vectores, y el sistema que lo decidio."""

    vectors: tuple[Vector, ...]
    target: Vector
    solution: Solution
    general: General | None

    @property
    def is_combination(self) -> bool:
        """Verdadero salvo que el sistema no tenga solucion."""
        return self.solution.kind is not SystemKind.INCONSISTENT

    @property
    def weights(self) -> Vector | None:
        """
        Una eleccion de escalares que funciona, o None si no hay ninguna.

        Con una sola solucion, es esa solucion. Con infinitas, es la que pone en 0
        todos los escalares libres, y entonces cada escalar basico vale la constante
        de su fila en la forma escalonada reducida.
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
    Decide si target es combinacion lineal de vectors.

    Arma [ v1 ... vk | b ] y lo resuelve. Cuando hay infinitas soluciones
    escribe tambien la familia, leida de la forma escalonada reducida.
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
