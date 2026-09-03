"""
Solving A x = b, by Gaussian elimination or by Gauss-Jordan.

The two methods share this page because they share the walk: `to_ref` stops at
the staircase, `to_rref` keeps going and clears above every pivot as well.
Which one was used changes the step by step and the last matrix; it does not
change the classification, which counts pivots, nor the values, which the two
paths agree on exactly because nothing is ever rounded.

Not a line of the wording is decided here. `ui/presentation.py` writes the
sentences for the terminal and the window alike; this page arranges them.
"""

import re
from dataclasses import replace
from typing import Any

import customtkinter as ctk

from core.elimination import Elimination, to_rref
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
from core.scalar import format_scalar
from core.systems import Solution, SystemKind, solve
from core.verification import verify
from ui.presentation import (
    SUBSCRIPTS,
    describe,
    pretty_label,
    render_equations,
    render_substitutions,
    render_values,
    render_verification,
    unknown_name,
)

from .. import theme
from ..widgets import (
    SIZE_LIMIT,
    Card,
    CellError,
    Chip,
    ErrorBanner,
    MatrixDisplay,
    MatrixEntryGrid,
    MonoBlock,
    PageHeader,
    PrimaryButton,
    SectionTitle,
    SegmentedControl,
)

GAUSS = "Gauss"
JORDAN = "Gauss-Jordan"

# The two ways a system can be handed over, the same two the terminal offers.
COEFFICIENTS = "Coeficientes"
EQUATIONS = "Ecuaciones"

EQUATION_HELP = (
    "Una ecuación por línea. Por ejemplo:  2x + 3y - z = 5   o   2x = 3y + 1\n"
    "Se admiten enteros, decimales (2.5 o 2,5) y fracciones (1/3)."
)

EXAMPLE_SYSTEM = "x - 2y + z = 0\n2y - 8z = 8\n-4x + 5y + 9z = -9"

# One page and one title; only the line underneath changes with the method,
# because where the walk stops is the whole difference between the two.
SUBTITLES = {
    GAUSS: "Resolver A x = b · forma escalonada por operaciones elementales de fila.",
    JORDAN: "Resolver A x = b · forma escalonada reducida, con cada pivote solo en su columna.",
}

# A colour per classification, so the answer is legible before it is read.
KIND_COLORS = {
    SystemKind.UNIQUE: theme.GREEN,
    SystemKind.INFINITE: theme.ORANGE,
    SystemKind.INCONSISTENT: theme.RED,
}

# A row named at the start of a line, inside a block already lined up in columns.
_ROW_TAG = re.compile(r"f_(\d+):")

def _typographic(block: str) -> str:
    """
    `f_2:` written `f₂:` without moving anything that was lined up under it.

    `ui/presentation.py` lays these blocks out in columns, counting characters,
    and a subscript costs one character less than `f_2` does. The space the
    underscore used to take is put back after the colon, so the lines that were
    indented to match still match.
    """
    return _ROW_TAG.sub(lambda match: f"f{match[1].translate(SUBSCRIPTS)}: ", block)

