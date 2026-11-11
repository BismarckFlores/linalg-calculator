import unittest
from fractions import Fraction

from core.linear_algebra.handlers.equations import parse_equation
from core.linear_algebra.handlers.matrix import Matrix
from core.numerical_methods.handlers.root_bracket import read_root_number
from core.linear_algebra.vectors import parse_vector
from desktop.core.math_notation import from_ascii, matrix_rows, result_blocks, to_latex


class MathNotationTests(unittest.TestCase):
    def test_results_keep_matrix_dividers_and_math_in_steps(self):
        blocks = result_blocks(
            "f₂ → f₂ + 1/3 · f₁\n[ 1; -2/3; |; 4 ]\n[ 0; 1; |; 5 ]\n"
            "xₙ₊₁ = xₙ − f(xₙ) / f′(xₙ)\n"
            "f(x) ≈ 2.5 × 10⁻⁶\nTodas las ecuaciones se cumplen."
        )
        self.assertEqual([kind for kind, _ in blocks], ["latex", "augmented", "latex", "latex", "line"])
        self.assertIn(r"\frac{1}{3}", blocks[0][1])
        left, right = blocks[1][1]
        self.assertIn(r"\frac{2}{3}", left)
        self.assertIn(r"\vphantom{\frac{1}{1}}", right)
        self.assertIn(r"\frac{f(x_{n})}{f'(x_{n})}", blocks[2][1])
        self.assertIn(r"10^{-6}", blocks[3][1])

    def test_trigonometric_powers_render_without_confusing_inverse_and_reciprocal(self):
        self.assertEqual(
            to_latex("sin^(-1)(x)+cos^2(2x)", "function"),
            r"\arcsin\left(x\right)+\cos^{2}\left(2x\right)",
        )
        self.assertEqual(to_latex("sin(x)^(-1)", "function"), r"\sin\left(x\right)^{-1}")
        self.assertEqual(from_ascii("a r c s e c (x)", "function"), "arcsec(x)")

    def test_function_displays_log_base_and_absolute_bars(self):
        self.assertEqual(
            to_latex("log(2, abs(x-1))", "function"),
            r"\log_{2}\left(\left|x-1\right|\right)",
        )

    def test_function_displays_coefficients_by_juxtaposition(self):
        self.assertEqual(to_latex("x^4 - 5x^3 + 0.5x^2 - 11x + 10", "function"),
                         "x^{4}-5x^{3}+0.5x^{2}-11x+10")
        self.assertEqual(to_latex("2*3", "function"), r"2\cdot 3")

    def test_linear_coefficients_and_variable_names_survive_export(self):
        equation = from_ascii("((1)/(2))x_(12)+y=(3)/(5)", "equations")
        parsed = parse_equation(equation)
        self.assertEqual(parsed.terms, {"x_12": Fraction(1, 2), "y": Fraction(1)})
        self.assertEqual(parsed.constant, Fraction(3, 5))

    def test_matrix_cells_keep_decimal_comma_and_exact_fractions(self):
        exported = "0,5;(1)/(3)\n(2)/(-5);4"
        matrix = Matrix(matrix_rows(from_ascii(exported, "matrix")))
        self.assertEqual(matrix.row(1), [Fraction(1, 2), Fraction(1, 3)])
        self.assertEqual(matrix.row(2), [Fraction(-2, 5), Fraction(4)])

    def test_matrix_paste_preserves_its_shape(self):
        self.assertEqual(
            to_latex("1 / 2;2\n3;4", "matrix", paste=True),
            r"\begin{bmatrix}\frac{1}{2}&2\\3&4\end{bmatrix}",
        )
        self.assertEqual(to_latex("1/2", "matrix", paste=True), r"\frac{1}{2}")
        self.assertEqual(matrix_rows("1;2;3\n4;5;6"), [["1", "2", "3"], ["4", "5", "6"]])
        with self.assertRaises(ValueError):
            matrix_rows("1;2;3\n4;5")

    def test_vector_and_bisection_parameter_keep_their_values(self):
        vector = from_ascii("1, -2, -(1)/(2)", "vector")
        self.assertEqual(parse_vector(vector), (Fraction(1), Fraction(-2), Fraction(-1, 2)))
        self.assertEqual(read_root_number(from_ascii("(4)/(2)", "number")), 2.0)
        self.assertEqual(to_latex("1e-5", "number"), r"1\times 10^{-5}")
