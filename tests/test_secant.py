"""Traza y condiciones de parada de la secante."""

import unittest

from core.numerical_methods.handlers.real_function import RootInputError
from core.numerical_methods.handlers.root_bracket import RootStop
from core.numerical_methods.secant import secant


class SecantTests(unittest.TestCase):
    def test_guided_trace_and_absolute_tolerance(self):
        result = secant("x^3-x-2", 1, 2)
        self.assertEqual(result.stop, RootStop.TOLERANCE)
        self.assertEqual(result.iterations, 7)
        self.assertAlmostEqual(result.steps[0].next_x, 4 / 3)
        self.assertAlmostEqual(result.root, 1.5213797068045676)
        self.assertLessEqual(result.steps[-1].absolute_error, result.tolerance)
        for step, following in zip(result.steps, result.steps[1:]):
            self.assertEqual((following.previous, following.x), (step.x, step.next_x))

    def test_limit_same_sign_and_zero_denominator(self):
        limited = secant("x^3-2x-5", 2, 3, max_iterations=1)
        self.assertEqual((limited.stop, limited.iterations), (RootStop.LIMIT, 1))
        self.assertTrue(secant("x^2-2", 2, 3).converged)
        horizontal = secant("x^2+1", -1, 1)
        self.assertEqual((horizontal.stop, horizontal.iterations), (RootStop.ZERO_DENOMINATOR, 0))
        with self.assertRaisesRegex(RootInputError, "distintas"):
            secant("x^2-2", 2, 2)

    def test_exact_root_and_large_ordinates(self):
        initial = secant("x-1", 1, 2)
        self.assertEqual((initial.stop, initial.root, initial.iterations), (RootStop.ZERO, 1, 0))
        result = secant("1e308*x", -1, 1)
        self.assertEqual((result.stop, result.root), (RootStop.ZERO, 0))
