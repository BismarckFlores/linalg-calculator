"""
Smoke test for the engine. Run it from the repository root: python check.py

It is not a test suite, it is a transcription check: if every line prints what
it says it should, the modules of `core/` are wired together correctly.
"""

from fractions import Fraction

from core.bases import BadDigit, from_base, to_base
from core.echelon import analyse, free_columns, leading_entries, pivot_columns
from core.elimination import to_ref, to_rref
from core.equations import parse_equation, to_augmented, unknown_names
from core.matrix import Matrix
from core.parametric import general_solution
from core.scalar import format_scalar
from core.systems import SystemKind, solve
from core.verification import verify
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
    """Whatever a check produced, written on one line and without reprs."""
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
    """Print one line per claim, and stop at the first one that is wrong."""
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

print("exact arithmetic, end to end")
third = solve(Matrix([[3, 1]]))
check("3x = 1", third.values, (Fraction(1, 3),))
check("and it checks out", verify(third.coefficients, third.constants, third.values).holds,
      True)

print()
print("Everything above says ok: the engine is wired correctly.")