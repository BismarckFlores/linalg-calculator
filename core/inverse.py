"""
La inversa de una matriz cuadrada, hallada con la eliminacion que ya hay aqui.

A^-1 es la matriz que deshace A: A A^-1 = A^-1 A = I. Se halla reduciendo
[A | I] a su forma escalonada reducida. Cada operacion de fila que convierte A
en I le hace lo mismo a I, y en lo que I se convierte es exactamente A^-1. Si el
bloque izquierdo no llega a I, la matriz tiene menos de n pivotes y no hay
inversa.

Una vez que hay inversa, A x = b se resuelve multiplicando: x = A^-1 b. Es un
camino distinto al de la eliminacion, y solo sirve cuando A es invertible, asi
que un sistema singular sigue siendo cosa de core/systems.py.

Aqui no se cree nada bajo palabra: se calculan los dos productos y se comparan
con la identidad, y la solucion se sustituye de vuelta en A x.

Como el resto de core, esto no le dice nada a nadie. Devuelve las matrices y
lanza errores; la ventana decide el castellano.
"""

from dataclasses import dataclass

from .elimination import Elimination, to_rref
from .matrix import Matrix


class SingularMatrix(ValueError):
    """Una matriz cuadrada con menos de n pivotes, que no tiene inversa."""


@dataclass(frozen=True)
class InverseResult:
    """
    Una inversa y todo lo que hizo falta para encontrarla.

    reduction es el recorrido de [A | I] a [I | A^-1], asi que el paso a paso y
    el resultado son dos lecturas de la misma eliminacion. left_check y
    right_check son los dos productos, guardados en vez de descartados, porque
    mostrarlos es lo que demuestra el resultado.
    """

    original: Matrix
    inverse: Matrix
    reduction: Elimination
    left_check: Matrix
    right_check: Matrix


@dataclass(frozen=True)
class InverseSystem:
    """Un sistema resuelto con la inversa: x = A^-1 b, y A x sustituido de vuelta."""

    inverse_result: InverseResult
    constants: Matrix
    solution: Matrix
    check: Matrix


def invert(matrix: Matrix) -> InverseResult:
    """
    Reduce [A | I] y lee A^-1 en la mitad derecha.

    Que la mitad izquierda llegue a I es el teorema de la matriz invertible en la
    practica: ocurre exactamente cuando A tiene n posiciones pivote. Cuando no,
    la matriz es singular y no hay nada que devolver.
    """
    matrix.require_square()

    # I se agrega a la derecha, asi que cada operacion que actua sobre A actua
    # sobre ella a la vez. Ese es todo el metodo: A se vuelve I, e I se vuelve A^-1.
    identity = Matrix.identity(matrix.rows)
    reduction = to_rref(matrix.augment(identity))

    if reduction.result.take_columns(1, matrix.rows) != identity:
        raise SingularMatrix("The matrix is singular.")

    inverse = reduction.result.take_columns(matrix.rows + 1, 2 * matrix.rows)
    left_check = matrix * inverse
    right_check = inverse * matrix

    # Los dos productos, no uno. Para una matriz cuadrada, AB = I basta por el
    # teorema, pero comprobar la pareja cuesta una multiplicacion y responde a la
    # definicion en vez de apoyarse en el.
    if left_check != identity or right_check != identity:
        raise ArithmeticError("The inverse failed verification.")

    return InverseResult(matrix, inverse, reduction, left_check, right_check)


def solve_with_inverse(matrix: Matrix, constants: Matrix) -> InverseSystem:
    """
    Resuelve A x = b como x = A^-1 b, y lo comprueba en la A original.

    Multiplicar por A^-1 por la izquierda en los dos lados de A x = b da
    x = A^-1 b, y como A es invertible esa x es la unica solucion. La
    comprobacion multiplica A por ella y la compara con b, lo que no confia ni en
    la inversa ni en la eliminacion que la produjo.
    """
    if constants.size() != (matrix.rows, 1):
        raise ValueError("The constants must be a column with one entry per row.")

    result = invert(matrix)
    solution = result.inverse * constants
    check = matrix * solution

    if check != constants:
        raise ArithmeticError("The solution failed verification.")

    return InverseSystem(result, constants, solution, check)
