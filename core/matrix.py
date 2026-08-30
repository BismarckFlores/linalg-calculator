"""
The matrix: a rectangle of exact numbers, and the operations that need no
explaining.

Nothing here writes to a step log. A row operation returns a new matrix and says
nothing about itself; remembering the chain is `worksheet.Worksheet`'s job. That
way a matrix used for plain arithmetic carries no bookkeeping at all, and a
matrix being reduced is not a different kind of object.

Indices are 1-based through `elem`, `row` and the row operations, because that
is how they are written on paper: a_23 is `elem(2, 3)`.
"""

from collections.abc import Sequence

from .scalar import NumberLike, Scalar, format_scalar, to_scalar

def _is_row(value: object) -> bool:
    """A sequence of values, but not a string: str is a Sequence too."""
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))

class Matrix:
    """An m x n rectangle of exact rationals."""

    def __init__(self, data: Sequence[Sequence[NumberLike]]) -> None:
        """Build from a list of rows: Matrix([[1, 2], [3, 4]]) is 2x2."""
        if not _is_row(data) or not all(_is_row(row) for row in data):
            raise ValueError("A matrix is built from a list of rows.")

        rows = [[to_scalar(value) for value in row] for row in data]
        if len({len(row) for row in rows}) > 1:
            widths = ", ".join(str(len(row)) for row in data)
            raise ValueError(f"Every row needs the same lenght, got {widths}.")

        self.data: list[list[Scalar]] = rows
        self.rows: int = len(rows)
        self.cols: int = len(rows[0]) if rows else 0


    # ----- Reading -----

    def elem(self, i: int, j: int) -> Scalar:
        """The entry a_ij, counting from 1."""
        return self.data[i - 1][j - 1]

    def row(self, i: int) -> list[Scalar]:
        """Row i as a plain list, counting from 1."""
        return list(self.data[i - 1])

    def column(self, j: int) -> list[Scalar]:
        """Column j as a plain list, counting from 1."""
        return [row[j - 1] for row in self.data]

    def diagonal(self) -> list[Scalar]:
        """The main diagonal, as far as it reaches."""
        return [self.data[i][i] for i in range(min(self.rows, self.cols))]

    def is_squared(self) -> bool:
        return self.rows == self.cols

    def is_zero_row(self, i: int) -> bool:
        """Whether row i is entirely zeros: the shape a fibre of `0 = k` takes."""
        return all(value == 0 for value in self.data[i - 1])

    def size(self) -> tuple[int, int]:
        return self.rows, self.cols

    # ----- Shape -----

    def transpose(self) -> "Matrix":
        """Rows become columns."""
        return Matrix([[row[j] for row in self.data] for j in range(self.cols)])

    def augment(self, other: "Matrix") -> "Matrix":
        """Glue another matrix to the right: [A | B], and later [A | I]."""
        if self.rows != other.rows:
            raise ValueError(
                f"Cannot augment: {self.rows} rows on the left, {other.rows} on the right."
            )
        return Matrix([left + right for left, right in zip(self.data, other.data)])

    def take_columns(self, first: int, last: int) -> "Matrix":
        """Columns `first` to `last`, both included and counted from 1."""
        if not 1 <= first <= last <= self.cols:
            raise ValueError(f"Columns {first}..{last} fall outside a {self.cols}-wide matrix.")
        return Matrix([row[first - 1:last] for row in self.data])

    # ----- elemtary row operations -----

    def swap_rows(self, i: int, j: int) -> "Matrix":
        """f_i <-> f_j"""
        rows = [list(row) for row in self.data]
        rows[i - 1], rows[j - 1] = rows[j - 1], rows[i - 1]
        return Matrix(rows)

    def scale_row(self, i: int, factor: NumberLike) -> "Matrix":
        """f_i -> k*f_i, with k not zero: multiplying by zero is not reversible."""
        factor = to_scalar(factor)
        if factor == 0:
            raise ValueError("Scaling a row by zero is not an elementary operation.")
        rows = [list(row) for row in self.data]
        rows[i - 1] = [value * factor for value in rows[i - 1]]
        return Matrix(rows)

    def add_scaled_row(self, i: int, j: int, factor: NumberLike) -> "Matrix":
        """f_i -> f_i + k*f_j"""
        if i == j:
            raise ValueError("A row cannot be added to itself.")
        factor = to_scalar(factor)
        rows = [list(row) for row in self.data]
        rows[i - 1] = [
            value + factor * other for value, other in zip(rows[i - 1], rows[j - 1])
        ]
        return Matrix(rows)

    # ----- arithmetic -----

    def __add__(self, other: "Matrix") -> "Matrix":
        if not isinstance(other, Matrix):
            return NotImplemented
        self._require_same_size(other, "added")
        return Matrix([
            [a + b for a, b in zip(left, right)]
            for left, right in zip(self.data, other.data)
        ])

    def __sub__(self, other: "Matrix") -> "Matrix":
        if not isinstance(other, Matrix):
            return NotImplemented
        self._require_same_size(other, "subtracted")
        return Matrix([
            [a - b for a, b in zip(left, right)]
            for left, right in zip(self.data, other.data)
        ])

    def __mul__(self, other: "Matrix | NumberLike") -> "Matrix":
        """A * B if the shapes agree, A * k for a number."""
        if isinstance(other, Matrix):
            if self.cols != other.rows:
                raise ValueError(
                    f"Cannot multiply: A has {self.cols} columns and B has {other.rows} rows."
                )
            return Matrix([
                [
                    sum(
                        (row[k] * other.data[k][j] for k in range(self.cols)),
                        to_scalar(0),
                    )
                    for j in range(other.cols)
                ]
                for row in self.data
            ])

        if isinstance(other, (int, float, Scalar, str)) and not isinstance(other, bool):
            factor = to_scalar(other)
            return Matrix([[value * factor for value in row] for row in self.data])

        return NotImplemented

    def __rmul__(self, other: NumberLike) -> "Matrix":
        """k * A reads better than A * k, and means the same."""
        return self.__mul__(other)

    def __neg__(self) -> "Matrix":
        return self.__mul__(-1)

    def _require_same_size(self, other: "Matrix", verb: str) -> None:
        if self.size() != other.size():
            raise ValueError(
                f"Cannot be {verb}: A is {self.rows}x{self.cols} "
                f"and B is {other.rows}x{other.cols}."
            )

    # ----- building -----

    @classmethod
    def zero(cls, rows: int, cols: int) -> Matrix:
        """The rows x cols matriz of zeros."""
        return cls([[0] * cols for _ in range(rows)])

    @classmethod
    def identity(cls, n: int) -> "Matrix":
        """I_n, with ones down the diagonal."""
        return cls([[1 if i == j else 0 for j in range(n)] for i in range(n)])

    @classmethod
    def column_vector(cls, values: Sequence[NumberLike]) -> "Matrix":
        """A single column, which is how a vector b enters the system."""
        return cls([[value] for value in values])

    # ----- comparing and printing -----

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented
        return self.data == other.data

    def __str__(self) -> str:
        """Aligned on the widest entry, so the columns line up whatever they hold."""
        if not self.rows:
            return "[ ]"
        texts = [[format_scalar(value) for value in row] for row in self.data]
        width = max(len(text) for row in texts for text in row)
        return "\n".join(
            "[ " + "  ".join(text.rjust(width) for text in row) + " ]" for row in texts
        )

    def __repr__(self) -> str:
        return f"Matrix({[[format_scalar(v) for v in row] for row in self.data]})"