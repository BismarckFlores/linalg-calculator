"""
Prueba de humo del motor. Se ejecuta desde la raiz del repositorio:
python check.py

No es una bateria de pruebas, es una comprobacion de transcripcion: si cada
linea imprime lo que dice que deberia, los modulos de core estan bien
conectados entre si.
"""

from fractions import Fraction

from core.bases import BadDigit, from_base, to_base
from core.echelon import analyse, free_columns, leading_entries, pivot_columns
from core.elimination import to_ref, to_rref
from core.equations import parse_equation, to_augmented, unknown_names
from core.inverse import invert, solve_with_inverse
from core.lu import factorize, solve_with_lu
from core.matrix import Matrix, NotSquare, SingularMatrix
from core.parametric import general_solution
from core.scalar import format_scalar
from core.systems import SystemKind, solve
from core.verification import verify
from ui.presentation import render_despeje, render_substitutions
from core.determinant import (
    best_line,
    by_cofactors,
    by_lu,
    costs,
    determinant,
)
from core.roman import (
    BadLetter,
    BadOrder,
    NotCanonical,
    difference_of,
    product_of,
    read,
    sum_of,
    to_roman,
    to_value,
)
from core.vectors import (
    DimensionMismatch,
    UnreadableComponent,
    add,
    combine,
    linear_sum,
    parse_vector,
    scale,
    subtract,
)
from core.worksheet import Worksheet


def show(value: object) -> str:
    """Lo que haya producido una comprobacion, en una linea y sin reprs."""
    if isinstance(value, Matrix):
        return " / ".join(str(value).splitlines())
    if isinstance(value, Fraction):
        return format_scalar(value)
    if isinstance(value, list):
        return "[" + ", ".join(show(item) for item in value) + "]"
    if isinstance(value, tuple):
        return "(" + ", ".join(show(item) for item in value) + ")"
    return str(value)


def check(name: str, got: object, expected: object) -> None:
    """Imprime una linea por afirmacion, y para en la primera que este mal."""
    if got == expected:
        print(f"  ok   {name}: {show(got)}")
        return
    print(f"  BAD  {name}: got {show(got)}, expected {show(expected)}")
    raise AssertionError(name)


print("scalar and matrix")
a = Matrix([[1, 2], [3, 4]])
b = Matrix([[5, 6], [7, 8]])
check("a_21", a.elem(2, 1), 3)
check("A + B", a + b, Matrix([[6, 8], [10, 12]]))
check("A - B", a - b, Matrix([[-4, -4], [-4, -4]]))
check("A * B", a * b, Matrix([[19, 22], [43, 50]]))
check("3 * A", 3 * a, Matrix([[3, 6], [9, 12]]))
check("A * v", a * Matrix.column_vector([5, 6]), Matrix([[17], [39]]))
check("transpose", a.transpose(), Matrix([[1, 3], [2, 4]]))
check("augment", a.augment(Matrix.column_vector([5, 6])), Matrix([[1, 2, 5], [3, 4, 6]]))
check("halves", a * "1/2", Matrix([["1/2", 1], ["3/2", 2]]))

print("worksheet: [[-1, 4], [2, -5]] reaches the identity")
sheet = Worksheet(Matrix([[-1, 4], [2, -5]]))
sheet.add_scaled(2, 1, 2)
sheet.scale(1, -1)
sheet.scale(2, "1/3")
sheet.add_scaled(1, 2, 4)
check("result", sheet.matrix, Matrix.identity(2))
check("steps", len(sheet.log), 4)
check("first label", sheet.log[0].label, "f_2 -> f_2 + 2*f_1")
check("snapshot(0)", sheet.log.snapshot(0), Matrix([[-1, 4], [2, -5]]))

print("elimination")
big = Matrix([[1, -2, 1, 0], [0, 2, -8, 8], [-4, 5, 9, -9]])
echelon = to_ref(big)
check("pivots", echelon.pivots, ((1, 1), (2, 2), (3, 3)))
check("rank", echelon.rank, 3)
check("every pivot is 1", [echelon.result.elem(r, c) for r, c in echelon.pivots], [1, 1, 1])
check("the original is untouched", echelon.original, big)
check("identity needs no work", to_ref(Matrix.identity(3)).log.is_empty(), True)
check("a zero column holds no pivot", to_ref(Matrix([[0, 1, 2], [0, 0, 3]])).pivots,
      ((1, 2), (2, 3)))

