"""
La factorizacion LU de una matriz cuadrada, y los sistemas que se resuelven con ella.

Factorizar es escribir A como un producto de dos triangulares: A = LU, con L
triangular inferior de unos en la diagonal y U triangular superior. U es lo que
queda de A al reducirla por filas con puros reemplazos, y L guarda lo que hizo
falta para llegar ahi: en la posicion (i, j) esta el multiplicador de la
operacion que hizo cero la entrada (i, j). Por eso la misma secuencia de
operaciones que lleva A a U lleva L a la identidad.

Cuando un pivote es cero hay que intercambiar filas, y lo que se factoriza es
PA = LU, donde P es la matriz de permutacion que recuerda esos intercambios. Sin
P la factorizacion no reconstruiria la matriz original.

Para que sirve: Ax = b se convierte en L(Ux) = Pb. Con Ux = y, primero se
despeja y de Ly = Pb hacia adelante y despues x de Ux = y hacia atras. Las dos
son sustituciones directas, y la factorizacion se hace una sola vez aunque b
cambie.

El determinante es otra cosa que la factorizacion aprovecha, y vive en
core/determinant.py: lee la diagonal de U. Aqui no se menciona.

Todo es exacto. Las recomendaciones de tolerancia (comparar un pivote con un
epsilon, limpiar ceros fantasma como 1.2e-16) existen porque en coma flotante
una resta que deberia dar cero da un numero minusculo. Con Fraction eso no pasa
nunca: lo que da cero es cero, asi que comparar con cero es correcto y no hay
nada que limpiar.

Como el resto de core, esto no le dice nada a nadie. Devuelve el procedimiento y
lanza errores, y la ventana decide el castellano.
"""

from dataclasses import dataclass

from .matrix import Matrix, SingularMatrix
from .scalar import Scalar
from .steps import StepLog
from .worksheet import Worksheet

@dataclass(frozen=True)
class Factorization:
    """
    La factorizacion PA = LU, con el registro de la reduccion que la produjo.

    `swaps` cuenta los intercambios de fila. Cuando no hubo ninguno, P es la
    identidad y esto es la A = LU de las diapositivas. `rank` es cuantas
    columnas dieron un pivote: igual al orden cuando la matriz es invertible, y
    menor cuando no lo es, en cuyo caso U lleva un cero en la diagonal.

    `log` es el registro de la reduccion, el mismo que lleva cualquier otra
    eliminacion del proyecto: la matriz de partida y, por cada operacion, la que
    quedo despues. Con el, la ventana recorre la reduccion paso a paso sin tener
    que recalcular nada, y lo que ve es lo que produjo L y U.
    """

    matrix: Matrix
    lower: Matrix
    upper: Matrix
    permutation: Matrix
    swaps: int
    rank: int
    log: StepLog

    @property
    def order(self) -> int:
        return self.matrix.rows

    @property
    def permuted(self) -> bool:
        """Si hubo que intercambiar filas, y entonces lo factorizado es PA."""
        return self.swaps > 0

    @property
    def row_order(self) -> tuple[int, ...]:
        """
        P como una lista: que fila de A quedo en cada lugar, contando desde 1.

        Es la misma informacion que la matriz de permutacion, escrita de la manera
        corta: (1, 3, 2) quiere decir que la fila 3 de A paso a ser la segunda.
        """
        n = self.order
        return tuple(
            next(j for j in range(1, n + 1) if self.permutation.elem(i, j) == 1)
            for i in range(1, n + 1)
        )

    @property
    def singular(self) -> bool:
        """Si a la matriz le falto algun pivote, y U lleva un cero en la diagonal."""
        return self.rank < self.order

    @property
    def diagonal(self) -> tuple[Scalar, ...]:
        """Las entradas de la diagonal de U, que es donde estan los pivotes."""
        return tuple(self.upper.elem(i, i) for i in range(1, self.order + 1))

    @property
    def permuted_matrix(self) -> Matrix:
        """P A: la matriz con las filas en el orden en que se factorizo."""
        return self.permutation * self.matrix

    @property
    def product(self) -> Matrix:
        """L U: lo que se obtiene al multiplicar los dos factores."""
        return self.lower * self.upper

    @property
    def holds(self) -> bool:
        """
        La comprobacion: PA = LU, con L triangular inferior de unos y U triangular.

        Se compara de forma exacta y sin tolerancia, porque nada se redondeo. Es la
        unica manera de saber que la factorizacion reconstruye la matriz original.
        """
        n = self.order
        unit_lower = all(
            self.lower.elem(i, j) == (1 if i == j else 0)
            for i in range(1, n + 1)
            for j in range(i, n + 1)
        )
        upper = all(self.upper.elem(i, j) == 0 for i in range(2, n + 1) for j in range(1, i))
        return unit_lower and upper and self.permuted_matrix == self.product

