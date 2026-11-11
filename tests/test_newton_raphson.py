import unittest

from core.numerical_methods.handlers.real_function import RealFunction, RootInputError
from core.numerical_methods.handlers.root_bracket import RootStop
from core.numerical_methods.newton_raphson import newton_raphson


class NewtonRaphsonTests(unittest.TestCase):
    example = "x^3 - x - 2"

    def test_guided_example_stops_at_absolute_tolerance(self):
        function = RealFunction(self.example)
        result = newton_raphson(function, "1,5")
        self.assertIs(result.function, function)
        self.assertIs(result.stop, RootStop.TOLERANCE)
        self.assertTrue(result.converged)
        self.assertEqual(result.iterations, 3)
        self.assertAlmostEqual(result.root, 1.521379707, places=9)
        first = result.steps[0]
        self.assertEqual((first.index, first.x, first.fx, first.dfx), (1, 1.5, -0.125, 5.75))
        self.assertAlmostEqual(first.next_x, 1.521739130, places=9)
        self.assertAlmostEqual(first.absolute_error, 0.021739130, places=9)
        self.assertGreater(result.steps[-2].absolute_error, result.tolerance)
        self.assertLessEqual(result.steps[-1].absolute_error, result.tolerance)
        self.assertEqual(result.value, result.steps[-1].next_fx)

    def test_iteration_limit_and_tolerance_on_the_last_step(self):
        limited = newton_raphson(self.example, "3/2", max_iterations=1)
        self.assertIs(limited.stop, RootStop.LIMIT)
        self.assertFalse(limited.converged)
        self.assertEqual(limited.iterations, 1)
        accepted = newton_raphson(self.example, 1.5, limited.steps[0].absolute_error, max_iterations=1)
        self.assertIs(accepted.stop, RootStop.TOLERANCE)

    def test_exact_initial_and_new_roots(self):
        initial = newton_raphson("x^2", 0)
        self.assertIs(initial.stop, RootStop.ZERO)
        self.assertEqual(initial.iterations, 0)
        found = newton_raphson("x-2", 1)
        self.assertIs(found.stop, RootStop.ZERO)
        self.assertEqual(found.iterations, 1)
        self.assertEqual(found.root, 2)

    def test_failed_steps_preserve_the_last_valid_approximation(self):
        stalled = newton_raphson("x^3 - 3*x + 3", 0)
        self.assertIs(stalled.stop, RootStop.ZERO_DERIVATIVE)
        self.assertEqual((stalled.iterations, stalled.root, stalled.value), (1, 1, 1))
        self.assertFalse(stalled.converged)

        for expression, x0, expected in (
            ("sqrt(x)+1", 1, RootStop.EVALUATION_ERROR),
            ("abs(x)+1", 0, RootStop.EVALUATION_ERROR),
            ("1e-309*x+1", 0, RootStop.NONFINITE_STEP),
            ("(x-1)*1e30+1", 1, RootStop.STAGNATION),
        ):
            with self.subTest(expression=expression):
                result = newton_raphson(expression, x0)
                self.assertIs(result.stop, expected)
                self.assertEqual(result.iterations, 0)
                self.assertEqual(result.root, x0)

    def test_invalid_initial_inputs(self):
        for x0, tolerance, max_iterations in ((float("inf"), 1, 10), (1, 0, 10), (1, 1, True)):
            with self.subTest(x0=x0, tolerance=tolerance, max_iterations=max_iterations):
                with self.assertRaises(RootInputError):
                    newton_raphson(self.example, x0, tolerance, max_iterations=max_iterations)