print("gauss-jordan: the same walk, with a second pass back up")
reduced = to_rref(big)
check("result", reduced.result, Matrix([[1, 0, 0, 29], [0, 1, 0, 16], [0, 0, 1, 3]]))
check("the pivots did not move", reduced.pivots, echelon.pivots)
check("it says it is reduced", reduced.reduced, True)
check("the walk down is the same walk",
      [step.label for step in reduced.log][:len(echelon.log)],
      [step.label for step in echelon.log])
check("a free variable keeps its column", to_rref(Matrix([[1, 1, 5], [2, 2, 10]])).result,
      Matrix([[1, 1, 5], [0, 0, 0]]))

print("reading an equation the way it is written")
check("coefficients", parse_equation("2x + 3y - z = 5").terms, {"x": 2, "y": 3, "z": -1})
check("constant", parse_equation("2x + 3y - z = 5").constant, 5)
check("an implicit 1", parse_equation("x - y = 0").terms, {"x": 1, "y": -1})
check("a fraction", parse_equation("(1/3)x = 2").terms, {"x": Fraction(1, 3)})
check("a comma is a decimal point", parse_equation("2,5x = 1").terms, {"x": Fraction(5, 2)})
check("the right side moves left", parse_equation("2x = 3y + 1").terms, {"x": 2, "y": -3})
check("and its constant moves right", parse_equation("2x = 3y + 1").constant, 1)
check("a constant on the left moves too", parse_equation("2x + 3 = 5").constant, 2)
check("an unknown that cancels is gone", parse_equation("x + y = x + 2").terms, {"y": 1})
system = [parse_equation("x + z = 1"), parse_equation("y = 2")]
check("x10 sorts after x2", unknown_names([parse_equation("x10 + x2 = 1")]), ["x2", "x10"])
check("the unknowns are whatever was written", unknown_names(system), ["x", "y", "z"])
check("an unmentioned unknown is a zero", to_augmented(system, unknown_names(system)),
      Matrix([[1, 0, 1, 1], [0, 1, 0, 2]]))

print("the three cases the assignment asks for")
check("unique", solve(Matrix([[1, 1, 5], [1, -1, 1]])).kind, SystemKind.UNIQUE)
check("infinite", solve(Matrix([[1, 1, 5], [2, 2, 10]])).kind, SystemKind.INFINITE)
check("inconsistent", solve(Matrix([[1, 1, 5], [1, 1, 8]])).kind, SystemKind.INCONSISTENT)

print("the clearing, from the last unknown to the first")
solution = solve(big)
check("values", solution.values, (29, 16, 3))
check("order", [step.column for step in solution.substitutions], [3, 2, 1])
check("the last one needs nothing replaced", solution.substitutions[0].terms, ())
check("the first one needs two", len(solution.substitutions[-1].terms), 2)
check("ranks", (solution.coefficient_rank, solution.rank, solution.unknowns), (3, 3, 3))
check("A back out of [A | b]", solution.coefficients,
      Matrix([[1, -2, 1], [0, 2, -8], [-4, 5, 9]]))
check("b back out of [A | b]", solution.constants, Matrix([[0], [8], [-9]]))

print("verification puts the answer back into the original system")
good = verify(solution.coefficients, solution.constants, solution.values)
check("holds", good.holds, True)
check("rows checked", len(good.checks), 3)
check("both sides of every row", [check_.left for check_ in good.checks], [0, 8, -9])
wrong = verify(solution.coefficients, solution.constants, (0, 0, 0))
check("catches a wrong answer", wrong.holds, False)

