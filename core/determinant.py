"""
El determinante de una matriz cuadrada, por los dos caminos que pide el curso.

Por cofactores: se elige una fila o una columna, y el determinante es la suma de
cada entrada por su cofactor, C_ij = (-1)^(i+j) * M_ij, donde el menor M_ij es
el determinante de lo que queda al tachar la fila i y la columna j. Es la
definicion, y se aplica a si misma en cada menor hasta llegar a una matriz de
1 x 1.

Por LU: se factoriza A (core/lu.py) y entonces det A es el producto de la
diagonal de U. Si hizo falta intercambiar filas, lo que se factoriza es PA = LU y
cada intercambio cambia el signo: det A = (-1)^intercambios * det U. La
factorizacion es de ese modulo; aqui solo se lee su diagonal.

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

from .lu import Factorization, factorize
from .matrix import Matrix
from .scalar import Scalar

# Hasta este tamano, un desarrollo por cofactores todavia termina en un instante.
# Mas alla, 7! = 5040 menores de orden 6 y subiendo: es justo lo que el enunciado
# del curso llama imposible, y la pagina avisa antes de dejar que ocurra.
COFACTOR_LIMIT = 8

# Por debajo de este orden, n! es menor que n^3 / 3 y los cofactores siguen
# siendo el camino corto; de 4 x 4 en adelante gana LU.
LU_FROM = 4

# Desarrollar sin limite: cada menor se parte hasta el orden 2. Para los tamanos
# que esta pagina admite, el arbol entero cabe en pantalla.
FULL = 99

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
class Rule:
    """
    El determinante de una 2 x 2, que es donde el desarrollo toca fondo.

    Una matriz de orden 2 no necesita menores: su determinante es ad - bc, el
    producto de la diagonal principal menos el de la secundaria.
    """

    a: Scalar
    b: Scalar
    c: Scalar
    d: Scalar

    @property
    def value(self) -> Scalar:
        """ad - bc."""
        return self.a * self.d - self.b * self.c

@dataclass(frozen=True)
class Summand:
    """
    Un sumando del desarrollo: la entrada, su menor, su signo y lo que aporta.

    `sign` es (-1)^(i+j) y `minor` es el menor entero, con su propio desarrollo
    colgando: es el mismo tipo que lo contiene, porque un menor se calcula igual
    que la matriz de la que salio. `cofactor` es sign por lo que vale el menor, y
    el aporte al determinante es entry * cofactor.
    """

    row: int
    col: int
    entry: Scalar
    sign: int
    minor: "Cofactors"
    cofactor: Scalar
    amount: Scalar

    @property
    def minor_value(self) -> Scalar:
        """Lo que vale el menor, que es lo unico que necesita la suma."""
        return self.minor.value

@dataclass(frozen=True)
class Cofactors:
    """
    Un determinante por cofactores, con el desarrollo entero colgando de el.

    `along` dice si el desarrollo fue por una fila o por una columna, e `index`
    cual de las dos. Cada sumando lleva su menor, y ese menor lleva su propio
    desarrollo, asi hacia abajo hasta el orden 2, donde `rule` escribe ad - bc y
    la recursion se detiene. Una matriz de orden 1 no tiene ni lo uno ni lo otro:
    su determinante es su unica entrada.

    Los terminos con entrada cero no se guardan: su aporte es cero y su menor ni
    se calcula, que es el unico ahorro que admite el metodo.

    Cuando el desarrollo se corta por profundidad, terms y rule quedan vacios: el
    valor esta, pero calculado por otro camino y sin procedimiento que ensenar.
    """

    matrix: Matrix
    along: str
    index: int
    terms: tuple[Summand, ...]
    rule: Rule | None
    value: Scalar

    @property
    def expanded(self) -> bool:
        """Si este determinante trae su procedimiento o solo su numero."""
        return bool(self.terms) or self.rule is not None

ROW = "fila"
COLUMN = "columna"

@dataclass(frozen=True)
class ByLU:
    """
    Un determinante leido en la diagonal de U, con la factorizacion que lo dio.

    La factorizacion es de core/lu.py y aqui no se toca: este modulo solo la lee.
    El determinante de A es el producto de la diagonal de U, y cada intercambio de
    filas lo multiplica por -1, asi que det A = (-1)^intercambios * producto.
    """

    factorization: Factorization
    value: Scalar

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

def by_cofactors(matrix: Matrix, depth: int = FULL) -> Cofactors:
    """
    El determinante por el desarrollo de cofactores, a lo largo de la mejor linea.

    Se desarrolla por la fila o la columna que mas ceros tenga, porque cada cero
    se salta un menor entero. Es la misma eleccion que se hace a mano y la unica
    manera de que el metodo no cueste siempre lo mismo.

    Cada menor se desarrolla igual, y asi hacia abajo hasta el orden 2, que se
    resuelve con ad - bc. depth es cuantos niveles de ese desglose se guardan:
    pasado ese limite el menor sigue valiendo lo mismo, pero calculado por otro
    camino y sin procedimiento que ensenar.
    """
    matrix.require_square()
    order = matrix.rows

    if order == 1:
        return Cofactors(matrix, "", 0, (), None, matrix.elem(1, 1))

    if order == 2:
        rule = Rule(matrix.elem(1, 1), matrix.elem(1, 2), matrix.elem(2, 1), matrix.elem(2, 2))
        return Cofactors(matrix, "", 0, (), rule, rule.value)

    if depth <= 0:
        return Cofactors(matrix, "", 0, (), None, determinant(matrix))

    along, index = best_line(matrix)
    terms: list[Summand] = []
    value = Scalar(0)
    for other in range(1, order + 1):
        row, col = (index, other) if along == ROW else (other, index)
        entry = matrix.elem(row, col)
        if entry == 0:
            continue
        minor = by_cofactors(matrix.minor(row, col), depth - 1)
        sign = -1 if (row + col) % 2 else 1
        cofactor = sign * minor.value
        amount = entry * cofactor
        terms.append(Summand(row, col, entry, sign, minor, cofactor, amount))
        value += amount

    return Cofactors(matrix, along, index, tuple(terms), None, value)

def by_lu(matrix: Matrix) -> ByLU:
    """
    El determinante por la factorizacion LU: se factoriza y se multiplica la diagonal.

    Los reemplazos de fila no cambian el determinante, asi que el de A es el de U,
    y U es triangular: su determinante es el producto de su diagonal. Cada
    intercambio de filas lo multiplica por -1. Una matriz singular deja un cero en
    la diagonal y el determinante da cero, sin nada especial que hacer: la
    factorizacion se completa en modo permisivo y el cero se lee igual.
    """
    factorization = factorize(matrix)
    value = Scalar(-1) ** factorization.swaps
    for entry in factorization.diagonal:
        value *= entry
    return ByLU(factorization, value)

def drawn_terms(expansion: Cofactors) -> int:
    """
    Cuantos sumandos tiene el desarrollo entero, contando los de sus menores.

    Es la medida del arbol: cada sumando es un bloque con su matriz, su signo y
    su cuenta, asi que esto es lo que costaria dibujarlo. Crece como n!, y por
    eso hay un tamano a partir del cual no se dibuja sino que se avisa.
    """
    return len(expansion.terms) + sum(drawn_terms(term.minor) for term in expansion.terms)

def determinant(matrix: Matrix) -> Scalar:
    """
    El determinante a secas, por el camino mas corto, sin guardar nada.

    Es lo que usan los menores de un desarrollo por cofactores, donde solo hace
    falta el numero. Los ordenes 1 y 2 se responden con su formula, ad - bc, y
    de ahi en adelante se reduce.
    """
    matrix.require_square()
    order = matrix.rows
    if order == 1:
        return matrix.elem(1, 1)
    if order == 2:
        return matrix.elem(1, 1) * matrix.elem(2, 2) - matrix.elem(1, 2) * matrix.elem(2, 1)
    return by_lu(matrix).value

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

