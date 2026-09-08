"""
Is this matrix in echelon form? What does it reduce to? Where are its pivots?

The page for the definitions themselves. It takes a matrix as it stands, checks
the five numbered properties one by one and marks the leading entries; then it
reduces it, step by step, and points at the pivot positions the reduced form
puts on show.

The reduction is not decoration. A pivot position is defined as a place holding
a leading entry once the matrix is in reduced echelon form, so answering "where
are the pivots" means reducing, and a page that reduced without showing the work
would be asking to be taken on trust.

The Spanish for the five properties lives here and not in `ui/presentation.py`
because no other front end says it: the terminal program answers a different
assignment. The day one does, the wording moves there, which is exactly what
happened to the classification.
"""

from typing import Any

import customtkinter as ctk

from core.echelon import ECHELON, REDUCED, Form, analyse
from core.elimination import Elimination, to_rref
from core.matrix import Matrix
from core.scalar import format_scalar

from .. import theme
from ..entry import UNREADABLE, SystemInput
from ..widgets import (
    Card,
    Chip,
    ErrorBanner,
    MatrixDisplay,
    PageHeader,
    PrimaryButton,
    SectionTitle,
    StepWalker,
)

# The five properties, worded as the course words them and numbered as it
# numbers them: the first three make an echelon form, the last two a reduced one.
PROPERTIES = {
    1: "Todas las filas distintas de cero están arriba de las filas de ceros.",
    2: "La entrada principal de cada fila está en una columna a la derecha de la\n"
       "entrada principal de la fila superior.",
    3: "En una columna, todas las entradas debajo de la entrada principal son ceros.",
    4: "La entrada principal de cada fila distinta de cero es 1.",
    5: "Cada entrada principal 1 es la única entrada distinta de cero en su columna.",
}

# Why a property failed, said by pointing at the entry that breaks it.
FAILURES = {
    1: "La fila {row} no es de ceros y está debajo de una fila que sí lo es.",
    2: "La entrada principal de la fila {row} está en la columna {column}, que no\n"
       "queda a la derecha de la anterior.",
    3: "a_{row}{column} = {value}, y está debajo de una entrada principal.",
    4: "La entrada principal de la fila {row} vale {value}, no 1.",
    5: "a_{row}{column} = {value}, y comparte columna con una entrada principal.",
}

EXAMPLE = (("1", "-2", "1", "0"), ("0", "2", "-8", "8"), ("-4", "5", "9", "-9"))

