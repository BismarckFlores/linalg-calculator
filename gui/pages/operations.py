"""
Matrix arithmetic: A + B, A - B, A x B, k*A and the transpose.

Everything on this page is one call into `core/matrix.py`. The only work done
here is deciding which shapes are allowed to meet — and that check is repeated
rather than left to the engine on purpose: `Matrix` raises in English at
whoever wrote the code, and the person in front of the window needs a sentence
in Spanish naming the two sizes that did not agree.
"""

from typing import Any

import customtkinter as ctk

from core.matrix import Matrix
from core.scalar import format_scalar, to_scalar

from .. import theme
from ..widgets import (
    Card,
    CellError,
    ErrorBanner,
    MatrixDisplay,
    MatrixEntryGrid,
    PageHeader,
    PrimaryButton,
    SectionTitle,
    SegmentedControl,
)

# Every operation: the pill it is chosen by, and the line under the pills.
OPERATIONS = (
    ("A + B", "Suma de matrices, entrada por entrada."),
    ("A − B", "Resta de matrices, entrada por entrada."),
    ("A × B", "Producto de matrices: fila por columna."),
    ("k · A", "Cada entrada de A multiplicada por un mismo número."),
    ("Aᵀ", "La transpuesta: las filas de A pasan a ser sus columnas."),
)

NEEDS_B = ("A + B", "A − B", "A × B")

class OperationsPage(ctk.CTkFrame):
    """The page of basic matrix arithmetic."""

    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._operation = OPERATIONS[0][0]
        self._result: Card | None = None

        PageHeader(
            self,
            "⊞",
            "Operaciones Matriciales",
            "Suma, resta, producto de matrices, producto por un escalar y transpuesta.",
        ).pack(anchor="w", pady=(0, 18))

        SegmentedControl(
            self, [label for label, _description in OPERATIONS], self._choose
        ).pack(anchor="w")
        self._description = ctk.CTkLabel(
            self,
            text=OPERATIONS[0][1],
            font=theme.font("small"),
            text_color=theme.MUTED,
        )
        self._description.pack(anchor="w", pady=(8, 16))

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)

        self._scalar_row = ctk.CTkFrame(
            inside, fg_color=theme.FIELD, corner_radius=14
        )
        ctk.CTkLabel(
            self._scalar_row,
            text="Escalar (k)",
            font=theme.font("label"),
            text_color=theme.INK,
        ).pack(side="left", padx=(14, 10), pady=10)
        self._scalar = ctk.CTkEntry(
            self._scalar_row,
            width=70,
            height=32,
            corner_radius=theme.FIELD_RADIUS,
            fg_color=theme.CARD,
            border_width=1,
            border_color=theme.BORDER,
            text_color=theme.INK,
            font=theme.font("mono"),
            justify="center",
        )
        self._scalar.insert(0, "2")
        self._scalar.bind("<KeyRelease>", lambda _event: self._clear_result())
        self._scalar.pack(side="left", padx=(0, 14), pady=10)

        self._matrices = ctk.CTkFrame(inside, fg_color="transparent")
        self._matrices.pack(fill="x")
        matrices = self._matrices
        self._a = MatrixEntryGrid(
            matrices,
            "Matriz A",
            2,
            2,
            values=(("1", "2"), ("3", "4")),
            on_change=self._clear_result,
            on_resize=self._a_resized,
        )
        self._a.grid(row=0, column=0, sticky="nw", padx=(0, 40))
        self._b = MatrixEntryGrid(
            matrices,
            "Matriz B",
            2,
            2,
            values=(("5", "6"), ("7", "8")),
            on_change=self._clear_result,
        )
        self._b.grid(row=0, column=1, sticky="nw")

        self._error = ErrorBanner(inside)

        buttons = ctk.CTkFrame(inside, fg_color="transparent")
        buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(buttons, "Calcular  →", self._calculate).pack(side="right")
        self._error.appear_before(buttons)

    # ----- Choosing an operation -----

    def _choose(self, operation: str) -> None:
        self._operation = operation
        self._clear_result()
        self._error.hide()

        for label, description in OPERATIONS:
            if label == operation:
                self._description.configure(text=description)

        if operation == "k · A":
            self._scalar_row.pack(anchor="w", pady=(0, 20), before=self._matrices)
        else:
            self._scalar_row.pack_forget()

        if operation in NEEDS_B:
            self._b.grid()
            self._fit_b()
        else:
            self._b.grid_remove()

    def _a_resized(self, _rows: int, _cols: int) -> None:
        self._fit_b()
        self._clear_result()

    def _fit_b(self) -> None:
        """B follows A: the same size to add, as many rows as A has columns to multiply."""
        rows, cols = self._a.size()
        _b_rows, b_cols = self._b.size()
        if self._operation in ("A + B", "A − B"):
            self._b.set_size(rows, cols)
        elif self._operation == "A × B":
            self._b.set_size(cols, b_cols)

    # ----- Calculating -----

    def _calculate(self) -> None:
        self._clear_result()
        try:
            result, caption = self._compute()
        except (CellError, ValueError) as problem:
            self._error.show(str(problem))
            return

        self._error.hide()
        self._show(result, caption)

    def _compute(self) -> tuple[Matrix, str]:
        """The chosen operation, or a Spanish complaint about the sizes."""
        a = self._a.matrix()
        rows, cols = self._a.size()

        if self._operation == "Aᵀ":
            return a.transpose(), "Resultado  C = Aᵀ"

        if self._operation == "k · A":
            text = self._scalar.get().strip()
            try:
                factor = to_scalar(text or "1")
            except (ValueError, TypeError):
                raise ValueError(f"El escalar no es un número válido ('{text}').") from None
            return a * factor, f"Resultado  C = {format_scalar(factor)} · A"

        b = self._b.matrix()
        b_rows, b_cols = self._b.size()

        if self._operation in ("A + B", "A − B"):
            if (rows, cols) != (b_rows, b_cols):
                verb = "sumar" if self._operation == "A + B" else "restar"
                raise ValueError(
                    f"Para {verb}, A y B deben tener el mismo tamaño: "
                    f"A es {rows}×{cols} y B es {b_rows}×{b_cols}."
                )
            if self._operation == "A + B":
                return a + b, "Resultado  C = A + B"
            return a - b, "Resultado  C = A − B"

        if cols != b_rows:
            raise ValueError(
                f"Para multiplicar, las columnas de A ({cols}) deben ser tantas "
                f"como las filas de B ({b_rows})."
            )
        return a * b, "Resultado  C = A × B"

    # ----- Showing the result -----

    def _show(self, matrix: Matrix, caption: str) -> None:
        self._result = Card(self)
        self._result.pack(fill="x", pady=(16, 0))
        inside = ctk.CTkFrame(self._result, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        SectionTitle(inside, caption, f"Dimensión: {matrix.rows} × {matrix.cols}").pack(
            fill="x", pady=(0, 16)
        )
        MatrixDisplay(inside, matrix).pack(anchor="w")

    def _clear_result(self) -> None:
        """A result stops being true the moment anything is retyped."""
        if self._result is not None:
            self._result.destroy()
            self._result = None
