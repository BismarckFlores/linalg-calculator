"""Casos del curso y limites que podrian producir una falsa convergencia."""

import math
import unittest

from core.bisection import (
    BisectionCriterion, BisectionError, BisectionStop, RealFunction,
    bisect, bisection_number, sample_bisection,
)


COURSE_POLYNOMIAL = "x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10"


class BisectionTests(unittest.TestCase):
    def test_excel_residual_and_all_saved_midpoints(self):
        result = bisect(COURSE_POLYNOMIAL, "0.6", 1, criterion=BisectionCriterion.RESIDUAL)
        expected = (
            0.8, 0.7, 0.75, 0.775, 0.7625, 0.76875, 0.765625,
            0.7640625, 0.76328125, 0.763671875, 0.7638671875,
            0.76396484375, 0.763916015625, 0.7639404296875, 0.76392822265625,
        )
        self.assertEqual(len(result.steps), 15)
        for step, midpoint in zip(result.steps, expected):
            self.assertAlmostEqual(step.c, midpoint, places=14)
        self.assertAlmostEqual(result.value, 6.538248166698679e-5, places=13)
        self.assertLess(abs(result.value), 1e-4)
        self.assertGreater(result.steps[-2].residual, 1e-4)
        self.assertTrue(result.converged)

    def test_width_stopping_matches_reference_images(self):
        result = bisect(COURSE_POLYNOMIAL, "0.6", 1)
        self.assertEqual(len(result.steps), 13)
        self.assertAlmostEqual(result.root, 0.763916015625)
        self.assertLess(result.b - result.a, result.tolerance)
        self.assertGreater(abs(result.value), result.tolerance)
        self.assertAlmostEqual(result.bound, 4.8828125e-5)

    def test_relative_is_percent_and_not_residual(self):
        result = bisect("x^2-2", 1, 2, 1, criterion=BisectionCriterion.RELATIVE)
        self.assertIsNone(result.steps[0].relative_error)
        self.assertLess(result.steps[-1].relative_error, 1)
        self.assertGreaterEqual(result.steps[-2].relative_error, 1)
        self.assertAlmostEqual(result.root, 1.4140625)

    def test_the_bracket_retains_sqrt_two_and_halves(self):
        result = bisect("x^2 - 2", 1, 2, "1e-10")
        root = math.sqrt(2)
        self.assertLessEqual(abs(result.root - root), result.bound)
        for previous, step in zip(result.steps, result.steps[1:]):
            self.assertLessEqual(step.a, root)
            self.assertGreaterEqual(step.b, root)
            self.assertAlmostEqual(step.width, previous.width / 2)
            self.assertLessEqual(previous.a, step.a)
            self.assertGreaterEqual(previous.b, step.b)

    def test_boundary_roots_need_no_iterations(self):
        for interval in ((0, 2), (-2, 0)):
            result = bisect("x", *interval)
            self.assertEqual(result.root, 0)
            self.assertEqual(result.steps, ())
            self.assertEqual(result.bound, 0)

    def test_midpoint_zero_does_not_divide_by_zero(self):
        result = bisect("x", -1, 1, criterion=BisectionCriterion.RELATIVE)
        self.assertEqual(result.stop, BisectionStop.ZERO)
        self.assertIsNone(result.steps[-1].relative_error)

    def test_zero_midpoint_without_root_can_continue(self):
        result = bisect("x - 0.1", -1, 1, criterion=BisectionCriterion.RELATIVE)
        self.assertEqual(result.steps[0].c, 0)
        self.assertIsNone(result.steps[0].relative_error)
        self.assertTrue(result.converged)

    def test_iteration_limit_is_not_convergence(self):
        result = bisect("x^2-2", 1, 2, "1e-12", max_iterations=2)
        self.assertEqual(result.stop, BisectionStop.LIMIT)
        self.assertEqual(len(result.steps), 2)
        self.assertFalse(result.converged)
        self.assertEqual(result.root, result.steps[-1].c)

    def test_roundoff_stagnation_is_not_convergence(self):
        result = bisect("x^2-2", 1, 2, "1e-300")
        self.assertEqual(result.stop, BisectionStop.STAGNATION)
        self.assertFalse(result.converged)
        self.assertLess(len(result.steps), 100)

    def test_same_sign_is_rejected_even_with_loose_tolerance(self):
        with self.assertRaises(BisectionError):
            bisect("x^2+1", -1, 1, 100)
        with self.assertRaises(BisectionError):
            bisect("x^2", -1, 1)

    def test_adjacent_floats_can_already_satisfy_width_tolerance(self):
        b = math.sqrt(2)
        a = math.nextafter(b, 0)
        result = bisect("x^2-2", a, b, "1e-15")
        self.assertEqual(result.stop, BisectionStop.TOLERANCE)
        self.assertLess(result.b - result.a, result.tolerance)

    def test_tolerance_comparison_is_strict(self):
        result = bisect("x^2-2", 1, 2, "0.5")
        self.assertEqual(len(result.steps), 3)

    def test_parameters_are_validated(self):
        cases = (
            dict(a=2, b=1), dict(a=1, b=1), dict(a=1, b=2, tolerance=0),
            dict(a=1, b=2, tolerance=-1), dict(a=float("nan"), b=2),
            dict(a=1, b=float("inf")), dict(a=1, b=2, max_iterations=0),
            dict(a=1, b=2, max_iterations=True), dict(a=1, b=2, max_iterations=1001),
            dict(a=1, b=2, criterion="width"), dict(a=-1e308, b=1e308),
        )
        for case in cases:
            with self.subTest(case=case), self.assertRaises(BisectionError):
                bisect("x^2-2", **case)

    def test_large_sign_values_do_not_require_products(self):
        result = bisect("1e300*(x-0.3)", 0, 1)
        self.assertTrue(result.converged)
        self.assertLessEqual(abs(result.root - 0.3), result.bound)

    def test_small_sign_values_do_not_underflow_in_a_product(self):
        result = bisect("1e-300*(x-0.3)", 0, 1)
        self.assertTrue(result.converged)
        self.assertLessEqual(abs(result.root - 0.3), result.bound)

    def test_elementary_functions_and_arithmetic(self):
        cases = (("sin(pi/2)+cos(0)", 0, 2), ("exp(ln(e))", 0, math.e),
                 ("sqrt(abs(-x)) + log10(100)", 4, 4), ("-x^2 + 2^3", 2, 4),
                 ("x**3 + 1/2", 2, 8.5))
        for expression, x, value in cases:
            with self.subTest(expression=expression):
                self.assertAlmostEqual(RealFunction(expression)(x), value)

    def test_transcendental_root(self):
        result = bisect("exp(-x) - x", 0, 1, "1e-10")
        self.assertAlmostEqual(result.root, 0.5671432904097838, places=9)

    def test_code_and_unlisted_syntax_are_rejected(self):
        for expression in ("__import__('os')", "x.__class__", "[x][0]", "lambda: 1", "True",
                           "sqrt(x, 2)", "sin(x=x)", "sum([x])", "x if x else 0", "x=0"):
            with self.subTest(expression=expression), self.assertRaises(BisectionError):
                RealFunction(expression)

    def test_domain_and_overflow_are_reported(self):
        for expression, x in (("1/x", 0), ("ln(x)", -1), ("sqrt(x)", -1),
                              ("exp(x)", 1000), ("x^0.5", -1), ("2^2048", 0)):
            with self.subTest(expression=expression), self.assertRaises(BisectionError):
                RealFunction(expression)(x)
        with self.assertRaises(BisectionError):
            bisect("1/x", -1, 1)

    def test_underflow_is_not_a_false_zero(self):
        with self.assertRaises(BisectionError):
            RealFunction("1e-999*x")
        for expression in ("exp(-1000)", "1e-300*1e-300", "1e-300/1e300", "0.1^1000"):
            with self.subTest(expression=expression), self.assertRaises(BisectionError):
                RealFunction(expression)(1)

    def test_existing_number_reader_is_reused(self):
        self.assertEqual(bisection_number("1/2"), 0.5)
        self.assertEqual(bisection_number("0,25"), 0.25)
        for value in ("", "nan", "1e999999999", "1e-999", True):
            with self.subTest(value=value), self.assertRaises(BisectionError):
                bisection_number(value)

    def test_plot_samples_leave_gaps_at_undefined_points(self):
        points = sample_bisection(RealFunction("1/x"), -1, 1, 5)
        self.assertEqual(points[2], (0, None))
        self.assertEqual(points[0], (-1, -1))
        self.assertEqual(points[-1], (1, 1))


if __name__ == "__main__":
    unittest.main()