@dataclass(frozen=True)
class Substitution:
    """
    Un despeje de una triangular: la incognita, lo que ya se conoce y lo que queda.

    `known` son los terminos que ya tienen valor, como (coeficiente, valor, indice),
    y `constant` el lado derecho de esa ecuacion. `divisor` es el coeficiente de la
    incognita: 1 en L, que lleva unos en la diagonal, y el pivote en U.
    """

    unknown: int
    known: tuple[tuple[Scalar, Scalar, int], ...]
    constant: Scalar
    divisor: Scalar
    value: Scalar

@dataclass(frozen=True)
class LUSystem:
    """
    Un sistema Ax = b resuelto con la factorizacion, con las dos sustituciones.

    `permuted` es Pb, que es lo que de verdad se iguala a Ly, `intermediate` es y
    y `solution` es x. `check` es A x, que tiene que dar b.
    """

    factorization: Factorization
    constants: Matrix
    permuted: Matrix
    forward: tuple[Substitution, ...]
    intermediate: Matrix
    backward: tuple[Substitution, ...]
    solution: Matrix
    check: Matrix

def factorize(matrix: Matrix, partial: bool = False, strict: bool = False) -> Factorization:
    """
    Factoriza PA = LU reduciendo por filas, y apunta cada operacion.

    Se hacen ceros debajo de cada pivote con reemplazos de fila, y el multiplicador
    de cada operacion se guarda en L. Si el pivote es cero se intercambia con una
    fila de mas abajo que no lo sea, que es lo que convierte A = LU en PA = LU.

    `partial` activa el pivoteo parcial: en cada columna se elige como pivote el
    valor de mayor valor absoluto, no el primero que no sea cero. Es lo que se
    hace en coma flotante para que un pivote pequeno no estropee los demas; con
    fracciones exactas no hace falta, y por eso por defecto solo se intercambia
    cuando es indispensable, que es lo que ensenan las diapositivas.

    Una columna sin pivote (cero de la diagonal hacia abajo) quiere decir que la
    matriz es singular. En modo permisivo, el de siempre, la factorizacion se
    completa dejando ese cero en la diagonal de U, y `rank` dice cuantos pivotes
    hubo. En modo estricto, `strict`, se lanza SingularMatrix en cambio.

    La reduccion corre sobre un Worksheet, que es donde una operacion elemental
    ocurre y queda apuntada a la vez. Asi, el paso a paso es el mismo objeto que
    el de la eliminacion, y no puede contar una historia distinta de la que
    produjo L y U.
    """
    matrix.require_square()
    order = matrix.rows

    sheet = Worksheet(matrix, "Factorizacion LU")
    lower = [[Scalar(1) if i == j else Scalar(0) for j in range(order)] for i in range(order)]
    permutation = [[Scalar(1) if i == j else Scalar(0) for j in range(order)] for i in range(order)]
    swaps = 0
    rank = 0

    for column in range(1, order + 1):
        pivot = _pivot_row(sheet.matrix, column, partial)
        if pivot is None:
            if strict:
                raise SingularMatrix(
                    f"La columna {column} no tiene pivote: la matriz es singular.", column
                )
            continue
        rank += 1
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

    return Factorization(
        matrix,
        Matrix(lower),
        sheet.matrix,
        Matrix(permutation),
        swaps,
        rank,
        sheet.log,
    )

