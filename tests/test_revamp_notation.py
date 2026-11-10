import unittest
from fractions import Fraction

from core.equations import parse_equation
from core.matrix import Matrix
from core.root_bracket import read_root_number
from core.vectors import parse_vector
from revamp_poc.math_notation import from_ascii, matrix_rows, to_latex


class MathNotationTests(unittest.TestCase):
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
            r"\begin{pmatrix}\frac{1}{2}&2\\3&4\end{pmatrix}",
        )
        self.assertEqual(to_latex("1/2", "matrix", paste=True), r"\frac{1}{2}")
        with self.assertRaises(ValueError):
            matrix_rows("1;2;3\n4;5;6")

    def test_vector_and_bisection_parameter_keep_their_values(self):
        vector = from_ascii("1, -2, -(1)/(2)", "vector")
        self.assertEqual(parse_vector(vector), (Fraction(1), Fraction(-2), Fraction(-1, 2)))
        self.assertEqual(read_root_number(from_ascii("(4)/(2)", "number")), 2.0)
        self.assertEqual(to_latex("1e-5", "number"), r"1\mathrm{e}-5")
