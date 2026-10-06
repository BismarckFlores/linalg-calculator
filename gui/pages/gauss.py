"""
Resolver A x = b, por eliminacion gaussiana o por Gauss-Jordan.

Los dos metodos comparten esta pagina porque comparten el recorrido: to_ref se
detiene en la escalera y to_rref sigue y hace ceros tambien encima de cada
pivote. Cual se uso cambia el paso a paso y la ultima matriz; no cambia la
clasificacion, que cuenta pivotes, ni los valores, en los que los dos caminos
coinciden exactamente porque nunca se redondea nada.

El sistema se muestra tambien como lo que es en forma matricial, A x = b, y una
solucion unica se comprueba dos veces: con el producto A x, hecho con la misma
multiplicacion de matrices de la pagina de Operaciones Matriciales, y ecuacion
por ecuacion.

Aqui no se decide ni una palabra. ui/presentation.py escribe las frases para la
terminal y para la ventana por igual; esta pagina las coloca.
"""

from dataclasses import replace
from typing import Any

import customtkinter as ctk

from core.elimination import Elimination, to_rref
from core.matrix import Matrix
from core.parametric import general_solution
from core.scalar import format_scalar
from core.systems import Solution, SystemKind, solve
from core.verification import verify
from ui.presentation import (
    describe,
    pretty_label,
    render_equations,
    render_general,
    render_substitutions,
    render_values,
    render_verification,
    typographic_rows,
    unknown_name,
)

from .. import theme
from ..entry import UNREADABLE, SystemInput
from ..widgets import (
    Card,
    Chip,
    ErrorBanner,
    Expression,
    MathBlock,
    MathChip,
    MathLine,
    PageHeader,
    PrimaryButton,
    ResultsPage,
    SectionTitle,
    SegmentedControl,
    StepWalker,
)

GAUSS = "Gauss"
JORDAN = "Gauss-Jordan"

# Una pagina y un titulo; solo cambia la linea de debajo segun el metodo,
# porque donde se detiene el recorrido es toda la diferencia entre los dos.
SUBTITLES = {
    GAUSS: "Resolver A x = b · forma escalonada por operaciones elementales de fila.",
    JORDAN: "Resolver A x = b · forma escalonada reducida, con cada pivote solo en su columna.",
}

# Un color por clasificacion, para ver la respuesta antes de leerla.
KIND_COLORS = {
    SystemKind.UNIQUE: theme.GREEN,
    SystemKind.INFINITE: theme.ORANGE,
    SystemKind.INCONSISTENT: theme.RED,
}