class GaussPage(ctk.CTkFrame):
    """The page that solves a system and walks through how it was solved."""

    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._method = GAUSS
        self._way_in = COEFFICIENTS
        self._names: list[str] = []
        self._output: list[ctk.CTkBaseClass] = []
        self._elimination: Elimination | None = None
        self._index = 0
        self._unknowns = 0

        self._header = PageHeader(self, "▦", "Eliminación Gaussiana", SUBTITLES[GAUSS])
        self._header.pack(anchor="w", pady=(0, 18))

        self._methods = SegmentedControl(self, (GAUSS, JORDAN), self._choose_method)
        self._methods.pack(anchor="w", pady=(0, 16))

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)

        SegmentedControl(inside, (COEFFICIENTS, EQUATIONS), self._choose_way_in).pack(
            anchor="w", pady=(0, 18)
        )

        self._grids = self._build_grids(inside)
        self._grids.pack(fill="x")
        self._typed = self._build_equations(inside)

        self._error = ErrorBanner(inside)

        self._buttons = ctk.CTkFrame(inside, fg_color="transparent")
        self._buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(self._buttons, "Calcular  →", self._calculate).pack(side="right")
        self._error.appear_before(self._buttons)

    def _build_grids(self, master: Any) -> ctk.CTkFrame:
        """The coefficients typed one cell at a time: A beside b."""
        frame = ctk.CTkFrame(master, fg_color="transparent")
        self._a = MatrixEntryGrid(
            frame,
            "Matriz A",
            3,
            3,
            values=(("1", "-2", "1"), ("0", "2", "-8"), ("-4", "5", "9")),
            on_change=self._clear_output,
            on_resize=self._a_resized,
        )
        self._a.grid(row=0, column=0, sticky="nw", padx=(0, 40))
        self._b = MatrixEntryGrid(
            frame,
            "Vector b",
            3,
            1,
            values=(("0",), ("8",), ("-9",)),
            resizable_cols=False,
            on_change=self._clear_output,
            on_resize=self._b_resized,
        )
        self._b.grid(row=0, column=1, sticky="nw")
        return frame

    def _build_equations(self, master: Any) -> ctk.CTkFrame:
        """The system written out, one equation per line, the way it is on paper."""
        frame = ctk.CTkFrame(master, fg_color="transparent")
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
        self._lines.insert("1.0", EXAMPLE_SYSTEM)
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

    # ----- The two methods, the two ways in, and the sizes that follow -----

    def _choose_way_in(self, way_in: str) -> None:
        """Swap the grids for the text box, or back. Each keeps what was typed."""
        self._way_in = way_in
        self._clear_output()
        self._error.hide()
        if way_in == EQUATIONS:
            self._grids.pack_forget()
            self._typed.pack(fill="x", before=self._buttons)
        else:
            self._typed.pack_forget()
            self._grids.pack(fill="x", before=self._buttons)

    def _retyped(self) -> None:
        """A changed equation invalidates the unknowns that were read from it."""
        self._found.pack_forget()
        self._clear_output()

    def _choose_method(self, method: str) -> None:
        self._method = method
        self._header.set_subtitle(SUBTITLES[method])
        self._clear_output()

    def _a_resized(self, rows: int, _cols: int) -> None:
        """One equation is one row of A and one entry of b: they cannot drift."""
        self._b.set_size(rows, 1)
        self._clear_output()

    def _b_resized(self, rows: int, _cols: int) -> None:
        cols = self._a.size()[1]
        self._a.set_size(rows, cols)
        self._clear_output()

    # ----- Solving -----

    def _calculate(self) -> None:
        self._clear_output()
        try:
            augmented, names = self._read_system()
        except (CellError, EquationError, ValueError) as problem:
            self._error.show(str(problem))
            return

        self._error.hide()
        self._names = names
        solution = solve(augmented)
        self._unknowns = solution.unknowns
        self._elimination = (
            to_rref(augmented) if self._method == JORDAN else solution.reduction
        )
        self._index = 0

        # The same order the assignment numbers its requirements in: the walk,
        # the equivalent system, the classification, the solution, the check.
        self._draw_steps()
        self._draw_equivalent(solution)
        self._draw_result(solution)
        if solution.kind is SystemKind.UNIQUE:
            if self._method == GAUSS:
                self._draw_substitutions(solution)
            self._draw_verification(solution)

    # ----- Reading the system, whichever way it was written -----

    def _read_system(self) -> tuple[Matrix, list[str]]:
        """
        The augmented matrix, and the names of the unknowns when there are any.

        Only the typed equations know what the unknowns are called. Coefficients
        in a grid never say, so that route hands back an empty list and
        `ui/presentation.py` falls back to x, y, z, w.
        """
        if self._way_in == EQUATIONS:
            return self._read_equations()
        return self._a.matrix().augment(self._b.matrix()), []

    def _read_equations(self) -> tuple[Matrix, list[str]]:
        """
        Every non-blank line parsed, or a Spanish sentence about the first that
        was not.

        `core/equations.py` raises one exception per kind of mistake and says
        nothing to anybody; the wording is decided here, exactly as
        `ui/prompts.py` decides it for the terminal. What the window has to add
        is the number of the line, because every equation is on screen at once
        and nothing else would say which one is meant.
        """
        lines = [line.strip() for line in self._lines.get("1.0", "end").splitlines()]
        lines = [line for line in lines if line]

        if not lines:
            raise ValueError("Escribe al menos una ecuación.")
        if len(lines) > SIZE_LIMIT:
            raise ValueError(
                f"Son {len(lines)} ecuaciones y el máximo es {SIZE_LIMIT}."
            )

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
        return to_augmented(equations, names), names

    # ----- The step by step -----

    def _draw_steps(self) -> None:
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        self._counter = SectionTitle(inside, "Paso a paso", " ")
        self._counter.pack(fill="x", pady=(0, 14))

        self._operation = ctk.CTkLabel(
            inside,
            text="",
            font=theme.font("mono"),
            text_color=theme.INK,
            fg_color=theme.FIELD,
            corner_radius=12,
            anchor="w",
            padx=16,
            pady=12,
        )
        self._operation.pack(fill="x")

        self._matrix_holder = ctk.CTkFrame(inside, fg_color="transparent")
        self._matrix_holder.pack(anchor="w", pady=(14, 0))

        self._dots = ctk.CTkFrame(inside, fg_color="transparent")
        self._dots.pack(pady=(14, 0))

        navigation = ctk.CTkFrame(inside, fg_color="transparent")
        navigation.pack(fill="x", pady=(14, 0))
        self._previous = self._link(navigation, "‹  Anterior", -1)
        self._previous.pack(side="left")
        self._next = self._link(navigation, "Siguiente  ›", 1)
        self._next.pack(side="right")

        self._show_step()

    def _link(self, master: Any, text: str, delta: int) -> ctk.CTkButton:
        return ctk.CTkButton(
            master,
            text=text,
            width=100,
            height=30,
            corner_radius=15,
            fg_color="transparent",
            hover_color=theme.FIELD,
            text_color=theme.ACCENT,
            text_color_disabled=theme.FAINT,
            font=theme.font("button"),
            command=lambda: self._move(delta),
        )

    def _move(self, delta: int) -> None:
        self._index = max(0, min(self._total() - 1, self._index + delta))
        self._show_step()

    def _go(self, index: int) -> None:
        self._index = index
        self._show_step()

    def _total(self) -> int:
        """The starting matrix counts as a step: it is what the operations act on."""
        assert self._elimination is not None
        return len(self._elimination.log) + 1

    def _show_step(self) -> None:
        assert self._elimination is not None
        log = self._elimination.log
        total = self._total()

        self._counter.set_badge(f"{self._index + 1} / {total}")
        self._operation.configure(
            text="Matriz aumentada  [ A | b ]"
            if self._index == 0
            else pretty_label(log[self._index - 1].label)
        )

        for widget in self._matrix_holder.winfo_children():
            widget.destroy()
        MatrixDisplay(
            self._matrix_holder, log.snapshot(self._index), bar_after=self._unknowns
        ).pack(anchor="w")

        self._draw_dots(total)
        self._previous.configure(state="normal" if self._index > 0 else "disabled")
        self._next.configure(state="normal" if self._index < total - 1 else "disabled")

    def _draw_dots(self, total: int) -> None:
        """One dot per step, while there are few enough for it to help."""
        for widget in self._dots.winfo_children():
            widget.destroy()
        if total > 20:
            return

        for index in range(total):
            if index == self._index:
                glyph, colour = "◉", theme.ACCENT
            elif index < self._index:
                glyph, colour = "✓", theme.GREEN
            else:
                glyph, colour = "○", theme.FAINT
            ctk.CTkButton(
                self._dots,
                text=glyph,
                width=22,
                height=22,
                corner_radius=11,
                fg_color="transparent",
                hover_color=theme.FIELD,
                text_color=colour,
                font=theme.font("body"),
                command=lambda index=index: self._go(index),
            ).pack(side="left", padx=1)

    # ----- The answer -----

    def _draw_equivalent(self, solution: Solution) -> None:
        """
        The matrix the walk ended on, read back as the system it stands for.

        `render_equations` reads whichever matrix the solution's reduction ended
        on, and in Gauss-Jordan that is not the matrix `solve` walked to. Handing
        it a copy of the solution pointed at this page's own elimination is what
        keeps the equations and the step by step showing the same thing.
        """
        assert self._elimination is not None
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        SectionTitle(inside, "Sistema equivalente").pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            inside,
            text=(
                "La matriz escalonada reducida, leída otra vez como ecuaciones:"
                if self._method == JORDAN
                else "La matriz escalonada, leída otra vez como ecuaciones:"
            ),
            font=theme.font("small"),
            text_color=theme.MUTED,
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        walked = replace(solution, reduction=self._elimination)
        MonoBlock(inside, _typographic(render_equations(walked, self._names))).pack(anchor="w")

    def _draw_result(self, solution: Solution) -> None:
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        SectionTitle(inside, "Resultado").pack(fill="x", pady=(0, 14))

        ranks = ctk.CTkFrame(inside, fg_color="transparent")
        ranks.pack(anchor="w", pady=(0, 10))
        for text in (
            f"rango(A) = {solution.coefficient_rank}",
            f"rango(A|b) = {solution.rank}",
            f"incógnitas = {solution.unknowns}",
        ):
            Chip(ranks, text, theme.MUTED).pack(side="left", padx=(0, 8))

        columns = ctk.CTkFrame(inside, fg_color="transparent")
        columns.pack(anchor="w", pady=(0, 14))
        Chip(columns, f"columnas pivote: {self._pivot_columns(solution)}").pack(
            side="left", padx=(0, 8)
        )
        if solution.free_columns:
            free = ", ".join(str(column) for column in solution.free_columns)
            Chip(columns, f"columnas libres: {free}", theme.MUTED).pack(side="left")

        headline = ctk.CTkFrame(inside, fg_color="transparent")
        headline.pack(anchor="w")
        ctk.CTkLabel(
            headline,
            text="●",
            font=theme.font("body"),
            text_color=KIND_COLORS[solution.kind],
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            headline, text=describe(solution), font=theme.font("body"), text_color=theme.INK
        ).pack(side="left")

        if solution.kind is SystemKind.UNIQUE:
            values = ctk.CTkFrame(inside, fg_color="transparent")
            values.pack(anchor="w", pady=(14, 0))
            for column, value in enumerate(solution.values, start=1):
                Chip(
                    values,
                    f"✓  {unknown_name(column, self._names)} = {format_scalar(value)}",
                ).pack(side="left", padx=(0, 8))
            if solution.homogeneous:
                ctk.CTkLabel(
                    inside,
                    text="El sistema es homogéneo, y esta es su solución trivial.",
                    font=theme.font("small"),
                    text_color=theme.MUTED,
                ).pack(anchor="w", pady=(12, 0))
            elif self._method == JORDAN:
                ctk.CTkLabel(
                    inside,
                    text=(
                        "En la forma escalonada reducida cada pivote queda solo en su "
                        "columna, así que los valores se leen en la última columna."
                    ),
                    font=theme.font("small"),
                    text_color=theme.MUTED,
                    justify="left",
                    wraplength=560,
                ).pack(anchor="w", pady=(12, 0))
        else:
            # Prose, not a block lined up in columns: pretty_label can write
            # the row name in full here without pushing anything out of line.
            ctk.CTkLabel(
                inside,
                text=pretty_label(render_values(solution, self._names)),
                font=theme.font("body"),
                text_color=theme.MUTED,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(14, 0))
            # Requirement 7 still has an answer when there is nothing to check:
            # saying so beats a card that quietly fails to appear.
            ctk.CTkLabel(
                inside,
                text=(
                    "No hay una solución única que sustituir, así que no hay nada "
                    "que comprobar en el sistema original."
                ),
                font=theme.font("small"),
                text_color=theme.FAINT,
                justify="left",
                wraplength=560,
            ).pack(anchor="w", pady=(12, 0))

    def _pivot_columns(self, solution: Solution) -> str:
        """
        The columns of A that hold a pivot, which is what Gauss-Jordan is read
        off.

        Only the columns of A: a pivot can also land on the constants column,
        and that one is not a column of the system but the reason an
        inconsistent system is inconsistent. The classification already says so.
        """
        assert self._elimination is not None
        held = [
            column
            for _row, column in self._elimination.pivots
            if column <= solution.unknowns
        ]
        return ", ".join(str(column) for column in held) if held else "ninguna"

    def _draw_substitutions(self, solution: Solution) -> None:
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, "Despeje por sustitución hacia atrás").pack(fill="x", pady=(0, 14))
        MonoBlock(inside, _typographic(render_substitutions(solution, self._names))).pack(anchor="w")

    def _draw_verification(self, solution: Solution) -> None:
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, "Comprobación en el sistema original").pack(fill="x", pady=(0, 14))
        checked = verify(solution.coefficients, solution.constants, solution.values)
        MonoBlock(inside, render_verification(checked)).pack(anchor="w")

    # ----- Housekeeping -----

    def _add_card(self) -> Card:
        card = Card(self)
        card.pack(fill="x", pady=(16, 0))
        self._output.append(card)
        return card

    def _clear_output(self) -> None:
        """Everything below the input card stops being true as soon as it changes."""
        for card in self._output:
            card.destroy()
        self._output = []
        self._elimination = None
