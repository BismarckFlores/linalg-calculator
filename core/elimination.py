"""
La eliminacion gaussiana, en sus dos formas.

to_ref lleva la matriz a una forma escalonada por filas: la escalera de ceros,
con cada pivote normalizado a 1. to_rref sigue adelante y hace ceros tambien
*encima* de cada pivote, dejando la forma escalonada reducida, donde un pivote
es la unica entrada distinta de cero en su columna.

Las dos corren sobre un solo Worksheet, asi que el resultado y el paso a paso
son dos lecturas del mismo recorrido y no pueden separarse. Ademas comparten el
recorrido: to_rref es to_ref seguido de una segunda pasada, nunca un segundo
algoritmo.
"""

from dataclasses import dataclass

from .matrix import Matrix
from .steps import StepLog
from .worksheet import Worksheet

@dataclass(frozen=True)
class Elimination:
    """Lo que produjo una reduccion: el resultado, como se llego a el, y donde estan los pivotes"""

    original: Matrix
    result: Matrix
    log: StepLog
    pivots: tuple[tuple[int, int], ...]
    reduced: bool = False

    @property
    def rank(self) -> int:
        """El numero de pivotes, que es el rango de la matriz."""
        return len(self.pivots)

    def pivot_columns(self) -> list[int]:
        """Las columnas que tienen pivote, contando desde 1."""
        return [col for _row, col in self.pivots]

    def free_columns(self) -> list[int]:
        """Las columnas sin pivote, contando desde 1: las variables libres del sistema."""
        held = set(self.pivot_columns())
        return [col for col in range(1, self.result.cols + 1) if col not in held]

    def zero_rows(self) -> list[int]:
        """Las filas que quedaron todas a cero, contando desde 1."""
        return [i for i in range(1, self.result.rows + 1) if self.result.is_zero_row(i)]

def to_ref(matrix: Matrix, title: str = "") -> Elimination:
    """
    Reduce a una forma escalonada por filas, registrando cada operacion elemental.

    Un pivote por columna, normalizado a 1, con ceros por debajo. Una columna
    que esta toda a cero de esa fila hacia abajo no tiene pivote y se deja
    estar; la misma fila busca entonces una columna mas a la derecha, que es
    lo que hace que la escalera quede irregular cuando hay variables libres.
    """
    sheet = Worksheet(matrix, title)
    pivots = _forward(sheet)
    return Elimination(matrix, sheet.matrix, sheet.log, tuple(pivots))

def to_rref(matrix: Matrix, title: str = "") -> Elimination:
    """
    Reduce a la forma escalonada reducida por filas: Gauss-Jordan.

    El mismo recorrido de bajada que to_ref, y despues la vuelta hacia arriba:
    empezando por el pivote de mas a la derecha, se hacen ceros tambien por
    encima de cada pivote. Lo que sale cumple las dos condiciones de mas de la
    forma reducida: cada elemento principal es 1 y es el unico distinto de
    cero en su columna.

    La vuelta hacia arriba no mueve ningun pivote, asi que las posiciones
    encontradas en la bajada siguen siendo las posiciones al salir.
    """
    sheet = Worksheet(matrix, title)
    pivots = _forward(sheet)
    _backward(sheet, pivots)
    return Elimination(matrix, sheet.matrix, sheet.log, tuple(pivots), reduced=True)

def rank(matrix: Matrix) -> int:
    """Cuantos pivotes tiene la forma escalonada de esta matriz."""
    return to_ref(matrix).rank

def _forward(sheet: Worksheet) -> list[tuple[int, int]]:
    """
    La bajada: busca un pivote, lo lleva a 1 y hace ceros por debajo.

    Devuelve las posiciones de los pivotes en el orden en que se encontraron,
    que es por filas.
    """
    pivots: list[tuple[int, int]] = []
    row = 1

    for col in range(1, sheet.matrix.cols + 1):
        if row > sheet.matrix.rows:
            break

        pivot_row = _find_pivot_row(sheet.matrix, row, col)
        if pivot_row is None:
            continue

        sheet.swap(row, pivot_row)
        sheet.scale(row, 1 / sheet.matrix.elem(row, col))
        for below in range(row + 1, sheet.matrix.rows + 1):
            sheet.add_scaled(below, row, -sheet.matrix.elem(below, col))

        pivots.append((row, col))
        row += 1

    return pivots

def _backward(sheet: Worksheet, pivots: list[tuple[int, int]]) -> None:
    """
    La vuelta hacia arriba: hace ceros por encima de cada pivote, empezando
    por el de mas a la derecha.

    El orden de derecha a izquierda importa. Un pivote de mas a la derecha ya
    esta aislado cuando se usa para limpiar la columna de uno de mas a la
    izquierda, asi que ninguna operacion de aqui puede deshacer un cero que
    otra posterior ya habia conseguido.

    No se multiplica ninguna fila: _forward ya dejo todos los pivotes en 1.
    """
    for row, col in reversed(pivots):
        for above in range(1, row):
            sheet.add_scaled(above, row, -sheet.matrix.elem(above, col))

def _find_pivot_row(matrix: Matrix, from_row: int, col: int) -> int | None:
    """La primera fila, desde from_row hacia abajo, cuyo elemento en col no es cero."""
    for row in range(from_row, matrix.rows + 1):
        if matrix.elem(row, col) != 0:
            return row
    return None