class GaussPage(ResultsPage):
    """La pagina que resuelve un sistema y recorre como se resolvio."""

    def __init__(self, master: Any) -> None:
        super().__init__(master)
        self._method = GAUSS
        self._names: list[str] = []
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

    # ----- Los dos metodos -----

    def _choose_method(self, method: str) -> None:
        self._method = method
        self._header.set_subtitle(SUBTITLES[method])
        self._clear_output()

    # ----- Resolucion -----

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

        # El mismo orden en el que el enunciado numera sus requisitos: el recorrido,
        # el sistema equivalente, la clasificacion, la solucion y la comprobacion.
        # La forma matricial va primero, porque es el sistema que se esta resolviendo.
        self._draw_matrix_equation(solution)
        self._draw_steps()
        self._draw_equivalent(solution)
        self._draw_result(solution)
        if solution.kind is SystemKind.INFINITE:
            self._draw_general(solution)
        if solution.kind is SystemKind.UNIQUE:
            if self._method == GAUSS:
                self._draw_substitutions(solution)
            self._draw_verification(solution)

    # ----- La forma matricial -----

    def _draw_matrix_equation(self, solution: Solution) -> None:
        """El sistema como una sola ecuacion entre matrices: A por las incognitas es b."""
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        rows, cols = solution.coefficients.size()
        SectionTitle(inside, "Ecuación matricial  A x = b", f"A es {rows} × {cols}").pack(
            fill="x", pady=(0, 6)
        )
        ctk.CTkLabel(
            inside,
            text=(
                "El sistema escrito como una sola ecuación entre matrices. Resolverlo es "
                "encontrar el vector x que, multiplicado por A, da b."
            ),
            font=theme.font("small"),
            text_color=theme.MUTED,
            justify="left",
            wraplength=640,
        ).pack(anchor="w", pady=(0, 14))

        unknowns = [unknown_name(column, self._names) for column in range(1, cols + 1)]
        (
            Expression(inside)
            .matrix(solution.coefficients, "A")
            .symbol("·")
            .column(unknowns, "x", theme.ACCENT)
            .symbol("=")
            .matrix(solution.constants, "b")
        ).pack(anchor="w")

    # ----- El paso a paso -----

    def _draw_steps(self) -> None:
        """El recorrido, en una tarjeta que lleva su propia cuenta en el encabezado."""
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

    # ----- La respuesta -----

    def _draw_equivalent(self, solution: Solution) -> None:
        """
        La matriz en la que termino el recorrido, leida otra vez como el sistema que
        representa.

        render_equations lee la matriz en la que termino la reduccion de la solucion,
        y en Gauss-Jordan esa no es la matriz que recorrio solve. Pasarle una copia
        de la solucion apuntando a la eliminacion de esta pagina es lo que hace que
        las ecuaciones y el paso a paso ensenen lo mismo.
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
        MathBlock(inside, typographic_rows(render_equations(walked, self._names))).pack(anchor="w")

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
                MathChip(
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
            # Es prosa, no un bloque alineado en columnas: pretty_label puede escribir
            # aqui el nombre de la fila entero sin descuadrar nada.
            ctk.CTkLabel(
                inside,
                text=pretty_label(render_values(solution, self._names)),
                font=theme.font("body"),
                text_color=theme.MUTED,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(14, 0))
            # El requisito 7 tiene respuesta aunque no haya nada que comprobar:
            # decirlo es mejor que una tarjeta que simplemente no aparece.
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
        Las columnas de A que tienen pivote, que es lo que se lee de Gauss-Jordan.

        Solo las columnas de A: un pivote puede caer tambien en la columna de los
        terminos independientes, y esa no es una columna del sistema sino la razon
        de que un sistema incompatible lo sea. Eso ya lo dice la clasificacion.
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
        La familia de soluciones, escrita entera: cada variable basica en funcion
        de las libres.

        Se lee de la forma escalonada reducida aunque el metodo elegido sea Gauss,
        porque es ahi donde un pivote esta solo en su columna y la fila ya es el
        despeje. La familia es la misma por los dos caminos (el camino no cambia
        que valores resuelven un sistema), asi que reducir otra vez por detras no
        mete nada de contrabando.
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

        MathBlock(inside, render_general(family, self._names)).pack(anchor="w")

    def _draw_substitutions(self, solution: Solution) -> None:
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, "Despeje por sustitución hacia atrás").pack(fill="x", pady=(0, 14))
        MathBlock(
            inside, typographic_rows(render_substitutions(solution, self._names)), "left"
        ).pack(anchor="w")

    def _draw_verification(self, solution: Solution) -> None:
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, "Comprobación en el sistema original").pack(fill="x", pady=(0, 6))

        # La primera comprobacion es la propia forma matricial: el producto A x, hecho con
        # la misma multiplicacion que usa la pagina de Operaciones Matriciales.
        x = Matrix.column_vector(solution.values)
        product = solution.coefficients * x
        holds = product == solution.constants
        ctk.CTkLabel(
            inside,
            text="Con el producto de matrices, A por el vector solución tiene que dar b:",
            font=theme.font("small"),
            text_color=theme.MUTED,
            anchor="w",
        ).pack(fill="x", pady=(0, 12))
        (
            Expression(inside)
            .matrix(solution.coefficients, "A")
            .symbol("·")
            .matrix(x, "x", highlight=True)
            .symbol("=")
            .matrix(product, "A x")
        ).pack(anchor="w")
        Chip(
            inside,
            "A x = b  ✓" if holds else "A x ≠ b",
            theme.GREEN if holds else theme.RED,
        ).pack(anchor="w", pady=(12, 18))

        ctk.CTkLabel(
            inside,
            text="Y ecuación por ecuación:",
            font=theme.font("small"),
            text_color=theme.MUTED,
            anchor="w",
        ).pack(fill="x", pady=(0, 12))
        checked = verify(solution.coefficients, solution.constants, solution.values)
        MathBlock(inside, render_verification(checked), "left").pack(anchor="w")

    # ----- Mantenimiento -----

    def _clear_output(self) -> None:
        """
        Ademas de las tarjetas, el recorrido que las produjo.

        El paso a paso no es una tarjeta mas: es la eliminacion que esta pagina
        guarda para dibujarla, y mientras siga ahi un calculo nuevo podria
        mezclarse con el anterior.
        """
        super()._clear_output()
        self._elimination = None
