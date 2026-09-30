"""
The inverse of a matrix, and a system solved with it.

`[A | I]` is reduced to `[I | A⁻¹]` by the same Gauss-Jordan as the elimination
page, so the walk shown here is the walk that produced the answer. Both
products are drawn afterwards, because `A A⁻¹ = A⁻¹ A = I` is the definition
and not a formality.

The second mode takes `A x = b` the other way round from the elimination page:
it multiplies by the inverse, `x = A⁻¹ b`, and then checks `A x` against b.
When A is singular the page says so and sends the reader to Eliminación
Gaussiana, which classifies a system that this method cannot touch.

Each mode keeps its own input card, so switching between them does not throw
away what was typed in the other. The Spanish lives here because no other front
end says any of it.
"""

from typing import Any

import customtkinter as ctk

from core.inverse import InverseResult, InverseSystem, SingularMatrix, invert, solve_with_inverse
from core.scalar import format_scalar
from ui.presentation import unknown_name

from .. import theme
from ..entry import SystemInput
from ..widgets import (
    Card, Chip, ErrorBanner, Expression, MathChip, MatrixDisplay,
    PageHeader, PrimaryButton, SectionTitle, SegmentedControl, StepWalker,
)


# The two modes: the inverse on its own, and the inverse put to work.
INVERSE_MODES = ("Inversa A⁻¹", "Resolver Ax = b")
INVERSE_SUBTITLES = {
    INVERSE_MODES[0]: "Calcular A⁻¹ · transformar [ A | I ] en [ I | A⁻¹ ] por Gauss-Jordan.",
    INVERSE_MODES[1]: "Resolver A x = b · multiplicar b por la inversa de A y comprobar la solución.",
}


