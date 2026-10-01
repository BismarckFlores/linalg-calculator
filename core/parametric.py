"""
La solucion general de un sistema que tiene infinitas.

systems.solve se detiene al decir que variables son libres. Esto escribe la
familia entera: cada variable basica, la que tiene un pivote, en funcion de las
libres, que es lo que el curso llama la solucion general.

Lee la forma escalonada reducida y nada mas. En la reducida un pivote es 1 y
esta solo en su columna, asi que la fila x1 + 4*x3 = 1 ya es el despeje de x1
con un cambio de signo, y no hace falta sustituir hacia atras. Pasarle una
escalonada sin reducir seria un error, asi que la rechaza.
"""

from dataclasses import dataclass

from .elimination import Elimination
from .scalar import Scalar

@dataclass(frozen=True)
class Basic:
    """Una variable basica, escrita en funcion de las libres."""

    column: int
    constant: Scalar
    terms: tuple[tuple[Scalar, int], ...]

@dataclass(frozen=True)
class General:
    """La familia entera: las variables basicas y las libres de las que dependen."""

    basic: tuple[Basic, ...]
    free: tuple[int, ...]

def general_solution(reduction: Elimination, unknowns: int) -> General:
    """
    Lee la familia de la forma escalonada reducida: cada variable basica en
    funcion de las libres.

    Solo las columnas de A cuentan como variables; un pivote en la columna de
    los terminos independientes significa que el sistema no tiene solucion
    ninguna, y entonces no hay familia que escribir. Quien llama clasifica
    primero y solo pregunta cuando hay algo que preguntar.
    """
    if not reduction.reduced:
        raise ValueError("The general solution is read off the reduced form.")

    result = reduction.result
    constants = unknowns + 1
    pivots = [(row, column) for row, column in reduction.pivots if column <= unknowns]
    held = {column for _row, column in pivots}
    free = tuple(column for column in range(1, unknowns + 1) if column not in held)

    basic = tuple(
        Basic(
            column,
            result.elem(row, constants),
            tuple(
                (-result.elem(row, other), other)
                for other in free
                if result.elem(row, other) != 0
            ),
        )
        for row, column in pivots
    )
    return General(basic, free)
