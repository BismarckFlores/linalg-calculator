"""
La factorizacion LU de una matriz, y un sistema resuelto con ella.

A se reduce por filas con puros reemplazos, y el multiplicador de cada operacion
se guarda en L: lo que queda de A es U. Si un pivote es cero hay que intercambiar
filas, y entonces lo que se factoriza es PA = LU, con P la matriz que recuerda
esos intercambios. La reduccion se recorre paso a paso, y el resultado se
comprueba multiplicando: P por A tiene que ser igual a L por U.

El segundo modo es para lo que sirve LU: A x = b se vuelve L(Ux) = Pb, y se
resuelve con dos sustituciones directas, Ly = Pb hacia adelante y Ux = y hacia
atras, cada una escrita ecuacion por ecuacion. La factorizacion se hace una vez
aunque b cambie.

Dos opciones, porque la factorizacion tiene dos decisiones que son del usuario:
el pivoteo parcial, que elige en cada columna el valor de mayor valor absoluto en
vez del primero que no es cero, y el modo estricto, que rechaza una matriz
singular en vez de dejarle el cero en la diagonal de U.

Cada modo conserva su propia tarjeta de entrada, asi que pasar de uno a otro no
tira lo que se habia escrito en el anterior. El castellano vive aqui porque
ninguna otra interfaz dice nada de esto.
"""

from typing import Any

import customtkinter as ctk

from core.lu import Factorization, LUSystem, Substitution, factorize, solve_with_lu
from core.matrix import NotSquare, SingularMatrix
from core.scalar import format_scalar
from ui.presentation import render_despeje, subscript, typographic_rows, unknown_name

from .. import theme
from ..entry import UNREADABLE, SystemInput
from ..widgets import (
    Card,
    Chip,
    ErrorBanner,
    Expression,
    FactorizationDisplay,
    MathBlock,
    MathChip,
    PageHeader,
    PrimaryButton,
    ResultsPage,
    SegmentedControl,
)

FACTORIZE = "Factorizar"
SOLVE = "Resolver Ax = b"
LU_MODES = (FACTORIZE, SOLVE)

LU_SUBTITLES = {
    FACTORIZE: "A = LU · A como una triangular inferior de unos por una triangular superior, "
    "con P si hubo intercambios.",
    SOLVE: "Resolver A x = b · dos sustituciones directas: L y = P b hacia adelante y "
    "U x = y hacia atrás.",
}

# El ejemplo de la presentacion de LU del curso: una 4 x 4 que se factoriza sin
# un solo intercambio, con L y U de numeros enteros, y su b.
LU_MATRIX = (
    ("3", "-7", "-2", "2"),
    ("-3", "5", "1", "0"),
    ("6", "-4", "0", "-5"),
    ("-9", "5", "-5", "12"),
)
LU_CONSTANTS = (("-9",), ("5",), ("7",), ("11",))
LU_EQUATIONS = (
    "3x1 - 7x2 - 2x3 + 2x4 = -9\n"
    "-3x1 + 5x2 + x3 = 5\n"
    "6x1 - 4x2 - 5x4 = 7\n"
    "-9x1 + 5x2 - 5x3 + 12x4 = 11"
)

def triangular_lines(steps: tuple[Substitution, ...], names: list[str]) -> str:
    """
    Una sustitucion hacia adelante o hacia atras, escrita como el despeje de siempre.

    Es el mismo trabajo que el de una eliminacion, ecuacion por ecuacion, con una
    diferencia: el coeficiente de la incognita no siempre es 1. En L lo es, porque
    lleva unos en la diagonal, pero en U es el pivote, y entonces hay un ultimo
    paso que divide. `names` son los nombres de las incognitas, en orden.

    Vive aqui y no en presentation.py porque solo la dice esta pagina: la terminal
    no sabe de LU, y un texto compartido no puede depender de un tipo que su
    programa no trae.
    """
    lines: list[str] = []
    for step in steps:
        known = [
            (coefficient, value, names[index - 1]) for coefficient, value, index in step.known
        ]
        lines.extend(
            render_despeje(
                f"  f_{step.unknown}:  ",
                names[step.unknown - 1],
                step.divisor,
                known,
                step.constant,
                step.value,
            )
        )
    return "\n".join(lines).rstrip()

