"""
La inversa de una matriz, y un sistema resuelto con ella.

[A | I] se reduce a [I | A^-1] con el mismo Gauss-Jordan de la pagina de
eliminacion, asi que el recorrido que se ve aqui es el que produjo la respuesta.
Los dos productos se dibujan despues, porque A A^-1 = A^-1 A = I es la
definicion y no un tramite.

El segundo modo toma A x = b al reves que la pagina de eliminacion: multiplica
por la inversa, x = A^-1 b, y despues comprueba A x contra b. Cuando A es
singular, la pagina lo dice y manda a Eliminacion Gaussiana, que clasifica un
sistema que este metodo no puede tocar.

Cada modo conserva su propia tarjeta de entrada, asi que pasar de uno a otro no
tira lo que se habia escrito en el anterior. El castellano vive aqui porque
ninguna otra interfaz dice nada de esto.
"""

from typing import Any

import customtkinter as ctk

from core.inverse import InverseResult, InverseSystem, SingularMatrix, invert, solve_with_inverse
from core.matrix import NotSquare
from core.scalar import format_scalar
from ui.presentation import unknown_name

from .. import theme
from ..entry import SystemInput
from ..widgets import (
    Card, Chip, ErrorBanner, Expression, MathChip, MatrixDisplay,
    PageHeader, PrimaryButton, ResultsPage, SectionTitle, SegmentedControl,
    StepWalker,
)


# Los dos modos: la inversa sola, y la inversa puesta a trabajar.
INVERSE_MODES = ("Inversa A⁻¹", "Resolver Ax = b")
INVERSE_SUBTITLES = {
    INVERSE_MODES[0]: "Calcular A⁻¹ · transformar [ A | I ] en [ I | A⁻¹ ] por Gauss-Jordan.",
    INVERSE_MODES[1]: "Resolver A x = b · multiplicar b por la inversa de A y comprobar la solución.",
}


class InversePage(ResultsPage):
    """La pagina que invierte una matriz y resuelve un sistema con la inversa."""

    def __init__(self, master: Any) -> None:
        super().__init__(master)
        self._mode = INVERSE_MODES[0]
        self._names: list[str] = []

        self._header = PageHeader(self, "⁻¹", "Matriz Inversa", INVERSE_SUBTITLES[self._mode])
        self._header.pack(anchor="w", pady=(0, 18))
        self._modes = SegmentedControl(self, INVERSE_MODES, self._choose_mode)
        self._modes.pack(anchor="w", pady=(0, 16))

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)
        # Una tarjeta de entrada por modo, construida una vez y cambiada al mostrarla.
        # Una matriz escrita para la inversa sigue ahi despues de pasar por el
        # sistema, que es lo que espera quien compara los dos caminos.
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
        # Sin limite de tamano aqui: invertir es una sola reduccion, y el unico techo
        # real es lo que tarde la aritmetica.
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

    # ----- Eleccion de modo -----

    def _choose_mode(self, mode: str) -> None:
        """Cambia la tarjeta de entrada, y con ella el aviso que solo un modo necesita."""
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

    # ----- Calculo -----

    def _calculate(self) -> None:
        """
        Lee la matriz, la invierte y dibuja las tarjetas que salen de ahi.

        Las ecuaciones dan una matriz aumentada entera, asi que A son sus primeras
        unknowns columnas y b es el resto: lo mismo que se escribe produce la matriz
        que se invierte y el sistema que se resuelve con ella.
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
            solved = None
            if self._mode == INVERSE_MODES[1]:
                constants = typed.matrix.take_columns(typed.unknowns + 1, typed.matrix.cols)
                solved = solve_with_inverse(matrix, constants)
                result = solved.inverse_result
            else:
                result = invert(matrix)
        except NotSquare as problem:
            self._error.show(
                f"A debe ser cuadrada para tener inversa: es {problem.rows} × {problem.cols}."
            )
            return
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

    # ----- Las tarjetas -----

    def _draw_system(self, solved: InverseSystem) -> None:
        """El sistema en forma matricial, antes de hacerle nada."""
        matrix = solved.inverse_result.original
        inside = self._card("Ecuación matricial  A x = b", f"A es {matrix.rows} × {matrix.cols}")
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
        """La reduccion de [A | I], operacion por operacion, con la barra incluida."""
        inside, counter = self._titled_card("Paso a paso", " ")
        self._walker = StepWalker(
            inside,
            result.reduction.log,
            bar_after=result.original.cols,
            first_caption="Matriz aumentada  [ A | I ]",
            on_step=lambda index, total: counter.set_badge(f"{index + 1} / {total}"),
        )
        self._walker.pack(fill="x")

    def _draw_inverse(self, result: InverseResult) -> None:
        """La propia A^-1, que es la mitad derecha de la matriz en que termino el recorrido."""
        inside = self._card("Resultado  A⁻¹", f"Dimensión: {result.inverse.rows} × {result.inverse.cols}")
        Chip(inside, "A es invertible", theme.GREEN).pack(anchor="w", pady=(0, 14))
        MatrixDisplay(inside, result.inverse).pack(anchor="w")

    def _draw_solution(self, solved: InverseSystem) -> None:
        """x = A^-1 b como el producto que es, y despues valor por valor."""
        inside = self._card("Solución  x = A⁻¹b")
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
        Los dos productos contra la identidad, y A x contra b.

        La definicion pide A A^-1 y A^-1 A, asi que se dibujan los dos en vez de uno
        con una nota de que el otro tambien se cumple.
        """
        inside = self._card("Comprobación en la matriz original")
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
            inside = self._card("Comprobación en el sistema original")
            (
                Expression(inside)
                .matrix(result.original, "A")
                .symbol("·")
                .matrix(solved.solution, "x", highlight=True)
                .symbol("=")
                .matrix(solved.check, "A x")
            ).pack(anchor="w")
            Chip(inside, "A x = b  ✓", theme.GREEN).pack(anchor="w", pady=(12, 0))

    # ----- Mantenimiento -----


