"""
Leer la forma de una matriz, en vez de ponerla en una.

elimination lleva una matriz a la forma escalonada. Esto pregunta lo contrario:
la matriz tal como esta, ya tiene esa forma? El curso lo responde con cinco
propiedades numeradas, y este modulo tambien: una comprobacion por propiedad,
y cada una marca la entrada que la rompe cuando alguna falla.

Comprobar propiedad por propiedad es el sentido de todo esto. Un si o un no no
le sirve de mucho a quien esta aprendiendo la definicion; que le digan que la
propiedad 2 falla en la fila 3, si.

Aqui no se decide ni una palabra. Una Condition es un numero, un veredicto y la
posicion que lo justifica; quien lo dibuja escribe la frase.
"""

from dataclasses import dataclass

from .elimination import to_rref
from .matrix import Matrix

# Las cinco propiedades, numeradas como las numera el curso: las tres
# primeras definen la forma escalonada, y las dos ultimas la reducida.
ECHELON = (1, 2, 3)
REDUCED = (4, 5)

@dataclass(frozen=True)
class Condition:
    """
    Una de las propiedades numeradas, y la entrada que la rompe cuando alguna
    la rompe.

    row y column se cuentan desde 1 y solo significan algo cuando holds es falso.
    La propiedad 1 es la excepcion: falla en una fila entera, asi que column
    se queda en 0.
    """

    number: int
    holds: bool
    row: int = 0
    column: int = 0

@dataclass(frozen=True)
class Form:
    """En que forma esta una matriz, propiedad por propiedad."""

    matrix: Matrix
    conditions: tuple[Condition, ...]
    leading: tuple[tuple[int, int], ...]

    def condition(self, number: int) -> Condition:
        """El veredicto sobre una de las propiedades numeradas."""
        for condition in self.conditions:
            if condition.number == number:
                return condition
        raise ValueError(f"There is no property number {number}.")

    @property
    def is_echelon(self) -> bool:
        """Si se cumplen las tres primeras propiedades."""
        return all(self.condition(number).holds for number in ECHELON)

    @property
    def is_reduced(self) -> bool:
        """Si se cumplen las cinco."""
        return self.is_echelon and all(
            self.condition(number).holds for number in REDUCED
        )

def leading_column(matrix: Matrix, row: int) -> int | None:
    """
    La columna de la entrada principal de una fila: la entrada distinta de cero
    que esta mas a la izquierda.

    Una fila de ceros no tiene ninguna, que es lo que dice None. Todas las
    propiedades de abajo estan escritas en terminos de estas entradas, igual que
    la definicion.
    """
    for column in range(1, matrix.cols + 1):
        if matrix.elem(row, column) != 0:
            return column
    return None

def leading_entries(matrix: Matrix) -> tuple[tuple[int, int], ...]:
    """La posicion de cada entrada principal, en orden de fila."""
    found = []
    for row in range(1, matrix.rows + 1):
        column = leading_column(matrix, row)
        if column is not None:
            found.append((row, column))
    return tuple(found)

def analyse(matrix: Matrix) -> Form:
    """
    Comprueba las cinco propiedades sobre una matriz tal como estan escritas.

    Una matriz de ceros las cumple las cinco: cada propiedad afirma algo sobre
    las filas que no son nulas, y no tiene ninguna. Eso no es un caso especial
    tratado aparte, es lo que hacen los bucles cuando no hay nada que recorrer.
    """
    leading = leading_entries(matrix)
    return Form(
        matrix,
        (
            _zero_rows_last(matrix),
            _staircase(leading),
            _zeros_below(matrix, leading),
            _leading_ones(matrix, leading),
            _alone_in_column(matrix, leading),
        ),
        leading,
    )

def pivot_positions(matrix: Matrix) -> tuple[tuple[int, int], ...]:
    """
    Las posiciones pivote de una matriz: donde quedan las entradas principales
    de su forma escalonada reducida.

    La definicion no habla de la matriz tal como esta. Una posicion pivote de A
    es un lugar de A que lleva una entrada principal una vez que A esta en forma
    escalonada reducida, asi que aqui se reduce primero y se informan las
    posiciones encontradas por el camino.
    """
    return to_rref(matrix).pivots

def pivot_columns(matrix: Matrix) -> tuple[int, ...]:
    """Las columnas que tienen una posicion pivote."""
    return tuple(column for _row, column in pivot_positions(matrix))

def free_columns(matrix: Matrix) -> tuple[int, ...]:
    """Las columnas que no tienen ninguna."""
    held = set(pivot_columns(matrix))
    return tuple(column for column in range(1, matrix.cols + 1) if column not in held)

def _zero_rows_last(matrix: Matrix) -> Condition:
    """Propiedad 1: ninguna fila de ceros esta por encima de una que no lo es."""
    zeros_seen = False
    for row in range(1, matrix.rows + 1):
        if matrix.is_zero_row(row):
            zeros_seen = True
        elif zeros_seen:
            return Condition(1, False, row)
    return Condition(1, True)

def _staircase(leading: tuple[tuple[int, int], ...]) -> Condition:
    """Propiedad 2: cada entrada principal queda a la derecha de la de arriba."""
    rightmost = 0
    for row, column in leading:
        if column <= rightmost:
            return Condition(2, False, row, column)
        rightmost = column
    return Condition(2, True)

def _zeros_below(matrix: Matrix, leading: tuple[tuple[int, int], ...]) -> Condition:
    """Propiedad 3: debajo de una entrada principal, su columna es toda ceros."""
    for row, column in leading:
        for below in range(row + 1, matrix.rows + 1):
            if matrix.elem(below, column) != 0:
                return Condition(3, False, below, column)
    return Condition(3, True)

def _leading_ones(matrix: Matrix, leading: tuple[tuple[int, int], ...]) -> Condition:
    """Propiedad 4: cada entrada principal es un 1."""
    for row, column in leading:
        if matrix.elem(row, column) != 1:
            return Condition(4, False, row, column)
    return Condition(4, True)

def _alone_in_column(matrix: Matrix, leading: tuple[tuple[int, int], ...]) -> Condition:
    """Propiedad 5: una entrada principal es la unica de su columna que no es cero."""
    for row, column in leading:
        for other in range(1, matrix.rows + 1):
            if other != row and matrix.elem(other, column) != 0:
                return Condition(5, False, other, column)
    return Condition(5, True)
