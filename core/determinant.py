"""
El determinante de una matriz cuadrada, por los dos caminos que pide el curso.

Por cofactores: se elige una fila o una columna, y el determinante es la suma de
cada entrada por su cofactor, C_ij = (-1)^(i+j) * M_ij, donde el menor M_ij es
el determinante de lo que queda al tachar la fila i y la columna j. Es la
definicion, y se aplica a si misma en cada menor hasta llegar a una matriz de
1 x 1.

Por LU: se reduce A a una forma escalonada U con puros reemplazos de fila, se
guardan los multiplicadores en una triangular inferior L con unos en la
diagonal, y entonces det A es el producto de la diagonal de U. Si hizo falta
intercambiar filas, lo que se factoriza es PA = LU y cada intercambio cambia el
signo: det A = (-1)^intercambios * det U.

Los dos dan el mismo numero, y lo que los separa es el costo. El desarrollo por
cofactores necesita del orden de n! multiplicaciones y LU del orden de n^3 / 3,
asi que para una matriz de 4 x 4 ya conviene LU y a partir de ahi la diferencia
se vuelve absurda: una de 25 x 25 por cofactores son unas 1.5e25
multiplicaciones. `costs` pone los dos numeros uno al lado del otro para que la
eleccion se haga antes de calcular nada.

Como el resto de core, esto no le dice nada a nadie. Devuelve el procedimiento y
lanza errores, y la ventana decide el castellano.
"""

from dataclasses import dataclass

from .matrix import Matrix
from .scalar import Scalar
from .steps import StepLog
from .worksheet import Worksheet

# Hasta este tamano, un desarrollo por cofactores todavia termina en un instante.
# Mas alla, 7! = 5040 menores de orden 6 y subiendo: es justo lo que el enunciado
# del curso llama imposible, y la pagina avisa antes de dejar que ocurra.
COFACTOR_LIMIT = 8

# Por debajo de este orden, n! es menor que n^3 / 3 y los cofactores siguen
# siendo el camino corto; de 4 x 4 en adelante gana LU.
LU_FROM = 4

class NotSquare(ValueError):
    """La matriz no es cuadrada, y solo las cuadradas tienen determinante."""

    def __init__(self, rows: int, cols: int) -> None:
        super().__init__(f"A {rows}x{cols} matrix has no determinant.")
        self.rows = rows
        self.cols = cols

@dataclass(frozen=True)
class Costs:
    """
    Lo que costaria cada metodo en esta matriz, antes de elegir ninguno.

    Son multiplicaciones: las que hace el desarrollo por cofactores, que son del
    orden de n!, y las que hace LU, que son del orden de n^3 / 3. `advised` es el
    metodo mas barato de los dos.
    """

    order: int
    cofactor: int
    lu: int
    advised: str

    @property
    def times(self) -> int:
        """Cuantas veces mas caro es el desarrollo por cofactores que LU."""
        return self.cofactor // self.lu if self.lu else 0

@dataclass(frozen=True)
class Summand:
    """
    Un sumando del desarrollo: la entrada, su menor, su signo y lo que aporta.

    `sign` es (-1)^(i+j), `minor` es la matriz que queda al tachar la fila y la
    columna de la entrada, y `cofactor` es sign * det(minor). El aporte al
    determinante es entry * cofactor.
    """

    row: int
    col: int
    entry: Scalar
    sign: int
    minor: Matrix
    minor_value: Scalar
    cofactor: Scalar
    amount: Scalar

@dataclass(frozen=True)
class Cofactors:
    """
    Un determinante calculado por cofactores, con los sumandos que lo forman.

    `along` dice si el desarrollo fue por una fila o por una columna, e `index`
    cual de las dos. Los terminos con entrada cero no se guardan: su aporte es
    cero y su menor no se calcula, que es el unico ahorro que admite el metodo.
    """

    matrix: Matrix
    along: str
    index: int
    terms: tuple[Summand, ...]
    value: Scalar