class EchelonPage(ctk.CTkFrame):
    """The page that reads the form of a matrix, and then reduces it."""

    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._output: list[ctk.CTkBaseClass] = []
        self._bar: int | None = None

        PageHeader(
            self,
            "▧",
            "Formas Escalonadas",
            "Comprobar si una matriz está en forma escalonada, reducirla y localizar "
            "sus pivotes.",
        ).pack(anchor="w", pady=(0, 18))

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)

        self._input = SystemInput(
            inside,
            split=False,
            rows=3,
            cols=4,
            values=EXAMPLE,
            title="Matriz",
            on_change=self._clear_output,
        )
        self._input.pack(fill="x")

        self._error = ErrorBanner(inside)

        buttons = ctk.CTkFrame(inside, fg_color="transparent")
        buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(buttons, "Analizar  →", self._analyse).pack(side="right")
        self._error.appear_before(buttons)

    # ----- Reading the matrix -----

    def _analyse(self) -> None:
        self._clear_output()
        try:
            typed = self._input.read()
        except UNREADABLE as problem:
            self._error.show(str(problem))
            return

        self._error.hide()
        # A matrix typed cell by cell is a plain matrix and has no bar; one that
        # came from equations is augmented, and the bar goes after the unknowns.
        self._bar = typed.unknowns or None
        reduction = to_rref(typed.matrix)

        self._draw_form(analyse(typed.matrix))
        self._draw_reduction(reduction)
        self._draw_pivots(typed.matrix, reduction)

    # ----- The five properties -----

    def _draw_form(self, form: Form) -> None:
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        SectionTitle(inside, "Forma de la matriz").pack(fill="x", pady=(0, 14))

        verdicts = ctk.CTkFrame(inside, fg_color="transparent")
        verdicts.pack(anchor="w", pady=(0, 6))
        self._verdict(verdicts, "Forma escalonada", form.is_echelon)
        self._verdict(verdicts, "Forma escalonada reducida", form.is_reduced)

        ctk.CTkLabel(
            inside,
            text="Las entradas principales están marcadas en azul.",
            font=theme.font("small"),
            text_color=theme.MUTED,
        ).pack(anchor="w", pady=(8, 10))
        MatrixDisplay(
            inside, form.matrix, bar_after=self._bar, highlight=form.leading
        ).pack(anchor="w")

        properties = ctk.CTkFrame(inside, fg_color="transparent")
        properties.pack(fill="x", pady=(16, 0))
        for number in (*ECHELON, *REDUCED):
            self._property(properties, form, number)

    def _verdict(self, master: ctk.CTkFrame, text: str, holds: bool) -> None:
        """One of the two answers, coloured by itself so it reads at a glance."""
        Chip(
            master,
            f"{'✓' if holds else '✗'}  {text}",
            theme.GREEN if holds else theme.MUTED,
        ).pack(side="left", padx=(0, 8))

    def _property(self, master: ctk.CTkFrame, form: Form, number: int) -> None:
        """One numbered property: whether it holds, and where it broke if not."""
        condition = form.condition(number)
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            row,
            text=f"{'✓' if condition.holds else '✗'}  {number}.",
            width=34,
            anchor="w",
            font=theme.font("button"),
            text_color=theme.GREEN if condition.holds else theme.RED,
        ).pack(side="left", anchor="n")

        text = ctk.CTkFrame(row, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            text,
            text=PROPERTIES[number],
            font=theme.font("body"),
            text_color=theme.INK if condition.holds else theme.MUTED,
            justify="left",
            anchor="w",
        ).pack(anchor="w")

        if not condition.holds:
            value = (
                format_scalar(form.matrix.elem(condition.row, condition.column))
                if condition.column
                else ""
            )
            ctk.CTkLabel(
                text,
                text=FAILURES[number].format(
                    row=condition.row, column=condition.column, value=value
                ),
                font=theme.font("small"),
                text_color=theme.RED,
                justify="left",
                anchor="w",
            ).pack(anchor="w")

    # ----- Putting it into the reduced form -----

    def _draw_reduction(self, reduction: Elimination) -> None:
        """
        The walk to the reduced form, one elementary operation at a time.

        The same algorithm the elimination page runs, shown here because this
        page has to reduce anyway: the pivot positions it reports below are the
        leading entries of the matrix this walk ends on.
        """
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        counter = SectionTitle(inside, "Reducción a la forma escalonada reducida", " ")
        counter.pack(fill="x", pady=(0, 14))

        if reduction.log.is_empty():
            ctk.CTkLabel(
                inside,
                text=(
                    "No hizo falta ninguna operación: la matriz ya estaba en forma "
                    "escalonada reducida."
                ),
                font=theme.font("small"),
                text_color=theme.MUTED,
            ).pack(anchor="w", pady=(0, 12))

        StepWalker(
            inside,
            reduction.log,
            bar_after=self._bar,
            first_caption="Matriz inicial",
            on_step=lambda index, total: counter.set_badge(f"{index + 1} / {total}"),
        ).pack(fill="x")

    # ----- The pivots, which live in the reduced form -----

    def _draw_pivots(self, matrix: Matrix, reduction: Elimination) -> None:
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        SectionTitle(inside, "Posiciones y columnas pivote").pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            inside,
            text=(
                "Una posición pivote es un lugar de la matriz que en su forma escalonada "
                "reducida\nlleva una entrada principal, y una columna pivote es una "
                "columna que contiene una."
            ),
            font=theme.font("small"),
            text_color=theme.MUTED,
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        positions = reduction.pivots
        columns = [column for _row, column in positions]

        chips = ctk.CTkFrame(inside, fg_color="transparent")
        chips.pack(anchor="w", pady=(0, 14))
        Chip(chips, f"columnas pivote: {_listed(columns)}").pack(side="left", padx=(0, 8))
        free = [
            column for column in range(1, matrix.cols + 1) if column not in set(columns)
        ]
        if free:
            Chip(chips, f"columnas sin pivote: {_listed(free)}", theme.MUTED).pack(
                side="left"
            )

        both = ctk.CTkFrame(inside, fg_color="transparent")
        both.pack(anchor="w")
        self._marked(both, "La matriz, con sus posiciones pivote", matrix, positions)
        self._marked(
            both, "Su forma escalonada reducida", reduction.result, positions, column=1
        )

    def _marked(
        self,
        master: ctk.CTkFrame,
        caption: str,
        matrix: Matrix,
        positions: tuple[tuple[int, int], ...],
        column: int = 0,
    ) -> None:
        """One matrix with the pivot positions picked out, under its own caption."""
        holder = ctk.CTkFrame(master, fg_color="transparent")
        holder.grid(row=0, column=column, sticky="nw", padx=(0, 40))
        ctk.CTkLabel(
            holder,
            text=caption.upper(),
            font=theme.font("label"),
            text_color=theme.MUTED,
        ).pack(anchor="w", pady=(0, 8))
        MatrixDisplay(holder, matrix, bar_after=self._bar, highlight=positions).pack(
            anchor="w"
        )

    # ----- Housekeeping -----

    def _add_card(self) -> Card:
        card = Card(self)
        card.pack(fill="x", pady=(16, 0))
        self._output.append(card)
        return card

    def _clear_output(self) -> None:
        """A verdict about a matrix stops meaning anything once it is retyped."""
        for card in self._output:
            card.destroy()
        self._output = []

def _listed(columns: list[int]) -> str:
    """`1, 3, 5`, or the word for none of them."""
    return ", ".join(str(column) for column in columns) if columns else "ninguna"
