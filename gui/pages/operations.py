"""
Aritmetica de matrices: A + B, A - B, A x B, k*A y la traspuesta.

Todo lo de esta pagina es una llamada a core/matrix.py. Lo unico que se decide
aqui es que tamanos pueden encontrarse, y esa comprobacion se repite a proposito
en vez de dejarsela al motor: Matrix lanza un error en ingles dirigido a quien
escribio el codigo, y la persona que esta delante de la ventana necesita una
frase en castellano que nombre los dos tamanos que no coincidieron.
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
    ResultsPage,
    SectionTitle,
    SegmentedControl,
)

# Cada operacion: el boton con el que se elige, y la linea que va debajo.
OPERATIONS = (
    ("A + B", "Suma de matrices, entrada por entrada."),
    ("A − B", "Resta de matrices, entrada por entrada."),
    ("A × B", "Producto de matrices: fila por columna."),
    ("k · A", "Cada entrada de A multiplicada por un mismo número."),
    ("Aᵀ", "La transpuesta: las filas de A pasan a ser sus columnas."),
)

NEEDS_B = ("A + B", "A − B", "A × B")

class OperationsPage(ResultsPage):
    """La pagina de aritmetica basica con matrices."""

    def __init__(self, master: Any) -> None:
        super().__init__(master)
        self._operation = OPERATIONS[0][0]

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
        self._scalar.bind("<KeyRelease>", lambda _event: self._clear_output())
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
            on_change=self._clear_output,
            on_resize=self._a_resized,
        )
        self._a.grid(row=0, column=0, sticky="nw", padx=(0, 40))
        self._b = MatrixEntryGrid(
            matrices,
            "Matriz B",
            2,
            2,
            values=(("5", "6"), ("7", "8")),
            on_change=self._clear_output,
        )
        self._b.grid(row=0, column=1, sticky="nw")

        self._error = ErrorBanner(inside)

        buttons = ctk.CTkFrame(inside, fg_color="transparent")
        buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(buttons, "Calcular  →", self._calculate).pack(side="right")
        self._error.appear_before(buttons)

    # ----- Eleccion de la operacion -----

    def _choose(self, operation: str) -> None:
        self._operation = operation
        self._clear_output()
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
        self._clear_output()

    def _fit_b(self) -> None:
        """
        B sigue a A: el mismo tamano para sumar, tantas filas como columnas tenga A
        para multiplicar.
        """
        rows, cols = self._a.size()
        _b_rows, b_cols = self._b.size()
        if self._operation in ("A + B", "A − B"):
            self._b.set_size(rows, cols)
        elif self._operation == "A × B":
            self._b.set_size(cols, b_cols)

    # ----- Calculo -----

    def _calculate(self) -> None:
        self._clear_output()
        try:
            result, caption = self._compute()
        except (CellError, ValueError) as problem:
            self._error.show(str(problem))
            return

        self._error.hide()
        self._show(result, caption)

    def _compute(self) -> tuple[Matrix, str]:
        """La operacion elegida, o una queja en castellano sobre los tamanos."""
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

    # ----- Presentacion del resultado -----

    def _show(self, matrix: Matrix, caption: str) -> None:
        inside = self._card(caption, f"Dimensión: {matrix.rows} × {matrix.cols}")
        MatrixDisplay(inside, matrix).pack(anchor="w")
