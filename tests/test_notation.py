"""La notacion implicita conserva los calculos y los limites de cada lector."""

import math
import unittest
from fractions import Fraction

from core.numerical_methods.bisection import BisectionError, RealFunction, bisect
from core.linear_algebra.handlers.equations import EquationError, parse_equation


class ImplicitProductTests(unittest.TestCase):
    def test_trigonometric_functions_inverses_and_powers(self):
        cases = (
            ("e^x-sin^(-1)(x)+cos^2(2x)", 0.5, math.exp(0.5) - math.asin(0.5) + math.cos(1)**2),
            ("sin⁻¹(x)+cos²(2x)", 0.5, math.asin(0.5) + math.cos(1)**2),
            ("2cos^2(sin^2(x))", 0.5, 2 * math.cos(math.sin(0.5)**2)**2),
            ("cos^(1/2)(0)", 0, 1),
            ("sin(x)^(-1)", math.pi / 2, 1),
            ("sec(x)", math.pi / 3, 2),
            ("csc(x)", math.pi / 6, 2),
            ("cot(x)", math.pi / 4, 1),
            ("arccos(x)", 0, math.pi / 2),
            ("arctan(x)", 1, math.pi / 4),
            ("sec^-1(x)", 2, math.pi / 3),
            ("arccsc(x)", 2, math.pi / 6),
            ("arccot(x)", -1, 3 * math.pi / 4),
        )
        for expression, x, expected in cases:
            with self.subTest(expression=expression):
                self.assertAlmostEqual(RealFunction(expression)(x), expected)
        for expression in ("sec(pi/2)", "csc(pi)", "cot(0)", "tan(pi/2)", "arcsin(2)", "arcsec(0.5)"):
            with self.subTest(expression=expression), self.assertRaises(BisectionError):
                RealFunction(expression)(0)

    def test_logarithms_with_and_without_explicit_base(self):
        self.assertAlmostEqual(RealFunction("log(2, x)")(8), 3)
        self.assertAlmostEqual(RealFunction("log(1/2, x)")(4), -2)
        self.assertAlmostEqual(RealFunction("log(x)")(math.e), 1)
        self.assertAlmostEqual(RealFunction("log10(x)")(100), 2)
        for expression in ("log(1, x)", "log(0, x)", "log(-2, x)", "log(2, -x)", "abs(1, x)"):
            with self.subTest(expression=expression), self.assertRaises(BisectionError):
                RealFunction(expression)(8)

    def test_products_in_functions(self):
        cases = (
            ("5x^3", 2, 40), ("0.5x^2", 2, 2), ("(1/2)x", 2, 1),
            ("2(x+1)", 2, 6), ("x(x+1)", 2, 6),
            ("(x+1)(x-1)", 2, 3), ("(x+1)2", 2, 6),
            ("2sin(x)", math.pi/2, 2), ("sin(x)cos(x)", math.pi/4, 0.5),
            ("2pi", 0, 2*math.pi), ("x pi", 2, 2*math.pi),
            ("x sin(x)", math.pi/2, math.pi/2), ("2sin(x)^2", math.pi/2, 2),
            ("1/2x", 4, 2), ("1/(2x)", 4, 0.125),
            ("2(\nx + 1\n)", 2, 6),
        )
        for expression, x, expected in cases:
            with self.subTest(expression=expression):
                self.assertAlmostEqual(RealFunction(expression)(x), expected)

    def test_scientific_numbers_are_not_split(self):
        for expression, expected in (("1e-3x", 0.002), ("1e+3x", 2000),
                                     ("2e3", 2000), ("2e", 2*math.e)):
            with self.subTest(expression=expression):
                self.assertAlmostEqual(RealFunction(expression)(2), expected)

    def test_implicit_course_polynomial_has_identical_iterations(self):
        implicit = bisect("x^4 - 5x^3 + 0.5x^2 - 11x + 10", 0.6, 1)
        explicit = bisect("x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10", 0.6, 1)
        self.assertEqual(implicit.steps, explicit.steps)
        self.assertEqual(implicit.root, explicit.root)
        self.assertEqual(implicit.value, explicit.value)

    def test_original_linear_notation_is_preserved(self):
        for implicit, explicit in (
            ("5x+2y=7", "5*x+2*y=7"),
            ("(1/2)x-3y=1", "(1/2)*x-3*y=1"),
            ("2,5x+y=0", "2,5*x+y=0"),
            ("2 x = 6", "2*x=6"),
        ):
            with self.subTest(expression=implicit):
                left, right = parse_equation(implicit), parse_equation(explicit)
                self.assertEqual(left.terms, right.terms)
                self.assertEqual(left.constant, right.constant)
        self.assertEqual(parse_equation("(1/2)x=0").terms, {"x": Fraction(1, 2)})

    def test_linear_identifiers_are_not_split(self):
        result = parse_equation("2x1 + 3x10 + 4xy + 1e3x = 0")
        self.assertEqual(result.terms, {"x1": 2, "x10": 3, "xy": 4, "e3x": 1})

    def test_linear_reader_still_rejects_nonlinear_work(self):
        for expression in ("5x^3=0", "x*y=1", "x*x=1", "x(x+1)=0", "2(x+1)=0"):
            with self.subTest(expression=expression), self.assertRaises(EquationError):
                parse_equation(expression)

    def test_malformed_text_does_not_become_a_product(self):
        for expression in ("1 2", "1..2", "sin x", "pix", "x2", "x**", "(x+1", "unknown(x)"):
            with self.subTest(expression=expression), self.assertRaises(BisectionError):
                RealFunction(expression)


if __name__ == "__main__":
    unittest.main()
