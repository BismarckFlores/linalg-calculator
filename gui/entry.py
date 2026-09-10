"""
The two ways a matrix is handed over, in one place.

Both pages of this window ask for the same thing in the same two ways — a grid
of numbers, or the system written out as equations — so the card that asks lives
here instead of twice. What comes back is a `Typed`: the matrix, the names of
the unknowns when anything named them, and how many of its columns are
coefficients rather than constants.

The Spanish for what cannot be read lives here for the same reason. It is the
wording `ui/prompts.py` uses in the terminal, plus the number of the line, which
the terminal never needs because it has just asked for that one equation and the
window has all of them on screen at once.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import customtkinter as ctk

from core.equations import (
    Equation,
    EquationError,
    MissingEquals,
    UnreadableTerm,
    parse_equation,
    to_augmented,
    unknown_names,
)
from core.matrix import Matrix

from . import theme
from .widgets import SIZE_LIMIT, CellError, MatrixEntryGrid, SegmentedControl

COEFFICIENTS = "Coeficientes"
EQUATIONS = "Ecuaciones"

EQUATION_HELP = (
    "Una ecuación por línea. Por ejemplo:  2x + 3y - z = 5   o   2x = 3y + 1\n"
    "Se admiten enteros, decimales (2.5 o 2,5) y fracciones (1/3)."
)

EXAMPLE_SYSTEM = "x - 2y + z = 0\n2y - 8z = 8\n-4x + 5y + 9z = -9"

@dataclass(frozen=True)
class Typed:
    """
    What somebody handed over, whichever way they wrote it.

    `unknowns` is how many columns hold coefficients, so `unknowns` is where the
    bar of an augmented matrix goes. It is 0 for a plain matrix typed cell by
    cell, which is not augmented and has no bar. `names` is empty unless the
    equations said what the unknowns are called.
    """

    matrix: Matrix
    names: list[str] = field(default_factory=list)
    unknowns: int = 0

class SystemInput(ctk.CTkFrame):
    """
    The pill, the grids and the text box: everything above the Calcular button.

    `split` is the difference between the two pages. A page solving `A x = b`
    wants A and b in separate grids, with b following A row for row; a page
    reading the form of a matrix wants one grid and no b at all. Typed
    equations produce an augmented matrix either way, because that is what a
    system written out is.
    """

    def __init__(
        self,
        master: Any,
        split: bool,
        rows: int = 3,
        cols: int = 3,
        values: Sequence[Sequence[str]] = (),
        constants: Sequence[Sequence[str]] = (),
        title: str = "Matriz",
        example: str = EXAMPLE_SYSTEM,
        on_change: Callable[[], None] | None = None,
        augmentable: bool = False,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._split = split
        self._way_in = COEFFICIENTS
        self._on_change = on_change

        SegmentedControl(self, (COEFFICIENTS, EQUATIONS), self._choose_way_in).pack(
            anchor="w", pady=(0, 18)
        )

        self._grids = ctk.CTkFrame(self, fg_color="transparent")
        self._grids.pack(fill="x")
        self._a = MatrixEntryGrid(
            self._grids,
            "Matriz A" if split else title,
            rows,
            cols,
            values=values,
            on_change=self._changed,
            on_resize=self._a_resized,
        )
        self._a.grid(row=0, column=0, sticky="nw", padx=(0, 40))

        self._b: MatrixEntryGrid | None = None
        if split:
            self._b = MatrixEntryGrid(
                self._grids,
                "Vector b",
                rows,
                1,
                values=constants,
                resizable_cols=False,
                on_change=self._changed,
                on_resize=self._b_resized,
            )
            self._b.grid(row=0, column=1, sticky="nw")

        # One grid says nothing about whether its last column is b. Somebody has
        # to, or a 3x5 augmented matrix reads as five unknowns instead of four.
        self._augmented: ctk.CTkSwitch | None = None
        if augmentable and not split:
            self._augmented = ctk.CTkSwitch(
                self._grids,
                text="Es una matriz aumentada  [ A | b ]",
                font=theme.font("body"),
                text_color=theme.INK,
                progress_color=theme.ACCENT,
                command=self._changed,
            )
            self._augmented.grid(row=1, column=0, columnspan=2, sticky="w", pady=(14, 0))

        self._typed = self._build_equations(example)

    def _build_equations(self, example: str) -> ctk.CTkFrame:
        """The system written out, one equation per line, the way it is on paper."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkLabel(
            frame, text="ECUACIONES", font=theme.font("label"), text_color=theme.MUTED
        ).pack(anchor="w", pady=(0, 8))

        self._lines = ctk.CTkTextbox(
            frame,
            height=150,
            corner_radius=12,
            fg_color=theme.FIELD,
            border_width=1,
            border_color=theme.BORDER,
            # CTkTextbox annotates text_color as a single colour while accepting
            # the same (light, dark) pair as everything else, and honouring it.
            text_color=theme.INK,  # type: ignore[arg-type]
            font=theme.font("mono"),
            wrap="none",
        )
        self._lines.insert("1.0", example)
        self._lines.bind("<KeyRelease>", lambda _event: self._retyped())
        self._lines.pack(fill="x")

        ctk.CTkLabel(
            frame,
            text=EQUATION_HELP,
            font=theme.font("small"),
            text_color=theme.MUTED,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(8, 0))

        # Filled in once the equations have been read, never before: the list of
        # unknowns is a proof of what was understood, so it has to be earned.
        self._found = ctk.CTkLabel(
            frame, text="", font=theme.font("small"), text_color=theme.ACCENT, anchor="w"
        )
        return frame

    # ----- Swapping one way in for the other -----

    def _choose_way_in(self, way_in: str) -> None:
        """Swap the grids for the text box, or back. Each keeps what was typed."""
        self._way_in = way_in
        if way_in == EQUATIONS:
            self._grids.pack_forget()
            self._typed.pack(fill="x")
        else:
            self._typed.pack_forget()
            self._grids.pack(fill="x")
        self._changed()

    def _retyped(self) -> None:
        """A changed equation invalidates the unknowns that were read from it."""
        self._found.pack_forget()
        self._changed()

    def _changed(self) -> None:
        if self._on_change is not None:
            self._on_change()

    def _a_resized(self, rows: int, _cols: int) -> None:
        """One equation is one row of A and one entry of b: they cannot drift."""
        if self._b is not None:
            self._b.set_size(rows, 1)
        self._changed()

    def _b_resized(self, rows: int, _cols: int) -> None:
        self._a.set_size(rows, self._a.size()[1])
        self._changed()

    # ----- Reading it back -----

    def read(self) -> Typed:
        """
        The matrix, and the names of the unknowns when there are any.

        Only typed equations know what the unknowns are called. Numbers in a
        grid never say, so that route hands back an empty list and
        `ui/presentation.py` falls back to x, y, z, w.
        """
        if self._way_in == EQUATIONS:
            return self._read_equations()
        if self._b is not None:
            return Typed(self._a.matrix().augment(self._b.matrix()), [], self._a.size()[1])
        matrix = self._a.matrix()
        if self._augmented is not None and self._augmented.get():
            if matrix.cols < 2:
                raise ValueError(
                    "Una matriz aumentada necesita al menos una columna de "
                    "coeficientes además de la de los términos independientes."
                )
            return Typed(matrix, [], matrix.cols - 1)
        return Typed(matrix)

    def _read_equations(self) -> Typed:
        """
        Every non-blank line parsed, or a Spanish sentence about the first that
        was not.

        `core/equations.py` raises one exception per kind of mistake and says
        nothing to anybody; the wording is decided here, exactly as
        `ui/prompts.py` decides it for the terminal.
        """
        lines = [line.strip() for line in self._lines.get("1.0", "end").splitlines()]
        lines = [line for line in lines if line]

        if not lines:
            raise ValueError("Escribe al menos una ecuación.")
        if len(lines) > SIZE_LIMIT:
            raise ValueError(f"Son {len(lines)} ecuaciones y el máximo es {SIZE_LIMIT}.")

        equations: list[Equation] = []
        for number, text in enumerate(lines, start=1):
            try:
                equations.append(parse_equation(text))
            except MissingEquals:
                raise ValueError(
                    f"A la ecuación {number} le falta el '='. "
                    "Una ecuación se escribe como  2x + 3y = 5"
                ) from None
            except UnreadableTerm as problem:
                raise ValueError(
                    f"En la ecuación {number} no entiendo la parte "
                    f"'{problem.text}'. Revísala."
                ) from None
            except EquationError:
                raise ValueError(
                    f"No pude leer la ecuación {number}. Escríbela otra vez."
                ) from None

        names = unknown_names(equations)
        if not names:
            raise ValueError("Ninguna de las ecuaciones tiene incógnitas.")
        if len(names) > SIZE_LIMIT:
            raise ValueError(f"Son {len(names)} incógnitas y el máximo es {SIZE_LIMIT}.")

        self._found.configure(
            text=f"Incógnitas encontradas ({len(names)}): {', '.join(names)}"
        )
        self._found.pack(anchor="w", pady=(10, 0))
        return Typed(to_augmented(equations, names), names, len(names))

# Anything a page has to catch when it reads what was typed.
UNREADABLE = (CellError, ValueError)
