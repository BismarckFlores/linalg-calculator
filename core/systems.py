"""
Los sistemas lineales, leidos de una matriz aumentada [A | b].

solve reduce la matriz aumentada por eliminacion de filas y clasifica el sistema
como lo hace Rouche-Frobenius: compara el rango de la matriz de coeficientes con
el de la aumentada, y despues con el numero de incognitas.

    rango(A) < rango(A|b)                 sin solucion
    rango(A) = rango(A|b) < incognitas    infinitas soluciones
    rango(A) = rango(A|b) = incognitas    solucion unica

Cuando hay solucion unica, las incognitas se despejan hacia atras, de la ultima
a la primera, y se guarda cada uno de esos pasos: ver la matriz escalonada y
despues el despeje es el sentido del metodo.

Aqui nadie escribe una frase para una persona: la interfaz decide las palabras.
"""

from dataclasses import dataclass
from enum import Enum

from .elimination import Elimination, to_ref
from .matrix import Matrix
from .scalar import Scalar
from .steps import StepLog

class SystemKind(Enum):
    """La clasificacion de un sistema segun Rouche-Frobenius."""

    INCONSISTENT = "inconsistent"
    UNIQUE = "unique"
    INFINITE = "infinite"

@dataclass(frozen=True)
class BackSubstitution:
    """Una incognita despejada de la forma escalonada, y lo que costo despejarla."""

    column: int
    row: int
    constant: Scalar
    terms: tuple[tuple[Scalar, int], ...]
    value: Scalar

@dataclass(frozen=True)
class Solution:
    """Lo que la forma escalonada dice sobre el sistema."""

    kind: SystemKind
    reduction: Elimination
    unknowns: int
    values: tuple[Scalar, ...]
    free_columns: tuple[int, ...]
    homogeneous: bool
    substitutions: tuple[BackSubstitution, ...]

    @property
    def log(self) -> StepLog:
        return self.reduction.log

    @property
    def augmented(self) -> Matrix:
        """La matriz [A | b] tal como se entrego el sistema."""
        return self.reduction.original

    @property
    def result(self) -> Matrix:
        """La forma escalonada en la que termino la eliminacion."""
        return self.reduction.result

    @property
    def coefficients(self) -> Matrix:
        """La matriz A sola, para sustituir la solucion en el sistema original."""
        return self.augmented.take_columns(1, self.unknowns)

    @property
    def constants(self) -> Matrix:
        """El vector b solo, como una unica columna."""
        return self.augmented.take_columns(self.unknowns + 1, self.unknowns + 1)

    @property
    def rank(self) -> int:
        """Rango de la matriz aumentada."""
        return self.reduction.rank

    @property
    def coefficient_rank(self) -> int:
        """
        Rango de A: los pivotes que caen sobre una incognita, no sobre los terminos
        independientes.
        """
        return sum(1 for _row, col in self.reduction.pivots if col <= self.unknowns)

def solve(augmented: Matrix) -> Solution:
    """
    Resuelve el sistema escrito como matriz aumentada, con los terminos
    independientes en la ultima columna.

    Todo el recorrido hasta la forma escalonada esta en solution.log, y el
    despeje que viene despues esta en solution.substitutions.
    """
    if augmented.rows < 1 or augmented.cols < 2:
        raise ValueError("A system needs at least one equation and one unknown.")

    unknowns = augmented.cols - 1
    reduction = to_ref(augmented)

    coefficient_rank = sum(1 for _row, col in reduction.pivots if col <= unknowns)
    free_columns = tuple(col for col in reduction.free_columns() if col <= unknowns)
    homogeneous = all(row[-1] == 0 for row in augmented.data)

    values: tuple[Scalar, ...] = ()
    substitutions: tuple[BackSubstitution, ...] = ()

    if reduction.rank > coefficient_rank:
        # Un pivote cayo en la columna de terminos independientes: alguna fila dice 0 = k.
        kind = SystemKind.INCONSISTENT
    elif coefficient_rank < unknowns:
        # Menos pivotes que incognitas: las que sobran son libres.
        kind = SystemKind.INFINITE
    else:
        kind = SystemKind.UNIQUE
        substitutions = _back_substitute(reduction, unknowns)
        cleared = {step.column: step.value for step in substitutions}
        values = tuple(cleared[col] for col in range(1, unknowns + 1))

    return Solution(
        kind, reduction, unknowns, values, free_columns, homogeneous, substitutions
    )

def _back_substitute(
    reduction: Elimination, unknowns: int
) -> tuple[BackSubstitution, ...]:
    """
    Sube por la forma escalonada sustituyendo las incognitas ya despejadas.

    Solo se llama cuando la solucion es unica, que es lo que permite que sea
    tan corta: cada incognita tiene pivote, y cada pivote ya vale 1 porque
    to_ref los normaliza. Los pasos salen en el orden en que se hace el
    trabajo, asi que la ultima incognita va primero.
    """
    echelon = reduction.result
    constants = unknowns + 1
    known: dict[int, Scalar] = {}
    cleared: list[BackSubstitution] = []

    for row, col in reversed(reduction.pivots):
        constant = echelon.elem(row, constants)
        terms = tuple(
            (echelon.elem(row, other), other)
            for other in range(col + 1, constants)
            if echelon.elem(row, other) != 0
        )
        value = constant - sum(
            (coefficient * known[other] for coefficient, other in terms),
            start=Scalar(0),
        )
        known[col] = value
        cleared.append(BackSubstitution(col, row, constant, terms, value))

    return tuple(cleared)