print("the five properties that define the two echelon forms")
staircase = analyse(Matrix([[2, -3, 2, 1], [0, 1, -4, 8], [0, 0, 0, 5]]))
check("echelon", staircase.is_echelon, True)
check("but not reduced, its leading entries are not 1", staircase.is_reduced, False)
check("property 4 names the row that breaks it", staircase.condition(4).row, 1)
check("leading entries", staircase.leading, ((1, 1), (2, 2), (3, 4)))

reduced = analyse(Matrix([[1, 0, -5, 1], [0, 1, 1, 4], [0, 0, 0, 0]]))
check("reduced", reduced.is_reduced, True)
check("a zero row at the bottom is allowed", reduced.condition(1).holds, True)

upside_down = analyse(Matrix([[0, 0, 0], [1, 2, 3], [0, 4, 5]]))
check("a zero row above a full one breaks property 1", upside_down.condition(1).row, 2)
check("and the matrix is not echelon", upside_down.is_echelon, False)
check("all zeros passes every property", analyse(Matrix.zero(2, 3)).is_reduced, True)

print("pivot positions live in the reduced form, not in the matrix as it stands")
lay = Matrix([[0, -3, -6, 4, 9], [-1, -2, -1, 3, 1], [-2, -3, 0, 3, -1], [1, 4, 5, -9, -7]])
check("pivot columns", pivot_columns(lay), (1, 2, 4))
check("the rest", free_columns(lay), (3, 5))
check("nothing leads a row of zeros", leading_entries(Matrix.zero(2, 2)), ())

print("the general solution of a system with infinitely many")
family = general_solution(to_rref(Matrix([[1, 1, 1, 6], [1, 2, 3, 14], [2, 3, 4, 20]])), 3)
check("one free variable", family.free, (3,))
check("two basic ones", [item.column for item in family.basic], [1, 2])
check("x = -2 + z", (family.basic[0].constant, family.basic[0].terms),
      (Fraction(-2), ((Fraction(1), 3),)))
check("y = 8 - 2z", (family.basic[1].constant, family.basic[1].terms),
      (Fraction(8), ((Fraction(-2), 3),)))
free_at = Fraction(5)
check("and it solves the system for any z", 
      [(-2 + free_at) + (8 - 2 * free_at) + free_at], [Fraction(6)])

print("numeral systems: dividing into a base, and reading back out of it")
binary = to_base(43, 2)
check("43 in base 2", binary.numeral, "101011")
check("the first division", (binary.divisions[0].quotient, binary.divisions[0].remainder),
      (21, 1))
check("every division holds", all(
    step.dividend == 2 * step.quotient + step.remainder for step in binary.divisions), True)
check("3054 in base 16", to_base(3054, 16).numeral, "BEE")
check("43 in base 8", to_base(43, 8).numeral, "53")
check("zero is one digit", to_base(0, 2).numeral, "0")
back = from_base("101011", 2)
check("101011 in base 2", back.value, 43)
check("its combination", [(term.value, term.position) for term in back.terms],
      [(1, 5), (0, 4), (1, 3), (0, 2), (1, 1), (1, 0)])
check("a letter is worth its value", from_base("2b", 16).terms[1].value, 11)
check("spaces are ignored", from_base("1010 1100", 2).value, 172)
check("the round trip holds", all(
    from_base(to_base(n, b).numeral, b).value == n for n in range(300) for b in (2, 8, 16)),
    True)
check("any base up to 36", to_base(35, 36).numeral, "Z")
check("43 in base 5", to_base(43, 5).numeral, "133")
check("a base with letters past F", from_base("1j", 20).value, 39)
check("the round trip holds in every base", all(
    from_base(to_base(n, b).numeral, b).value == n for n in range(200) for b in range(2, 37)),
    True)
check("-43 in base 2", to_base(-43, 2).numeral, "-101011")
check("a negative divides its absolute value", to_base(-43, 2).divisions[0].dividend, 43)
check("-2B in base 16", from_base("-2b", 16).value, -43)
check("the sign is not a term", len(from_base("-2B", 16).terms), 2)
check("minus zero is zero", (from_base("-0", 2).value, from_base("-0", 2).numeral), (0, "0"))
check("a plus changes nothing", from_base("+101", 2).value, 5)
check("negatives round trip in every base", all(
    from_base(to_base(-n, b).numeral, b).value == -n for n in range(100) for b in range(2, 37)),
    True)
