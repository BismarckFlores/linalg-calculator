import unittest
from fractions import Fraction

from core.linear_algebra.handlers.matrix import Matrix
from core.linear_algebra.iterative import IterativeCriterion, IterativeMethod, IterativeStop, solve_iterative


class IterativeTests(unittest.TestCase):
    a = Matrix([[10, -1, 2, 0], [-1, 11, -1, 3], [2, -1, 10, -1], [0, 3, -1, 8]])
    b = (6, 25, -11, 15)

    def test_teacher_first_two_iterations(self):
        expected = (
            ((.6, 25 / 11, -1.1, 1.875), (1.047272727, 1.715909091, -.805227273, .885227273)),
            ((.6, 2.327272727, -.987272727, .878863636), (1.030181818, 2.036938017, -1.014456198, .984341219)),
        )
        for method, vectors in zip(IterativeMethod, expected):
            with self.subTest(method=method):
                result = solve_iterative(self.a, self.b, method=method, max_iterations=2)
                self.assertIs(result.stop, IterativeStop.LIMIT)
                self.assertTrue(result.strictly_dominant)
                for step, vector in zip(result.steps, vectors):
                    for value, reference in zip(step.values, vector):
                        self.assertAlmostEqual(float(value), reference, places=8)
                    self.assertEqual(step.error, max(abs(x-y) for x, y in zip(step.values, step.previous)))
                self.assertIsInstance(result.values[0], Fraction)

    def test_convergence_and_residual(self):
        for method in IterativeMethod:
            result = solve_iterative(self.a, self.b, method=method)
            self.assertIs(result.stop, IterativeStop.TOLERANCE)
            for value, exact in zip(result.values, (1, 2, -1, 1)):
                self.assertAlmostEqual(float(value), exact, places=4)
            self.assertLess(result.steps[-1].error, Fraction("0.0001"))
            self.assertGreater(result.residual, 0)

    def test_initial_solution_and_non_dominant_system(self):
        exact = solve_iterative(self.a, self.b, initial=(1, 2, -1, 1))
        self.assertIs(exact.stop, IterativeStop.EXACT)
        self.assertEqual(exact.steps, ())
        result = solve_iterative(Matrix([[1, 2], [0, 1]]), (3, 1))
        self.assertFalse(result.strictly_dominant)
        self.assertEqual(result.values, (1, 1))

    def test_invalid_inputs_and_divergence(self):
        for kwargs in (dict(tolerance=0), dict(tolerance=-1), dict(max_iterations=0),
                       dict(max_iterations=True), dict(initial=(0,))):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                solve_iterative(self.a, self.b, **kwargs)
        for a, b in ((Matrix([[0, 1], [1, 1]]), (1, 1)),
                     (Matrix([[1, 2]]), (1,)),
                     (self.a, (1,))):
            with self.assertRaises(ValueError):
                solve_iterative(a, b)
        result = solve_iterative(Matrix([[1, 2], [2, 1]]), (1, 1), max_iterations=5)
        self.assertIs(result.stop, IterativeStop.LIMIT)
        self.assertEqual(len(result.steps), 5)

    def test_pasted_divergent_system_preserves_error_at_iteration_50(self):
        a = Matrix([[4, 5, 6, 7], [1, -1, -1, 2], [0, 1, 1, 1], [-2, -1, 2, 2]])
        result = solve_iterative(a, (1, 2, 3, 4), method=IterativeMethod.GAUSS_SEIDEL)
        self.assertIs(result.stop, IterativeStop.LIMIT)
        self.assertEqual(result.steps[-1].index, 50)
        self.assertAlmostEqual(float(result.steps[-1].error) / 1e23, 1.924045223597, places=6)
        self.assertFalse(result.strictly_dominant)

    def test_residual_criterion_controls_stopping(self):
        result = solve_iterative(self.a, self.b, criterion=IterativeCriterion.RESIDUAL)
        self.assertIs(result.stop, IterativeStop.TOLERANCE)
        self.assertLess(result.steps[-1].residual, Fraction("0.0001"))
        self.assertGreaterEqual(result.steps[-2].residual, Fraction("0.0001"))