def solve_with_lu(matrix: Matrix, constants: Matrix, partial: bool = False) -> LUSystem:
    """
    Resuelve A x = b factorizando y despejando dos veces.

    PA = LU convierte A x = b en L(Ux) = Pb. Con Ux = y, se despeja y de Ly = Pb de
    arriba abajo, y despues x de Ux = y de abajo arriba. Cada despeje solo usa lo
    que ya se encontro, que es por lo que son sustituciones directas y no un
    sistema por resolver.

    Si U lleva un cero en la diagonal, la sustitucion hacia atras dividiria entre
    cero: la matriz es singular y este camino no la resuelve, asi que se lanza
    SingularMatrix. Clasificar un sistema asi es cosa de la eliminacion.

    El resultado se comprueba multiplicando A por x, que tiene que dar b, y eso
    no confia ni en la factorizacion ni en las sustituciones.
    """
    if constants.size() != (matrix.rows, 1):
        raise ValueError("Los términos independientes deben ser una columna con una entrada por fila.")

    factorization = factorize(matrix, partial)
    zero = next((i for i, entry in enumerate(factorization.diagonal, start=1) if entry == 0), None)
    if zero is not None:
        raise SingularMatrix(f"U tiene un cero en la diagonal, en la posición {zero}: la matriz es singular.", zero)

    permuted = factorization.permutation * constants
    forward = _substitute_forward(factorization.lower, permuted)
    intermediate = Matrix.column_vector([step.value for step in forward])
    backward = _substitute_backward(factorization.upper, intermediate)
    # La sustitucion hacia atras se hace de la ultima incognita a la primera, y
    # asi se guardan los pasos; el vector solucion, en cambio, va en su orden.
    solution = Matrix.column_vector(
        [step.value for step in sorted(backward, key=lambda step: step.unknown)]
    )
    check = matrix * solution

    if check != constants:
        raise ArithmeticError("La comprobación de la solución falló.")

    return LUSystem(
        factorization, constants, permuted, forward, intermediate, backward, solution, check
    )

def _substitute_forward(lower: Matrix, constants: Matrix) -> tuple[Substitution, ...]:
    """Ly = Pb, de la primera ecuacion a la ultima: cada y usa las anteriores."""
    steps: list[Substitution] = []
    values: list[Scalar] = []
    for i in range(1, lower.rows + 1):
        known = tuple(
            (lower.elem(i, j), values[j - 1], j) for j in range(1, i) if lower.elem(i, j) != 0
        )
        constant = constants.elem(i, 1)
        value = constant - sum((c * v for c, v, _j in known), Scalar(0))
        steps.append(Substitution(i, known, constant, Scalar(1), value))
        values.append(value)
    return tuple(steps)

def _substitute_backward(upper: Matrix, constants: Matrix) -> tuple[Substitution, ...]:
    """Ux = y, de la ultima ecuacion a la primera: cada x usa las siguientes."""
    steps: list[Substitution] = []
    values: dict[int, Scalar] = {}
    for i in range(upper.rows, 0, -1):
        known = tuple(
            (upper.elem(i, j), values[j], j)
            for j in range(i + 1, upper.cols + 1)
            if upper.elem(i, j) != 0
        )
        constant = constants.elem(i, 1)
        divisor = upper.elem(i, i)
        value = (constant - sum((c * v for c, v, _j in known), Scalar(0))) / divisor
        steps.append(Substitution(i, known, constant, divisor, value))
        values[i] = value
    return tuple(steps)

def _pivot_row(matrix: Matrix, column: int, partial: bool) -> int | None:
    """
    La fila, de esta columna hacia abajo, que sera el pivote.

    Con pivoteo parcial, la de mayor valor absoluto; si no, la primera que no sea
    cero. En un empate gana la de arriba, que es la que se elegiria a mano.
    """
    candidates = [row for row in range(column, matrix.rows + 1) if matrix.elem(row, column) != 0]
    if not candidates:
        return None
    if not partial:
        return candidates[0]
    return max(candidates, key=lambda row: abs(matrix.elem(row, column)))