ROW = "fila"
COLUMN = "columna"

@dataclass(frozen=True)
class Factorization:
    """
    La factorizacion PA = LU, y el determinante que se lee en la diagonal de U.

    `swaps` cuenta los intercambios de fila, que son los que cambian el signo.
    Cuando no hubo ninguno, P es la identidad y la factorizacion es la A = LU de
    las diapositivas.

    `log` es el registro de la reduccion, el mismo que lleva cualquier otra
    eliminacion del proyecto: la matriz de partida y, por cada operacion, la que
    quedo despues. Con el, la ventana recorre la reduccion paso a paso sin tener
    que recalcular nada.
    """

    matrix: Matrix
    lower: Matrix
    upper: Matrix
    permutation: Matrix
    swaps: int
    log: StepLog
    diagonal: tuple[Scalar, ...]
    value: Scalar

    @property
    def permuted(self) -> bool:
        """Si hubo que intercambiar filas, y entonces lo factorizado es PA."""
        return self.swaps > 0

def costs(order: int) -> Costs:
    """
    Lo que cuesta cada metodo para una matriz de este orden.

    El desarrollo por cofactores de orden n hace n menores de orden n - 1, y una
    multiplicacion por cada uno: M(n) = n * (M(n-1) + 1), con M(1) = 0. Eso es
    n! por una constante, que es la cuenta que hace el curso.

    La reduccion de LU hace, en la columna k, (n - k) divisiones y (n - k)^2
    multiplicaciones, lo que suma (n^3 - n) / 3 en total.
    """
    cofactor = 0
    for size in range(2, order + 1):
        cofactor = size * (cofactor + 1)
    lu = (order**3 - order) // 3
    advised = "LU" if order >= LU_FROM else "cofactores"
    return Costs(order, cofactor, lu, advised)

def by_cofactors(matrix: Matrix) -> Cofactors:
    """
    El determinante por el desarrollo de cofactores, a lo largo de la mejor linea.

    Se desarrolla por la fila o la columna que mas ceros tenga, porque cada cero
    se salta un menor entero. Es la misma eleccion que se hace a mano y la unica
    manera de que el metodo no cueste siempre lo mismo.
    """
    _require_square(matrix)
    along, index = best_line(matrix)
    order = matrix.rows

    if order == 1:
        value = matrix.elem(1, 1)
        return Cofactors(matrix, along, index, (), value)

    terms: list[Summand] = []
    value = Scalar(0)
    for other in range(1, order + 1):
        row, col = (index, other) if along == ROW else (other, index)
        entry = matrix.elem(row, col)
        if entry == 0:
            continue
        minor = minor_of(matrix, row, col)
        minor_value = determinant(minor)
        sign = -1 if (row + col) % 2 else 1
        cofactor = sign * minor_value
        amount = entry * cofactor
        terms.append(Summand(row, col, entry, sign, minor, minor_value, cofactor, amount))
        value += amount

    return Cofactors(matrix, along, index, tuple(terms), value)

