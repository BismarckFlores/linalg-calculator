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
from core.parametric import General, general_solution
from core.scalar import format_factor, format_scalar
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
from ..entry import UNREADABLE, SystemInput
from ..widgets import (
    Card,
    Chip,
    ErrorBanner,
    MonoBlock,
    PageHeader,
    PrimaryButton,
    SectionTitle,
    SegmentedControl,
    StepWalker,
)

GAUSS = "Gauss"
JORDAN = "Gauss-Jordan"

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
        self._names: list[str] = []
        self._output: list[ctk.CTkBaseClass] = []
        self._elimination: Elimination | None = None
        self._unknowns = 0

        self._header = PageHeader(self, "▦", "Eliminación Gaussiana", SUBTITLES[GAUSS])
        self._header.pack(anchor="w", pady=(0, 18))

        self._methods = SegmentedControl(self, (GAUSS, JORDAN), self._choose_method)
        self._methods.pack(anchor="w", pady=(0, 16))

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)

        self._input = SystemInput(
            inside,
            split=True,
            values=(("1", "-2", "1"), ("0", "2", "-8"), ("-4", "5", "9")),
            constants=(("0",), ("8",), ("-9",)),
            on_change=self._clear_output,
        )
        self._input.pack(fill="x")

        self._error = ErrorBanner(inside)

        self._buttons = ctk.CTkFrame(inside, fg_color="transparent")
        self._buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(self._buttons, "Calcular  →", self._calculate).pack(side="right")
        self._error.appear_before(self._buttons)

    # ----- The two methods -----

    def _choose_method(self, method: str) -> None:
        self._method = method
        self._header.set_subtitle(SUBTITLES[method])
        self._clear_output()

    # ----- Solving -----

    def _calculate(self) -> None:
        self._clear_output()
        try:
            typed = self._input.read()
        except UNREADABLE as problem:
            self._error.show(str(problem))
            return

        self._error.hide()
        augmented, self._names = typed.matrix, typed.names
        solution = solve(augmented)
        self._unknowns = solution.unknowns
        self._elimination = (
            to_rref(augmented) if self._method == JORDAN else solution.reduction
        )

        # The same order the assignment numbers its requirements in: the walk,
        # the equivalent system, the classification, the solution, the check.
        self._draw_steps()
        self._draw_equivalent(solution)
        self._draw_result(solution)
        if solution.kind is SystemKind.INFINITE:
            self._draw_general(solution)
        if solution.kind is SystemKind.UNIQUE:
            if self._method == GAUSS:
                self._draw_substitutions(solution)
            self._draw_verification(solution)

    # ----- The step by step -----

    def _draw_steps(self) -> None:
        """The walk, in a card that keeps its own count in the heading."""
        assert self._elimination is not None
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        self._counter = SectionTitle(inside, "Paso a paso", " ")
        self._counter.pack(fill="x", pady=(0, 14))

        self._walker = StepWalker(
            inside,
            self._elimination.log,
            bar_after=self._unknowns,
            first_caption="Matriz aumentada  [ A | b ]",
            on_step=lambda index, total: self._counter.set_badge(f"{index + 1} / {total}"),
        )
        self._walker.pack(fill="x")

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

    def _draw_general(self, solution: Solution) -> None:
        """
        The family of solutions, written out: every basic variable in terms of
        the free ones.

        It is read from the reduced form even when the method chosen was Gauss,
        because that is where a pivot is alone in its column and the row is
        already the answer. The family is the same either way — the road taken
        cannot change which values solve a system — so nothing is smuggled in by
        reducing a second time behind the scenes.
        """
        family = general_solution(to_rref(solution.augmented), solution.unknowns)
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        SectionTitle(inside, "Solución general").pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            inside,
            text=(
                "Las variables de las columnas pivote son las variables básicas; las\n"
                "demás son libres. Cada valor que se dé a las libres produce una solución."
            ),
            font=theme.font("small"),
            text_color=theme.MUTED,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        variables = ctk.CTkFrame(inside, fg_color="transparent")
        variables.pack(anchor="w", pady=(0, 14))
        basic = ", ".join(unknown_name(item.column, self._names) for item in family.basic)
        free = ", ".join(unknown_name(column, self._names) for column in family.free)
        Chip(variables, f"variables básicas: {basic}").pack(side="left", padx=(0, 8))
        Chip(variables, f"variables libres: {free}", theme.MUTED).pack(side="left")

        MonoBlock(inside, self._general_lines(family)).pack(anchor="w")

    def _general_lines(self, family: General) -> str:
        """`x = 1 + 4*z`, one line per variable, the names lined up on the equals."""
        columns = [item.column for item in family.basic] + list(family.free)
        width = max((len(unknown_name(column, self._names)) for column in columns), default=1)

        lines = []
        for item in family.basic:
            terms = ""
            for coefficient, column in item.terms:
                sign = "-" if coefficient < 0 else "+"
                size = -coefficient if coefficient < 0 else coefficient
                factor = "" if size == 1 else f"{format_factor(size)}*"
                terms += f" {sign} {factor}{unknown_name(column, self._names)}"
            name = unknown_name(item.column, self._names)
            lines.append(f"  {name:>{width}} = {format_scalar(item.constant)}{terms}")

        for column in family.free:
            lines.append(f"  {unknown_name(column, self._names):>{width}} es libre")
        return "\n".join(lines)

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
