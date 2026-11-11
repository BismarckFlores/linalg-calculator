import unittest

import sympy as sp

from core.calculus import X, differentiate, integrate, read_calculus_point
from core.numerical_methods.handlers.real_function import RootInputError


class CalculusTests(unittest.TestCase):
    def test_derivative_can_be_displayed_and_evaluated(self):
        derivative = differentiate("x³ - x - 2")
        self.assertEqual(derivative.expression, 3 * X**2 - 1)
        self.assertEqual(derivative.at(read_calculus_point("1,5")), sp.Rational(23, 4))
        self.assertEqual(derivative(1.5), 5.75)
        self.assertEqual(differentiate("log(2,x)").expression, 1 / (X * sp.log(2)))

    def test_derivative_rejects_undefined_points(self):
        zero = read_calculus_point("0")
        for function in ("abs(x)", "sqrt(x)", "x/x"):
            with self.subTest(function=function), self.assertRaises(RootInputError):
                differentiate(function).at(zero)

    def test_integrals_are_exact(self):
        zero, one = map(read_calculus_point, ("0", "1"))
        self.assertEqual(integrate("x^2"), X**3 / 3)
        self.assertEqual(integrate("1/x"), sp.log(sp.Abs(X)))
        self.assertEqual(integrate("x^2", (zero, one)), sp.Rational(1, 3))
        self.assertEqual(integrate("x^2", (one, zero)), -sp.Rational(1, 3))
        self.assertEqual(integrate("x^2", (one, one)), 0)

    def test_integral_rejects_discontinuities_including_canceled_factors(self):
        bounds = tuple(map(read_calculus_point, ("0", "2")))
        for function in ("1/(x-1)", "(x-1)/(x-1)", "tan(x)"):
            with self.subTest(function=function), self.assertRaises(RootInputError):
                integrate(function, bounds)

    def test_input_reuses_the_function_reader(self):
        with self.assertRaises(RootInputError):
            differentiate("x.__class__")
        with self.assertRaises(RootInputError):
            read_calculus_point("x + 1")