class InversePage(ctk.CTkFrame):
    """The page that inverts a matrix and solves a system with the inverse."""

    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._mode = INVERSE_MODES[0]
        self._output: list[Card] = []
        self._names: list[str] = []

        self._header = PageHeader(self, "⁻¹", "Matriz Inversa", INVERSE_SUBTITLES[self._mode])
        self._header.pack(anchor="w", pady=(0, 18))
        self._modes = SegmentedControl(self, INVERSE_MODES, self._choose_mode)
        self._modes.pack(anchor="w", pady=(0, 16))

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)
        # One input card per mode, built once and swapped by packing. A matrix
        # typed for the inverse is still there after a detour through the
        # system, which is what somebody comparing the two roads expects.
        self._input_holder = ctk.CTkFrame(inside, fg_color="transparent")
        self._input_holder.pack(fill="x")
        self._inputs = {
            mode: SystemInput(
                self._input_holder,
                split=mode == INVERSE_MODES[1],
                rows=2,
                cols=2,
                values=(("3", "4"), ("5", "6")),
                constants=(("3",), ("7",)),
                title="Matriz A",
                example="3x + 4y = 3\n5x + 6y = 7",
                on_change=self._clear_output,
                max_size=None,
            )
            for mode in INVERSE_MODES
        }
        # No size limit here: inverting is one reduction, and the only real
        # ceiling is how long the arithmetic takes.
        self._input = self._inputs[self._mode]
        self._input.pack(fill="x")
        self._hint = ctk.CTkLabel(
            inside,
            text="En Ecuaciones se invierte A, la matriz de coeficientes del sistema.",
            font=theme.font("small"),
            text_color=theme.MUTED,
            anchor="w",
        )
        self._hint.pack(anchor="w", pady=(12, 0))
        self._error = ErrorBanner(inside)
        self._buttons = ctk.CTkFrame(inside, fg_color="transparent")
        self._buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(self._buttons, "Calcular  →", self._calculate).pack(side="right")
        self._error.appear_before(self._buttons)

    # ----- Choosing a mode -----

    def _choose_mode(self, mode: str) -> None:
        """Swap the input card, and with it the hint that only one mode needs."""
        self._clear_output()
        self._error.hide()
        self._input.pack_forget()
        self._mode = mode
        self._input = self._inputs[mode]
        self._input.pack(fill="x")
        self._header.set_subtitle(INVERSE_SUBTITLES[mode])
        if mode == INVERSE_MODES[0]:
            self._hint.pack(anchor="w", pady=(12, 0), before=self._buttons)
        else:
            self._hint.pack_forget()

    # ----- Calculating -----

    def _calculate(self) -> None:
        """
        Read the matrix, invert it, and draw the cards that follow from it.

        Equations give a whole augmented matrix, so A is its first `unknowns`
        columns and b is the rest: the same typing produces both the matrix to
        invert and the system to solve with it.
        """
        self._clear_output()
        self._error.hide()
        try:
            typed = self._input.read()
            self._names = typed.names
            matrix = (
                typed.matrix.take_columns(1, typed.unknowns)
                if typed.unknowns else typed.matrix
            )
            if not matrix.is_square():
                raise ValueError(
                    f"A debe ser cuadrada para tener inversa: es {matrix.rows} × {matrix.cols}."
                )
            solved = None
            if self._mode == INVERSE_MODES[1]:
                constants = typed.matrix.take_columns(typed.unknowns + 1, typed.matrix.cols)
                solved = solve_with_inverse(matrix, constants)
                result = solved.inverse_result
            else:
                result = invert(matrix)
        except SingularMatrix:
            self._error.show(
                "A es singular: no puede reducirse a la identidad y no tiene inversa.\n"
                "Para clasificar un sistema con esta matriz, usa Eliminación Gaussiana."
            )
            return
        except ValueError as problem:
            self._error.show(str(problem))
            return
        except MemoryError:
            self._error.show("No hay memoria suficiente para calcular esta matriz.")
            return
        except ArithmeticError:
            self._error.show("La comprobación exacta del resultado falló.")
            return

        if solved is not None:
            self._draw_system(solved)
        self._draw_steps(result)
        self._draw_inverse(result)
        if solved is not None:
            self._draw_solution(solved)
        self._draw_verification(result, solved)

    # ----- The cards -----

    def _draw_system(self, solved: InverseSystem) -> None:
        """The system in matrix form, before anything is done to it."""
        matrix = solved.inverse_result.original
        inside = self._section("Ecuación matricial  A x = b", f"A es {matrix.rows} × {matrix.cols}")
        unknowns = [unknown_name(column, self._names) for column in range(1, matrix.cols + 1)]
        (
            Expression(inside)
            .matrix(matrix, "A")
            .symbol("·")
            .column(unknowns, "x", theme.ACCENT)
            .symbol("=")
            .matrix(solved.constants, "b")
        ).pack(anchor="w")

    def _draw_steps(self, result: InverseResult) -> None:
        """The reduction of `[A | I]`, one operation at a time, bar included."""
        card = Card(self)
        card.pack(fill="x", pady=(16, 0))
        self._output.append(card)
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        counter = SectionTitle(inside, "Paso a paso", " ")
        counter.pack(fill="x", pady=(0, 14))
        self._walker = StepWalker(
            inside,
            result.reduction.log,
            bar_after=result.original.cols,
            first_caption="Matriz aumentada  [ A | I ]",
            on_step=lambda index, total: counter.set_badge(f"{index + 1} / {total}"),
        )
        self._walker.pack(fill="x")

    def _draw_inverse(self, result: InverseResult) -> None:
        """A⁻¹ itself, which is the right half of the matrix the walk ended on."""
        inside = self._section("Resultado  A⁻¹", f"Dimensión: {result.inverse.rows} × {result.inverse.cols}")
        Chip(inside, "A es invertible", theme.GREEN).pack(anchor="w", pady=(0, 14))
        MatrixDisplay(inside, result.inverse).pack(anchor="w")

    def _draw_solution(self, solved: InverseSystem) -> None:
        """`x = A⁻¹ b` as the product it is, and then value by value."""
        inside = self._section("Solución  x = A⁻¹b")
        (
            Expression(inside)
            .matrix(solved.inverse_result.inverse, "A⁻¹")
            .symbol("·")
            .matrix(solved.constants, "b")
            .symbol("=")
            .matrix(solved.solution, "x", highlight=True)
        ).pack(anchor="w")
        values = ctk.CTkFrame(inside, fg_color="transparent")
        values.pack(anchor="w", pady=(14, 0))
        for column, value in enumerate(solved.solution.column(1), start=1):
            MathChip(
                values, f"✓  {unknown_name(column, self._names)} = {format_scalar(value)}"
            ).grid(row=(column - 1) // 4, column=(column - 1) % 4, sticky="w", padx=(0, 8), pady=4)

    def _draw_verification(self, result: InverseResult, solved: InverseSystem | None) -> None:
        """
        Both products against the identity, and `A x` against b.

        The definition asks for `A A⁻¹` and `A⁻¹ A`, so both are drawn rather
        than one with a note that the other holds too.
        """
        inside = self._section("Comprobación en la matriz original")
        (
            Expression(inside)
            .matrix(result.original, "A")
            .symbol("·")
            .matrix(result.inverse, "A⁻¹")
            .symbol("=")
            .matrix(result.left_check, "I")
        ).pack(anchor="w")
        Chip(inside, "A · A⁻¹ = I  ✓", theme.GREEN).pack(anchor="w", pady=(12, 18))
        (
            Expression(inside)
            .matrix(result.inverse, "A⁻¹")
            .symbol("·")
            .matrix(result.original, "A")
            .symbol("=")
            .matrix(result.right_check, "I")
        ).pack(anchor="w")
        Chip(inside, "A⁻¹ · A = I  ✓", theme.GREEN).pack(anchor="w", pady=(12, 0))
        if solved is not None:
            inside = self._section("Comprobación en el sistema original")
            (
                Expression(inside)
                .matrix(result.original, "A")
                .symbol("·")
                .matrix(solved.solution, "x", highlight=True)
                .symbol("=")
                .matrix(solved.check, "A x")
            ).pack(anchor="w")
            Chip(inside, "A x = b  ✓", theme.GREEN).pack(anchor="w", pady=(12, 0))

    # ----- Housekeeping -----

    def _section(self, title: str, badge: str = "") -> ctk.CTkFrame:
        """A card with its heading, kept so the next calculation can clear it."""
        card = Card(self)
        card.pack(fill="x", pady=(16, 0))
        self._output.append(card)
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, title, badge).pack(fill="x", pady=(0, 14))
        return inside

    def _clear_output(self) -> None:
        """A result stops being true the moment the matrix is retyped."""
        for card in self._output:
            card.destroy()
        self._output = []
