"""
La matriz: un rectangulo de numeros exactos, y las operaciones que no necesitan
explicacion.

Aqui nadie escribe en un registro de pasos. Una operacion de fila devuelve una
matriz nueva y no dice nada de si misma; acordarse de la cadena es trabajo de
worksheet.Worksheet. Asi, una matriz usada para aritmetica normal no carga con
ningun apunte, y una matriz que se esta reduciendo no es un objeto distinto.

Los indices empiezan en 1 en elem, row y las operaciones de fila, porque es como
se escriben en papel: a_23 es elem(2, 3).
"""

from collections.abc import Sequence

from .scalar import NumberLike, Scalar, format_scalar, to_scalar

def _is_row(value: object) -> bool:
    """Una secuencia de valores, pero no un texto: str tambien es una secuencia."""
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))

class Matrix:
    """Un rectangulo de m x n numeros racionales exactos."""

    def __init__(self, data: Sequence[Sequence[NumberLike]]) -> None:
        """Se construye con una lista de filas: Matrix([[1, 2], [3, 4]]) es 2x2."""
        if not _is_row(data) or not all(_is_row(row) for row in data):
            raise ValueError("A matrix is built from a list of rows.")

        rows = [[to_scalar(value) for value in row] for row in data]
        if len({len(row) for row in rows}) > 1:
            widths = ", ".join(str(len(row)) for row in data)
            raise ValueError(f"Every row needs the same length, got {widths}.")

        self.data: list[list[Scalar]] = rows
        self.rows: int = len(rows)
        self.cols: int = len(rows[0]) if rows else 0


    # ----- Lectura -----

    def elem(self, i: int, j: int) -> Scalar:
        """El elemento a_ij, contando desde 1."""
        return self.data[i - 1][j - 1]

    def row(self, i: int) -> list[Scalar]:
        """La fila i como lista, contando desde 1."""
        return list(self.data[i - 1])

    def column(self, j: int) -> list[Scalar]:
        """La columna j como lista, contando desde 1."""
        return [row[j - 1] for row in self.data]

    def diagonal(self) -> list[Scalar]:
        """La diagonal principal, hasta donde llegue."""
        return [self.data[i][i] for i in range(min(self.rows, self.cols))]

    def is_square(self) -> bool:
        return self.rows == self.cols

    def is_zero_row(self, i: int) -> bool:
        """Si la fila i es toda ceros, que es la forma que toma una fila 0 = k."""
        return all(value == 0 for value in self.data[i - 1])

    def size(self) -> tuple[int, int]:
        return self.rows, self.cols

    # ----- Forma -----

    def transpose(self) -> "Matrix":
        """Las filas pasan a ser columnas."""
        return Matrix([[row[j] for row in self.data] for j in range(self.cols)])

    def augment(self, other: "Matrix") -> "Matrix":
        """Pega otra matriz a la derecha: [A | B], y mas adelante [A | I]."""
        if self.rows != other.rows:
            raise ValueError(
                f"Cannot augment: {self.rows} rows on the left, {other.rows} on the right."
            )
        return Matrix([left + right for left, right in zip(self.data, other.data)])

    def take_columns(self, first: int, last: int) -> "Matrix":
        """Las columnas de first a last, ambas incluidas y contando desde 1."""
        if not 1 <= first <= last <= self.cols:
            raise ValueError(f"Columns {first}..{last} fall outside a {self.cols}-wide matrix.")
        return Matrix([row[first - 1:last] for row in self.data])

    # ----- operaciones elementales por filas -----

    def swap_rows(self, i: int, j: int) -> "Matrix":
        """f_i <-> f_j"""
        rows = [list(row) for row in self.data]
        rows[i - 1], rows[j - 1] = rows[j - 1], rows[i - 1]
        return Matrix(rows)

    def scale_row(self, i: int, factor: NumberLike) -> "Matrix":
        """f_i -> k*f_i, con k distinto de cero: multiplicar por cero no tiene vuelta atras."""
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

    # ----- aritmetica -----

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
        """A * B si las dimensiones encajan, A * k si el otro es un numero."""
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
        """k * A se lee mejor que A * k, y significa lo mismo."""
        return self.__mul__(other)

    def __neg__(self) -> "Matrix":
        return self.__mul__(-1)

    def _require_same_size(self, other: "Matrix", verb: str) -> None:
        if self.size() != other.size():
            raise ValueError(
                f"Cannot be {verb}: A is {self.rows}x{self.cols} "
                f"and B is {other.rows}x{other.cols}."
            )

    # ----- construccion -----

    @classmethod
    def zero(cls, rows: int, cols: int) -> Matrix:
        """La matriz de ceros de tamano filas x columnas."""
        return cls([[0] * cols for _ in range(rows)])

    @classmethod
    def identity(cls, n: int) -> "Matrix":
        """La identidad I_n, con unos en la diagonal."""
        return cls([[1 if i == j else 0 for j in range(n)] for i in range(n)])

    @classmethod
    def column_vector(cls, values: Sequence[NumberLike]) -> "Matrix":
        """Una sola columna, que es como entra el vector b al sistema."""
        return cls([[value] for value in values])

    # ----- comparacion e impresion -----

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented
        return self.data == other.data

    def __str__(self) -> str:
        """Alineada segun el elemento mas ancho, para que las columnas cuadren siempre."""
        if not self.rows:
            return "[ ]"
        texts = [[format_scalar(value) for value in row] for row in self.data]
        width = max(len(text) for row in texts for text in row)
        return "\n".join(
            "[ " + "  ".join(text.rjust(width) for text in row) + " ]" for row in texts
        )

    def __repr__(self) -> str:
        return f"Matrix({[[format_scalar(v) for v in row] for row in self.data]})"
