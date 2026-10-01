"""
Devolver la solucion al sitio del que salio.

Resolver es una cosa; demostrar que la respuesta se cumple es otra, y es la
unica comprobacion que no confia nada en la eliminacion. Cada ecuacion del
sistema *original* se evalua con los valores hallados, y los dos lados se
comparan de forma exacta, sin tolerancia, porque aqui nunca hubo redondeo.

Este modulo no sabe nada de como se llego a la solucion: se le dan A, b y una
lista de valores, y dice, fila por fila, si Ax = b.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from .matrix import Matrix
from .scalar import NumberLike, Scalar, to_scalar

@dataclass(frozen=True)
class RowCheck:
    """Una ecuacion del sistema original con los valores sustituidos en ella."""

    row: int
    terms: tuple[tuple[Scalar, Scalar, int], ...]
    left: Scalar
    right: Scalar

    @property
    def holds(self) -> bool:
        """Si esta ecuacion se cumple."""
        return self.left == self.right

@dataclass(frozen=True)
class Verification:
    """La misma comprobacion sobre todas las ecuaciones del sistema."""

    checks: tuple[RowCheck, ...]

    @property
    def holds(self) -> bool:
        """Cierto solo cuando se cumplen todas y cada una de las ecuaciones."""
        return all(check.holds for check in self.checks)

    def failures(self) -> tuple[RowCheck, ...]:
        """Las ecuaciones que no se cumplieron, si alguna no lo hizo."""
        return tuple(check for check in self.checks if not check.holds)

def verify(
    coefficients: Matrix, constants: Matrix, values: Sequence[NumberLike]
) -> Verification:
    """
    Evalua A x = b fila por fila con los valores hallados.

    constants es b como una sola columna, la misma forma que tiene dentro de
    la matriz aumentada. Cada RowCheck guarda sus terminos como
    (coeficiente, valor, columna) para que la interfaz pueda escribir la
    sustitucion entera y no solo dar el total.
    """
    if constants.cols != 1:
        raise ValueError(f"The constants must be a single column, got {constants.cols}.")
    if coefficients.rows != constants.rows:
        raise ValueError(
            f"A has {coefficients.rows} rows and b has {constants.rows}: they must match."
        )
    if len(values) != coefficients.cols:
        raise ValueError(
            f"A has {coefficients.cols} unknowns and {len(values)} values were given."
        )

    found = [to_scalar(value) for value in values]
    checks: list[RowCheck] = []

    for row in range(1, coefficients.rows + 1):
        terms = tuple(
            (coefficients.elem(row, col), found[col - 1], col)
            for col in range(1, coefficients.cols + 1)
        )
        left = sum((coefficient * value for coefficient, value, _col in terms), Scalar(0))
        checks.append(RowCheck(row, terms, left, constants.elem(row, 1)))

    return Verification(tuple(checks))
