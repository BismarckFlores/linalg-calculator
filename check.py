"""
Smoke test for the engine. Run it from the repository root: python check.py

It is not a test suite, it is a transcription check: if every line prints what
it says it should, the seven modules of `core/` are wired together correctly.
"""

from fractions import Fraction

from core.elimination import to_ref
from core.matrix import Matrix
from core.scalar import format_scalar
from core.systems import SystemKind, solve
from core.verification import verify
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

print("exact arithmetic, end to end")
third = solve(Matrix([[3, 1]]))
check("3x = 1", third.values, (Fraction(1, 3),))
check("and it checks out", verify(third.coefficients, third.constants, third.values).holds,
      True)

print()
print("Everything above says ok: the engine is wired correctly.")