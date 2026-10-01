"""
Esta matriz, esta escalonada? A que se reduce? Donde estan sus pivotes?

La pagina de las definiciones mismas. Toma una matriz tal como esta, comprueba
una por una las cinco propiedades numeradas y marca las entradas principales;
despues la reduce, paso a paso, y senala las posiciones pivote que la forma
reducida deja a la vista.

La reduccion no es un adorno. Una posicion pivote se define como el lugar que
ocupa una entrada principal una vez que la matriz esta en forma escalonada
reducida, asi que responder donde estan los pivotes es reducir, y una pagina que
redujera sin ensenar el trabajo estaria pidiendo que se la creyera.

El castellano de las cinco propiedades vive aqui y no en ui/presentation.py
porque ninguna otra interfaz lo dice: el programa de terminal responde a otra
tarea. El dia que alguna lo diga, las palabras se mudan alli, que es justo lo
que le paso a la clasificacion.
"""

from typing import Any

import customtkinter as ctk

from core.echelon import ECHELON, REDUCED, Form, analyse
from core.elimination import Elimination, to_rref
from core.matrix import Matrix
from core.scalar import format_scalar
from core.systems import Solution, SystemKind, solve
from ui.presentation import describe, unknown_name

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
from .gauss import KIND_COLORS

# Las cinco propiedades, dichas como las dice el curso y numeradas como
# las numera: las tres primeras dan la forma escalonada, las dos la reducida.
PROPERTIES = {
    1: "Todas las filas distintas de cero están arriba de las filas de ceros.",
    2: "La entrada principal de cada fila está en una columna a la derecha de la\n"
       "entrada principal de la fila superior.",
    3: "En una columna, todas las entradas debajo de la entrada principal son ceros.",
    4: "La entrada principal de cada fila distinta de cero es 1.",
    5: "Cada entrada principal 1 es la única entrada distinta de cero en su columna.",
}

# Por que fallo una propiedad, senalando la entrada que la rompe.
FAILURES = {
    1: "La fila {row} no es de ceros y está debajo de una fila que sí lo es.",
    2: "La entrada principal de la fila {row} está en la columna {column}, que no\n"
       "queda a la derecha de la anterior.",
    3: "a_{row}{column} = {value}, y está debajo de una entrada principal.",
    4: "La entrada principal de la fila {row} vale {value}, no 1.",
    5: "a_{row}{column} = {value}, y comparte columna con una entrada principal.",
}

EXAMPLE = (("1", "-2", "1", "0"), ("0", "2", "-8", "8"), ("-4", "5", "9", "-9"))

CLOSED = "Ver por qué  ▾"
OPEN = "Ocultar  ▴"