try:
    from_base("1-0", 2)
    check("a sign in the middle is refused", "accepted", "refused")
except BadDigit as problem:
    check("a sign in the middle is refused", problem.digit, "-")
try:
    to_base(5, 37)
    check("base 37 is refused", "accepted", "refused")
except ValueError:
    check("base 37 is refused", "refused", "refused")
try:
    from_base("5", 5)
    check("a 5 is not a digit in base 5", "accepted", "refused")
except BadDigit as problem:
    check("a 5 is not a digit in base 5", problem.digit, "5")
try:
    from_base("102", 2)
    check("a 2 is not a binary digit", "accepted", "refused")
except BadDigit as problem:
    check("a 2 is not a binary digit", problem.digit, "2")

print("vectors of R^n: operations, and linear combinations")
u = parse_vector("(1, -2, 3)")
v = parse_vector("4 0 -1/2")
check("the dimension is what was typed", len(parse_vector("1; 2; 3; 4; 5")), 5)
check("a bracketed component", parse_vector("[1, (1/3)]"), (Fraction(1), Fraction(1, 3)))
check("u + v", add(u, v), (5, -2, Fraction(5, 2)))
check("u - v", subtract(u, v), (-3, -2, Fraction(7, 2)))
check("k u", scale(Fraction(-3), u), (-3, 6, -9))
check("a sum of multiples", linear_sum((Fraction(2), Fraction(-1)), (u, v)), (-2, -4, Fraction(13, 2)))
try:
    add(u, (Fraction(1), Fraction(2)))
    check("R^3 and R^2 do not add", "accepted", "refused")
except DimensionMismatch as problem:
    check("R^3 and R^2 do not add", (problem.first, problem.second), (3, 2))
try:
    parse_vector("1, dos, 3")
    check("a word is not a component", "accepted", "refused")
except UnreadableComponent as problem:
    check("a word is not a component", problem.text, "dos")
a1, a2 = parse_vector("1, -2, -5"), parse_vector("2, 5, 6")
one = combine([a1, a2], parse_vector("7, 4, -3"))
check("b is a combination, one way", (one.solution.kind, one.weights), (SystemKind.UNIQUE, (3, 2)))
check("and the weights give b", linear_sum(one.weights or (), [a1, a2]), (7, 4, -3))
none = combine([a1, a2], parse_vector("1, 0, 0"))
check("b is not a combination", (none.is_combination, none.weights), (False, None))
many = combine([parse_vector("1, 1"), parse_vector("2, 2"), parse_vector("0, 1")],
               parse_vector("3, 5"))
check("infinitely many ways", many.solution.kind, SystemKind.INFINITE)
check("the example sets the free scalar to 0", many.weights, (3, 0, 2))
check("and it gives b", linear_sum(many.weights or (), [parse_vector("1, 1"),
      parse_vector("2, 2"), parse_vector("0, 1")]), (3, 5))

print("matrix inverse and its application")
inverse_example = Matrix([[3, 4], [5, 6]])
inverse_result = invert(inverse_example)
check("the exact inverse", inverse_result.inverse,
      Matrix([[-3, 2], ["5/2", "-3/2"]]))
check("both products are the identity",
      (inverse_result.left_check, inverse_result.right_check),
      (Matrix.identity(2), Matrix.identity(2)))
check("inverse by one-by-one elimination", invert(Matrix([[7]])).inverse,
      Matrix([["1/7"]]))
check("there is no fixed order ten limit", invert(Matrix.identity(11)).inverse,
      Matrix.identity(11))
upper = Matrix([[1 if i == j else 2 if j == i + 1 else 0
                 for j in range(11)] for i in range(11)])
upper_inverse = invert(upper).inverse
check("order eleven nontrivial inverse",
      (upper_inverse.elem(1, 2), upper_inverse.elem(1, 11)), (-2, 1024))
application = solve_with_inverse(inverse_example, Matrix.column_vector([3, 7]))
check("x = inverse(A) times b", application.solution,
      Matrix.column_vector([5, -3]))