class LUPage(ResultsPage):
    """La pagina que factoriza una matriz y resuelve un sistema con la factorizacion."""

    def __init__(self, master: Any) -> None:
        super().__init__(master)
        self._mode = FACTORIZE
        self._names: list[str] = []

        self._header = PageHeader(self, "LU", "Factorización LU", LU_SUBTITLES[FACTORIZE])
        self._header.pack(anchor="w", pady=(0, 18))
        SegmentedControl(self, LU_MODES, self._choose_mode).pack(anchor="w", pady=(0, 16))

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)

        # Una tarjeta de entrada por modo, construida una vez y cambiada al mostrarla:
        # una matriz escrita para factorizar sigue ahi despues de pasar por el sistema.
        self._input_holder = ctk.CTkFrame(inside, fg_color="transparent")
        self._input_holder.pack(fill="x")
        self._inputs = {
            mode: SystemInput(
                self._input_holder,
                split=mode == SOLVE,
                rows=4,
                cols=4,
                values=LU_MATRIX,
                constants=LU_CONSTANTS,
                title="Matriz A",
                example=LU_EQUATIONS,
                on_change=self._clear_output,
            )
            for mode in LU_MODES
        }
        self._input = self._inputs[self._mode]
        self._input.pack(fill="x")

        self._toggles = ctk.CTkFrame(inside, fg_color="transparent")
        self._toggles.pack(anchor="w", pady=(16, 0))
        self._partial = self._switch("Pivoteo parcial: en cada columna, el mayor valor absoluto")
        self._strict = self._switch("Modo estricto: rechazar una matriz singular")

        self._hint = ctk.CTkLabel(
            inside,
            text="En Ecuaciones se factoriza A, la matriz de coeficientes del sistema.",
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

    def _switch(self, text: str) -> ctk.CTkSwitch:
        """Un interruptor de una opcion: cambiarlo borra el resultado, que ya no vale."""
        switch = ctk.CTkSwitch(
            self._toggles,
            text=text,
            font=theme.font("body"),
            text_color=theme.INK,
            progress_color=theme.ACCENT,
            command=self._clear_output,
        )
        switch.pack(anchor="w", pady=(0, 8))
        return switch

    # ----- Eleccion de modo -----

    def _choose_mode(self, mode: str) -> None:
        """Cambia la tarjeta de entrada, y con ella lo que solo un modo necesita."""
        self._clear_output()
        self._error.hide()
        self._input.pack_forget()
        self._mode = mode
        self._input = self._inputs[mode]
        self._input.pack(fill="x")
        self._header.set_subtitle(LU_SUBTITLES[mode])
        if mode == FACTORIZE:
            self._hint.pack(anchor="w", pady=(12, 0), before=self._buttons)
        else:
            self._hint.pack_forget()

    # ----- Calculo -----

    def _calculate(self) -> None:
        """
        Lee la matriz, la factoriza y dibuja las tarjetas que salen de ahi.

        Las ecuaciones dan una matriz aumentada entera, asi que A son sus primeras
        columnas y b es el resto: lo mismo que se escribe produce la matriz que se
        factoriza y el sistema que se resuelve con ella.
        """
        self._clear_output()
        self._error.hide()
        partial = bool(self._partial.get())
        strict = bool(self._strict.get())

        try:
            typed = self._input.read()
            self._names = typed.names
            if self._mode == SOLVE:
                solved = solve_with_lu(typed.coefficients, typed.constants, partial)
                found = solved.factorization
            else:
                solved = None
                found = factorize(typed.coefficients, partial, strict)
        except NotSquare as problem:
            self._error.show(
                f"A debe ser cuadrada para factorizarse: es {problem.rows} × {problem.cols}."
            )
            return
        except SingularMatrix as problem:
            self._error.show(self._singular_message(problem.column))
            return
        except UNREADABLE as problem:
            self._error.show(str(problem))
            return
        except MemoryError:
            self._error.show("No hay memoria suficiente para calcular esta matriz.")
            return
        except ArithmeticError:
            self._error.show("La comprobación exacta del resultado falló.")
            return

        self._draw_reduction(found, partial)
        self._draw_factorization(found)
        self._draw_check(found)
        if solved is not None:
            self._draw_system(solved)

    def _singular_message(self, column: int | None) -> str:
        """Por que no se pudo: en cada modo la razon es otra y la salida tambien."""
        place = f" en la columna {column}" if column else ""
        if self._mode == SOLVE:
            return (
                f"A es singular: U tiene un 0 en la diagonal{place}, y la sustitución hacia "
                "atrás dividiría entre cero.\nPara clasificar un sistema con esta matriz, "
                "usa Eliminación Gaussiana."
            )
        return (
            f"A es singular: no hay pivote{place}, y el modo estricto no la factoriza.\n"
            "Apaga el modo estricto para ver la factorización con el 0 en la diagonal de U."
        )

    # ----- La factorizacion -----

    def _draw_reduction(self, lu: Factorization, partial: bool) -> None:
        """La reduccion de A a U, operacion por operacion."""
        how = (
            "En cada columna el pivote es el de mayor valor absoluto (pivoteo parcial)."
            if partial
            else "En cada columna el pivote es el primero que no es cero, y solo se "
            "intercambian filas cuando hace falta."
        )
        self._draw_walk(
            lu.log,
            "Matriz A",
            intro=(
                "Se hacen ceros debajo de cada pivote con reemplazos de fila, y el "
                "multiplicador de cada operación se guarda en L. " + how
            ),
        )

    def _draw_factorization(self, lu: Factorization) -> None:
        """P A = L U, con lo que dice la factorizacion de la matriz."""
        name = "P A = L U" if lu.permuted else "A = L U"
        inside = self._card(
            f"Factorización  {name}",
            f"{lu.swaps} intercambio{'s' if lu.swaps != 1 else ''}",
        )
        FactorizationDisplay(inside, lu).pack(anchor="w")

        facts = ctk.CTkFrame(inside, fg_color="transparent")
        facts.pack(anchor="w", pady=(16, 0))
        Chip(facts, f"rango = {lu.rank} de {lu.order}", theme.MUTED).pack(side="left", padx=(0, 8))
        if lu.permuted:
            order = ", ".join(str(row) for row in lu.row_order)
            Chip(facts, f"orden de las filas: {order}", theme.MUTED).pack(side="left", padx=(0, 8))
        if lu.singular:
            Chip(facts, "A es singular: U tiene un 0 en la diagonal", theme.ORANGE).pack(side="left")
        else:
            Chip(facts, "A es invertible", theme.GREEN).pack(side="left")

        if lu.permuted:
            self._muted(
                inside,
                "Hubo que intercambiar filas, y sin P la factorización no reconstruiría A: "
                "P es la identidad con las filas en el orden en que se factorizó.",
            ).pack_configure(pady=(14, 0))

    def _draw_check(self, lu: Factorization) -> None:
        """P A contra L U, que es la unica manera de saber que la factorizacion vale."""
        name = "P A = L U" if lu.permuted else "A = L U"
        inside = self._card(f"Comprobación  {name}")
        self._muted(
            inside,
            "Se multiplican L y U y se compara con P por A, entrada por entrada. La "
            "comparación es exacta, sin tolerancia: con fracciones lo que da cero es "
            "cero, así que no hay ceros fantasma que limpiar.",
        ).pack_configure(pady=(0, 14))
        (
            Expression(inside)
            .matrix(lu.permuted_matrix, "P A" if lu.permuted else "A")
            .symbol("=" if lu.holds else "≠")
            .matrix(lu.product, "L U")
        ).pack(anchor="w")
        Chip(
            inside,
            f"{name}  ✓" if lu.holds else f"{name}  ✗",
            theme.GREEN if lu.holds else theme.RED,
        ).pack(anchor="w", pady=(12, 0))

    # ----- El sistema -----

    def _draw_system(self, solved: LUSystem) -> None:
        """Las dos sustituciones, la solucion y su comprobacion en el sistema original."""
        lu = solved.factorization
        n = lu.order
        y_names = [f"y{subscript(i)}" for i in range(1, n + 1)]
        x_names = [unknown_name(i, self._names) for i in range(1, n + 1)]

        inside = self._card("Dos sustituciones")
        self._muted(
            inside,
            "A x = b se vuelve L(U x) = P b. Con U x = y, primero se despeja y de "
            "L y = P b, de arriba abajo, y después x de U x = y, de abajo arriba. "
            "Cada despeje solo usa lo que ya se encontró.",
        ).pack_configure(pady=(0, 14))
        (
            Expression(inside)
            .matrix(lu.lower, "L")
            .symbol("·")
            .column(y_names, "y", theme.ACCENT)
            .symbol("=")
            .matrix(solved.permuted, "P b")
        ).pack(anchor="w")

        inside = self._card("Sustitución hacia adelante  L y = P b")
        MathBlock(
            inside, typographic_rows(triangular_lines(solved.forward, y_names)), "left"
        ).pack(anchor="w")
        self._values(inside, y_names, [step.value for step in solved.forward])

        inside = self._card("Sustitución hacia atrás  U x = y")
        (
            Expression(inside)
            .matrix(lu.upper, "U")
            .symbol("·")
            .column(x_names, "x", theme.ACCENT)
            .symbol("=")
            .matrix(solved.intermediate, "y")
        ).pack(anchor="w", pady=(0, 14))
        MathBlock(
            inside, typographic_rows(triangular_lines(solved.backward, x_names)), "left"
        ).pack(anchor="w")
        by_unknown = sorted(solved.backward, key=lambda step: step.unknown)
        self._values(inside, x_names, [step.value for step in by_unknown])

        inside = self._card("Comprobación en el sistema original")
        self._muted(
            inside,
            "A por el vector solución tiene que dar b, calculado con el producto de "
            "matrices y sin pasar por la factorización:",
        ).pack_configure(pady=(0, 12))
        self._product_check(inside, lu.matrix, solved.solution, solved.constants)

    def _values(self, inside: ctk.CTkFrame, names: list[str], values: list[Any]) -> None:
        """Lo que se encontro, una ficha por incognita."""
        row = ctk.CTkFrame(inside, fg_color="transparent")
        row.pack(anchor="w", pady=(14, 0))
        for name, value in zip(names, values):
            MathChip(row, f"✓  {name} = {format_scalar(value)}").pack(side="left", padx=(0, 8))