class EchelonPage(ctk.CTkFrame):
    """La pagina que lee la forma de una matriz y despues la reduce."""

    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._output: list[ctk.CTkBaseClass] = []
        self._bar: int | None = None
        self._names: list[str] = []

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
            augmentable=True,
        )
        self._input.pack(fill="x")

        self._error = ErrorBanner(inside)

        buttons = ctk.CTkFrame(inside, fg_color="transparent")
        buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(buttons, "Analizar  →", self._analyse).pack(side="right")
        self._error.appear_before(buttons)

    # ----- Lectura de la matriz -----

    def _analyse(self) -> None:
        self._clear_output()
        try:
            typed = self._input.read()
        except UNREADABLE as problem:
            self._error.show(str(problem))
            return

        self._error.hide()
        # Una matriz escrita casilla a casilla no es aumentada y no lleva barra;
        # una que viene de ecuaciones si, y la barra va tras las incognitas.
        self._bar = typed.unknowns or None
        reduction = to_rref(typed.matrix)

        self._names = typed.names
        self._draw_form(analyse(typed.matrix))
        self._draw_reduction(reduction)
        self._draw_pivots(
            typed.matrix, reduction, solve(typed.matrix) if self._bar else None
        )

    # ----- Las cinco propiedades -----

    def _draw_form(self, form: Form) -> None:
        """
        La respuesta en una linea, con el razonamiento plegado detras.

        Los dos veredictos son lo que alguien quiere de un vistazo. Las cinco
        propiedades son lo que quiere cuando la respuesta es no y necesita saber
        cual fallo. Solo lo primero se ha ganado estar en pantalla por defecto; lo
        segundo queda a un clic y no estorba.
        """
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        SectionTitle(inside, "Forma de la matriz").pack(fill="x", pady=(0, 12))

        verdicts = ctk.CTkFrame(inside, fg_color="transparent")
        verdicts.pack(anchor="w")
        self._verdict(verdicts, "Forma escalonada", form.is_echelon)
        self._verdict(verdicts, "Forma escalonada reducida", form.is_reduced)

        self._details = ctk.CTkFrame(inside, fg_color="transparent")
        ctk.CTkLabel(
            self._details,
            text="Las entradas principales están marcadas en azul.",
            font=theme.font("small"),
            text_color=theme.MUTED,
        ).pack(anchor="w", pady=(0, 10))
        MatrixDisplay(
            self._details, form.matrix, bar_after=self._bar, highlight=form.leading
        ).pack(anchor="w")

        properties = ctk.CTkFrame(self._details, fg_color="transparent")
        properties.pack(fill="x", pady=(16, 0))
        for number in (*ECHELON, *REDUCED):
            self._property(properties, form, number)

        self._toggle = ctk.CTkButton(
            inside,
            text=CLOSED,
            width=1,
            height=26,
            anchor="w",
            corner_radius=8,
            fg_color="transparent",
            hover_color=theme.FIELD,
            text_color=theme.ACCENT,
            font=theme.font("button"),
            command=self._toggle_details,
        )
        self._toggle.pack(anchor="w", pady=(12, 0))

    def _toggle_details(self) -> None:
        """Despliega las cinco propiedades, o las vuelve a plegar."""
        if self._details.winfo_ismapped():
            self._details.pack_forget()
            self._toggle.configure(text=CLOSED)
        else:
            self._details.pack(fill="x", pady=(14, 0), before=self._toggle)
            self._toggle.configure(text=OPEN)

    def _verdict(self, master: ctk.CTkFrame, text: str, holds: bool) -> None:
        """Una de las dos respuestas, con su propio color para leerla de un vistazo."""
        Chip(
            master,
            f"{'✓' if holds else '✗'}  {text}",
            theme.GREEN if holds else theme.MUTED,
        ).pack(side="left", padx=(0, 8))

    def _property(self, master: ctk.CTkFrame, form: Form, number: int) -> None:
        """Una propiedad numerada: si se cumple, y donde se rompio si no."""
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

    # ----- Paso a la forma escalonada reducida -----

    def _draw_reduction(self, reduction: Elimination) -> None:
        """
        El recorrido hasta la forma reducida, una operacion elemental cada vez.

        Es el mismo algoritmo que corre la pagina de eliminacion, y se ensena aqui
        porque esta pagina tiene que reducir de todas formas: las posiciones pivote
        que informa mas abajo son las entradas principales de la matriz en la que
        termina este recorrido.
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

    # ----- Los pivotes, que viven en la forma reducida -----

    def _draw_pivots(
        self, matrix: Matrix, reduction: Elimination, solution: Solution | None
    ) -> None:
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
        # Las columnas que son coeficientes: todas en una matriz cualquiera, todas
        # menos la ultima en una aumentada, cuya ultima columna es b.
        width = self._bar or matrix.cols
        columns = [column for _row, column in positions if column <= width]
        free = [column for column in range(1, width + 1) if column not in set(columns)]

        chips = ctk.CTkFrame(inside, fg_color="transparent")
        chips.pack(anchor="w", pady=(0, 14))
        if solution is not None:
            Chip(chips, f"incógnitas: {width}", theme.MUTED).pack(side="left", padx=(0, 8))
        Chip(chips, f"columnas pivote: {_listed(columns)}").pack(side="left", padx=(0, 8))
        if free:
            Chip(chips, f"columnas sin pivote: {_listed(free)}", theme.MUTED).pack(
                side="left", padx=(0, 8)
            )

        if solution is not None:
            self._draw_reading(inside, solution, reduction, free)

        both = ctk.CTkFrame(inside, fg_color="transparent")
        both.pack(anchor="w")
        self._marked(both, "La matriz, con sus posiciones pivote", matrix, positions)
        self._marked(
            both, "Su forma escalonada reducida", reduction.result, positions, column=1
        )

    def _draw_reading(
        self,
        master: ctk.CTkFrame,
        solution: Solution,
        reduction: Elimination,
        free: list[int],
    ) -> None:
        """
        Lo que dicen los pivotes del sistema que representa una matriz aumentada.

        Es el teorema de existencia leido en los pivotes, y nada mas: un sistema
        tiene solucion exactamente cuando la columna de b no tiene pivote, y una
        sola cuando todas las columnas de A lo tienen. Las palabras de la
        clasificacion son las del enunciado, de presentation.py, como en todo lo demas.
        """
        headline = ctk.CTkFrame(master, fg_color="transparent")
        headline.pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            headline, text="●", font=theme.font("body"),
            text_color=KIND_COLORS[solution.kind],
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            headline, text=describe(solution), font=theme.font("body"), text_color=theme.INK
        ).pack(side="left")

        if solution.kind is SystemKind.INCONSISTENT:
            row = next(row for row, column in reduction.pivots if column > solution.unknowns)
            reason = (
                "La columna de los términos independientes es columna pivote: la fila "
                f"{row} de la forma reducida se lee 0 = 1, y ningún valor de las "
                "incógnitas la cumple."
            )
        elif solution.kind is SystemKind.INFINITE:
            names = ", ".join(unknown_name(column, self._names) for column in free)
            reason = (
                "La columna de los términos independientes no es columna pivote, así "
                f"que hay solución; y {names} no tienen pivote, así que son "
                "variables libres."
            )
        else:
            reason = (
                "La columna de los términos independientes no es columna pivote y "
                "todas las de A lo son: hay solución, y es una sola."
            )
        ctk.CTkLabel(
            master, text=reason, font=theme.font("small"), text_color=theme.MUTED,
            justify="left", wraplength=620,
        ).pack(anchor="w", pady=(0, 14))

    def _marked(
        self,
        master: ctk.CTkFrame,
        caption: str,
        matrix: Matrix,
        positions: tuple[tuple[int, int], ...],
        column: int = 0,
    ) -> None:
        """Una matriz con sus posiciones pivote resaltadas, bajo su propio titulo."""
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

    # ----- Mantenimiento -----

    def _add_card(self) -> Card:
        card = Card(self)
        card.pack(fill="x", pady=(16, 0))
        self._output.append(card)
        return card

    def _clear_output(self) -> None:
        """Un veredicto sobre una matriz deja de significar nada al reescribirla."""
        for card in self._output:
            card.destroy()
        self._output = []

def _listed(columns: list[int]) -> str:
    """1, 3, 5, o la palabra para ninguna de ellas."""
    return ", ".join(str(column) for column in columns) if columns else "ninguna"