check("the original system holds", application.check, application.constants)
try:
    invert(Matrix([[1, -2, -1], [-1, 5, 6], [5, -4, 5]]))
    check("the practice matrix is singular", "accepted", "refused")
except SingularMatrix:
    check("the practice matrix is singular", "refused", "refused")
try:
    invert(Matrix([[1, 2, 3], [4, 5, 6]]))
    check("a rectangular matrix has no inverse", "accepted", "refused")
except ValueError:
    check("a rectangular matrix has no inverse", "refused", "refused")

print("roman numerals: reading, writing, and the three operations")
check("XIV is fourteen", to_value("XIV"), 14)
check("1994 is written", to_roman(1994), "MCMXCIV")
check("the largest numeral", to_roman(3999), "MMMCMXCIX")
check("every number from 1 to 3999 round trips", all(
    to_value(to_roman(n)) == n for n in range(1, 4000)), True)
check("a subtractive pair is one piece", [(p.text, p.value) for p in read("XIV").pieces],
      [("X", 10), ("IV", 4)])
check("XIV + IX", sum_of("XIV", "IX").numeral, "XXIII")
check("XIV - IX", difference_of("XIV", "IX").numeral, "V")
times = product_of("X", "V")
check("X * V by repeated addition", (times.terms, times.numeral), (("X",) * 5, "L"))
check("the terms are the operation", len(product_of("C", "X").terms), 10)
below = difference_of("V", "X")
check("a negative difference has no numeral", (below.value, below.numeral), (-5, ""))
check("zero has no numeral either", difference_of("V", "V").numeral, "")
check("nothing above MMMCMXCIX", sum_of("MMM", "M").numeral, "")
for text, kind in (("IIII", NotCanonical), ("IC", BadOrder), ("A", BadLetter)):
    try:
        read(text)
        check(f"{text} is refused", "accepted", "refused")
    except kind:
        check(f"{text} is refused", "refused", "refused")
check("IIII names its numeral", NotCanonical("IIII", "IV").canonical, "IV")
many = product_of("XIV", "IX")
check("any two numerals multiply", (many.value, many.numeral), (126, "CXXVI"))
check("and keep their terms", (len(many.terms), many.terms[0]), (9, "XIV"))
check("a product with no numeral", product_of("C", "C").numeral, "")

print("determinantes: por cofactores y por LU")
# El ejemplo de la presentacion: se reduce a triangular con un intercambio.
curso = Matrix([[1, -4, 2], [-2, 8, -9], [-1, 7, 0]])
check("det por cofactores", by_cofactors(curso).value, 15)
check("det por LU", by_lu(curso).value, 15)
check("el intercambio queda registrado", by_lu(curso).factorization.swaps, 1)
check("una triangular es el producto de su diagonal",
      by_lu(Matrix([[3, 0, 0], [5, 2, 0], [1, 7, -2]])).value, -12)
check("2 x 2 es ad - bc", determinant(Matrix([[3, -2], [-5, 4]])), 2)
check("1 x 1 es su unica entrada", determinant(Matrix([[7]])), 7)
check("el menor tacha fila y columna", curso.minor(3, 2).data,
      [[Fraction(1), Fraction(2)], [Fraction(-2), Fraction(-9)]])
check("se desarrolla por la linea con mas ceros", best_line(curso), ("fila", 3))
# El desarrollo se parte hasta el orden 2, donde termina en ad - bc.
grande = Matrix([[5, -7, 2, 2], [0, 3, 0, -4], [-5, -8, 0, 3], [0, 5, 0, -6]])
arbol = by_cofactors(grande)
check("el 4 x 4 se desarrolla", arbol.value, 20)
check("su menor trae su propio desarrollo", arbol.terms[0].minor.expanded, True)
dentro = arbol.terms[0].minor.terms[0].minor
check("el fondo es una 2 x 2 con su regla", (dentro.matrix.rows, dentro.rule is not None), (2, True))
check("y la regla es ad - bc", (dentro.rule.a * dentro.rule.d - dentro.rule.b * dentro.rule.c
                                if dentro.rule else None), dentro.value)