def by_lu(matrix: Matrix) -> Factorization:
    """
    El determinante por la factorizacion LU, que es la eliminacion de siempre.

    Se hacen ceros debajo de cada pivote con puros reemplazos de fila, que no
    cambian el determinante, y el multiplicador de cada operacion se guarda en L.
    Si el pivote es cero se intercambia con una fila de mas abajo, que es lo que
    convierte A = LU en PA = LU y lo que cambia el signo del resultado.

    Una columna entera de ceros desde el pivote hacia abajo deja un cero en la
    diagonal de U, y entonces el determinante es cero: no hay nada que arreglar
    y la reduccion sigue hasta el final igual.

    La reduccion corre sobre un Worksheet, que es donde una operacion elemental
    ocurre y queda apuntada a la vez. Asi, el paso a paso de esta pagina es el
    mismo objeto que el de la eliminacion, y no puede contar una historia
    distinta de la que produjo L y U.
    """
    _require_square(matrix)
    order = matrix.rows

    sheet = Worksheet(matrix, "Factorizacion LU")
    lower = [[Scalar(1) if i == j else Scalar(0) for j in range(order)] for i in range(order)]
    permutation = [[Scalar(1) if i == j else Scalar(0) for j in range(order)] for i in range(order)]
    swaps = 0

    for column in range(1, order + 1):
        pivot = _pivot_row(sheet.matrix, column)
        if pivot is None:
            continue
        if pivot != column:
            sheet.swap(column, pivot)
            permutation[column - 1], permutation[pivot - 1] = (
                permutation[pivot - 1], permutation[column - 1]
            )
            # Los multiplicadores ya guardados viajan con su fila: pertenecen a la
            # ecuacion, no al lugar que ocupaba antes del intercambio.
            for before in range(column - 1):
                lower[column - 1][before], lower[pivot - 1][before] = (
                    lower[pivot - 1][before], lower[column - 1][before]
                )
            swaps += 1

        for row in range(column + 1, order + 1):
            entry = sheet.matrix.elem(row, column)
            if entry == 0:
                continue
            factor = entry / sheet.matrix.elem(column, column)
            lower[row - 1][column - 1] = factor
            # Restar factor veces la fila del pivote es sumar -factor veces, que es
            # como lo escribe el resto del proyecto y como se escribe a mano.
            sheet.add_scaled(row, column, -factor)

    upper = sheet.matrix
    diagonal = tuple(upper.elem(i, i) for i in range(1, order + 1))
    value = Scalar(-1) ** swaps
    for entry in diagonal:
        value *= entry

    return Factorization(
        matrix,
        Matrix(lower),
        upper,
        Matrix(permutation),
        swaps,
        sheet.log,
        diagonal,
        value,
    )

def determinant(matrix: Matrix) -> Scalar:
    """
    El determinante a secas, por el camino mas corto, sin guardar nada.

    Es lo que usan los menores de un desarrollo por cofactores, donde solo hace
    falta el numero. Los ordenes 1 y 2 se responden con su formula, ad - bc, y
    de ahi en adelante se reduce.
    """
    _require_square(matrix)
    order = matrix.rows
    if order == 1:
        return matrix.elem(1, 1)
    if order == 2:
        return matrix.elem(1, 1) * matrix.elem(2, 2) - matrix.elem(1, 2) * matrix.elem(2, 1)
    return by_lu(matrix).value

def minor_of(matrix: Matrix, row: int, col: int) -> Matrix:
    """La matriz que queda al tachar una fila y una columna, contando desde 1."""
    return Matrix([
        [value for j, value in enumerate(line, start=1) if j != col]
        for i, line in enumerate(matrix.data, start=1)
        if i != row
    ])

def best_line(matrix: Matrix) -> tuple[str, int]:
    """
    La fila o la columna con mas ceros, que es por donde conviene desarrollar.

    En empate gana la fila, y entre filas la primera, que es como se escribe a
    mano cuando ninguna destaca.
    """
    rows = [sum(1 for value in matrix.row(i) if value == 0) for i in range(1, matrix.rows + 1)]
    cols = [sum(1 for value in matrix.column(j) if value == 0) for j in range(1, matrix.cols + 1)]
    best_row = max(range(len(rows)), key=lambda i: rows[i])
    best_col = max(range(len(cols)), key=lambda j: cols[j])
    if cols[best_col] > rows[best_row]:
        return COLUMN, best_col + 1
    return ROW, best_row + 1

def _pivot_row(matrix: Matrix, column: int) -> int | None:
    """La primera fila de esta columna hacia abajo con una entrada no nula."""
    for row in range(column, matrix.rows + 1):
        if matrix.elem(row, column) != 0:
            return row
    return None

def _require_square(matrix: Matrix) -> None:
    if matrix.rows != matrix.cols or matrix.rows == 0:
        raise NotSquare(matrix.rows, matrix.cols)
