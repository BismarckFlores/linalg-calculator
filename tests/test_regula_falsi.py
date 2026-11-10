"""La secante, el intervalo y la parada de la regla falsa clásica."""

from fractions import Fraction
import unittest

from core.real_function import RootInputError
from core.regula_falsi import regula_falsi
from core.root_bracket import RootCriterion, RootStop


class RegulaFalsiTests(unittest.TestCase):
    def test_interpolation_and_trace_match_exact_arithmetic(self):
        result = regula_falsi("x^2 - 2", 1, 2, "0.000001", criterion=RootCriterion.RESIDUAL)
        a, b = Fraction(1), Fraction(2)
        for step in result.steps[:4]:
            fa, fb = a*a - 2, b*b - 2
            c = (a*fb - b*fa) / (fb - fa)
            self.assertAlmostEqual(step.a, float(a))
            self.assertAlmostEqual(step.b, float(b))
            self.assertAlmostEqual(step.c, float(c))
            self.assertLess(step.fa * step.fb, 0)
            a = c
        self.assertIs(result.stop, RootStop.TOLERANCE)
        self.assertLess(abs(result.value), 1e-6)

    def test_course_example_relative_percent(self):
        result = regula_falsi("x^3 - 4.23603x^2 - 2.73620x - 13.09037", "4.95", "5.5")
        self.assertIs(result.stop, RootStop.TOLERANCE)
        self.assertEqual(len(result.steps), 4)
        self.assertAlmostEqual(result.root, 5.236050508, places=9)
        self.assertIsNone(result.steps[0].relative_error)
        self.assertLess(result.steps[-1].relative_error, 0.01)

    def test_limits_and_rounding_do_not_claim_convergence(self):
        limited = regula_falsi("x^10 - 1", 0, "1.3", max_iterations=2)
        self.assertIs(limited.stop, RootStop.LIMIT)
        stagnant = regula_falsi("(x-1)^8 - 1e-30", 1, 2)
        self.assertIs(stagnant.stop, RootStop.STAGNATION)
        self.assertFalse(stagnant.converged)

    def test_bracket_checks_and_large_ordinates(self):
        with self.assertRaises(RootInputError):
            regula_falsi("x^2 + 1", -1, 1)
        self.assertFalse(regula_falsi("x^2 - 1", 1, 2).steps)
        result = regula_falsi("1e308*x", -1, 1)
        self.assertIs(result.stop, RootStop.ZERO)
        self.assertEqual(result.root, 0)