check("cortar la profundidad deja el valor pero no el camino",
      (by_cofactors(grande, 1).value, by_cofactors(grande, 1).terms[0].minor.expanded), (20, False))
check("una matriz singular tiene determinante cero",
      by_cofactors(Matrix([[1, 2, 3], [2, 4, 6], [1, 0, 1]])).value, 0)
check("los dos metodos coinciden siempre", all(
    by_cofactors(m).value == by_lu(m).value for m in (
        Matrix([[0, 1], [1, 0]]),
        Matrix([[2, 0, 0, 1], [0, 3, 0, 0], [0, 0, 1, 0], [5, 0, 0, 2]]),
        Matrix([[1, 2], [3, 4]]),
    )), True)
check("un intercambio cambia el signo", by_lu(Matrix([[0, 1], [1, 0]])).value, -1)
check("el costo decide el metodo", (costs(3).advised, costs(4).advised), ("cofactores", "LU"))
check("cofactores crece como n!", (costs(4).cofactor, costs(5).cofactor), (40, 205))
check("LU crece como n^3/3", (costs(4).lu, costs(10).lu), (20, 330))
try:
    determinant(Matrix([[1, 2, 3], [4, 5, 6]]))
    check("una matriz no cuadrada no tiene determinante", "aceptada", "rechazada")
except NotSquare as problem:
    check("una matriz no cuadrada no tiene determinante", (problem.rows, problem.cols), (2, 3))

print("factorizacion LU: PA = LU, y los sistemas que resuelve")
# El ejemplo del pptx de LU: L y U son las de la diapositiva.
diapositiva = Matrix([[3, -7, -2, 2], [-3, 5, 1, 0], [6, -4, 0, -5], [-9, 5, -5, 12]])
lu = factorize(diapositiva)
check("L es triangular inferior con unos", [row[:i + 1] for i, row in enumerate(lu.lower.data)],
      [[Fraction(1)], [Fraction(-1), Fraction(1)], [Fraction(2), Fraction(-5), Fraction(1)],
       [Fraction(-3), Fraction(8), Fraction(3), Fraction(1)]])
check("U es la escalonada de la diapositiva", lu.upper.row(2),
      [Fraction(0), Fraction(-2), Fraction(-1), Fraction(2)])
check("L por U devuelve A", lu.product, lu.permuted_matrix)
check("sin intercambios, P es la identidad", (lu.swaps, lu.permutation == Matrix.identity(4)), (0, True))
check("la comprobacion PA = LU se cumple", lu.holds, True)
check("la diagonal de U son los pivotes", lu.diagonal, (3, -2, -1, -1))
check("una invertible tiene rango completo", (lu.rank, lu.singular), (4, False))
# Un cero en el pivote obliga a intercambiar, y entonces lo factorizado es PA.
cero = factorize(Matrix([[0, 1], [1, 0]]))
check("un cero en el pivote intercambia filas", (cero.swaps, cero.permuted), (1, True))
check("y PA = LU sigue valiendo", cero.holds, True)
# El pivoteo parcial elige el mayor valor absoluto, no el primero que no es cero.
curso_lu = Matrix([[1, -4, 2], [-2, 8, -9], [-1, 7, 0]])
check("por defecto, el primer pivote no nulo", factorize(curso_lu).permutation.row(1),
      [Fraction(1), Fraction(0), Fraction(0)])
parcial = factorize(curso_lu, partial=True)
check("el parcial elige el de mayor valor absoluto", parcial.permutation.row(1),
      [Fraction(0), Fraction(1), Fraction(0)])
check("y tambien reconstruye la matriz", parcial.holds, True)
# Una singular: permisivo deja el cero en la diagonal, estricto se niega.
singular = Matrix([[1, 2, 3], [2, 4, 6], [1, 0, 1]])
flojo = factorize(singular)
check("permisivo completa la factorizacion", (flojo.singular, flojo.rank, flojo.holds), (True, 2, True))
check("y deja un cero en la diagonal de U", 0 in flojo.diagonal, True)
try:
    factorize(singular, strict=True)
    check("estricto rechaza la singular", "aceptada", "rechazada")
except SingularMatrix as problem:
    check("estricto rechaza la singular", problem.column, 3)
try:
    factorize(Matrix([[1, 2, 3], [4, 5, 6]]))
    check("una no cuadrada no se factoriza", "aceptada", "rechazada")
except NotSquare as problem:
    check("una no cuadrada no se factoriza", (problem.rows, problem.cols), (2, 3))
check("la factorizacion lleva su paso a paso", len(lu.log), 6)
# Ax = b con las dos sustituciones: los valores de la diapositiva.
sistema = solve_with_lu(diapositiva, Matrix.column_vector([-9, 5, 7, 11]))
check("Ly = b da y", [row[0] for row in sistema.intermediate.data],
      [Fraction(-9), Fraction(-4), Fraction(5), Fraction(1)])
check("Ux = y da x", [row[0] for row in sistema.solution.data],
      [Fraction(3), Fraction(4), Fraction(-6), Fraction(-1)])
check("A x devuelve b", sistema.check, sistema.constants)
check("hay un despeje por incognita", (len(sistema.forward), len(sistema.backward)), (4, 4))
check("en L el divisor es 1, en U es el pivote",
      (sistema.forward[1].divisor, sistema.backward[0].divisor), (1, -1))
try:
    solve_with_lu(singular, Matrix.column_vector([1, 2, 3]))
    check("una singular no se resuelve con LU", "resuelta", "rechazada")
except SingularMatrix:
    check("una singular no se resuelve con LU", "rechazada", "rechazada")
casos = (
    (Matrix([[0, 1], [1, 0]]), [2, 3]),
    (Matrix([[2, 1, 1], [4, 3, 3], [8, 7, 9]]), [1, 2, 3]),
    (Matrix([[0, 2, 1], [1, 1, 1], [3, 0, 4]]), [3, 2, 1]),
)
check("con intercambios tambien resuelve", all(
    solve_with_lu(m, Matrix.column_vector(b)).solution == solve_with_inverse(m, Matrix.column_vector(b)).solution
    for m, b in casos), True)
check("el pivoteo parcial da la misma solucion", all(
    solve_with_lu(m, Matrix.column_vector(b), partial=True).solution
    == solve_with_inverse(m, Matrix.column_vector(b)).solution for m, b in casos), True)

print("el texto de los despejes: el de la eliminacion no cambia, el de LU divide")
sistema_texto = solve(Matrix([[1, -2, 1, 0], [0, 2, -8, 8], [-4, 5, 9, -9]]))
check("la eliminacion se escribe como siempre", render_substitutions(sistema_texto),
      "  f_3:  z = 3\n\n"
      "  f_2:  y - 4z = 4\n        y - 4(3) = 4\n        y = 4 + 4(3)\n        y = 16\n\n"
      "  f_1:  x - 2y + z = 0\n        x - 2(16) + 3 = 0\n        x = 2(16) - 3\n        x = 29")
check("un coeficiente distinto de 1 despeja y luego divide",
      render_despeje("  f_1:  ", "x", Fraction(-2), [(Fraction(3), Fraction(4), "y")],
                     Fraction(-4), Fraction(8)),
      ["  f_1:  -2x + 3y = -4", "        -2x + 3(4) = -4", "        -2x = -4 - 3(4)",
       "        -2x = -16", "        x = 8", ""])
check("sin terminos conocidos, solo divide",
      render_despeje("  f_3:  ", "z", Fraction(2), [], Fraction(6), Fraction(3)),
      ["  f_3:  2z = 6", "        z = 3", ""])
check("con coeficiente 1 y sin terminos, una linea",
      render_despeje("  f_2:  ", "w", Fraction(1), [], Fraction(5), Fraction(5)),
      ["  f_2:  w = 5", ""])

print("exact arithmetic, end to end")
third = solve(Matrix([[3, 1]]))
check("3x = 1", third.values, (Fraction(1, 3),))
check("and it checks out", verify(third.coefficients, third.constants, third.values).holds,
      True)

print()
print("Everything above says ok: the engine is wired correctly.")
