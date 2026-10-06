"""
El determinante de una matriz, por cofactores o por LU, y cual de los dos
conviene.

La pagina dice el costo de los dos metodos antes de que se elija ninguno: en
cuanto se sabe el tamano de la matriz se puede decir cuantas multiplicaciones
pide cada camino, y esa cuenta no depende de los numeros que haya dentro. Para
3 x 3 estan parejos; de 4 x 4 en adelante LU gana y la distancia crece como n!
contra n^3 / 3.

Elegido el metodo, se muestra el procedimiento entero: los menores con su signo
en el desarrollo por cofactores, y la reduccion con L, U y el producto de la
diagonal en LU. Al final, el otro metodo calcula el mismo determinante como
comprobacion, mientras el tamano lo permita.

El castellano vive aqui porque ninguna otra interfaz dice nada de esto.
"""

from typing import Any

import customtkinter as ctk

from core.determinant import (
    COFACTOR_LIMIT,
    ROW,
    Cofactors,
    Costs,
    Factorization,
    NotSquare,
    by_cofactors,
    by_lu,
    costs,
)
from core.scalar import format_factor, format_scalar
from ui.presentation import SUBSCRIPTS, SUPERSCRIPTS, pretty_label

from .. import theme
from ..entry import UNREADABLE, SystemInput
from ..widgets import (
    Card,
    Chip,
    ErrorBanner,
    Expression,
    MathChip,
    MatrixDisplay,
    PageHeader,
    PrimaryButton,
    SectionTitle,
    SegmentedControl,
)

COFACTORES = "Cofactores"
LU = "LU"

DETERMINANT_SUBTITLES = {
    COFACTORES: "det A por desarrollo de cofactores: cada entrada por su menor con signo.",
    LU: "det A por factorización LU: se reduce a U y se multiplica su diagonal.",
}

# El ejemplo con que abre la pagina es el de la presentacion del curso, el mismo
# que alli se resuelve reduciendo a una triangular.
EXAMPLE_MATRIX = (("1", "-4", "2"), ("-2", "8", "-9"), ("-1", "7", "0"))

# Mas alla de esto, calcular el otro metodo solo para comprobar costaria mas que
# todo lo demas junto: 8! son 40320 menores.
CHECK_LIMIT = 7

class DeterminantPage(ctk.CTkFrame):
    """La pagina que calcula un determinante por cofactores o por LU."""

    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._method = COFACTORES
        self._output: list[Card] = []

        self._header = PageHeader(
            self, "|A|", "Determinante", DETERMINANT_SUBTITLES[COFACTORES]
        )
        self._header.pack(anchor="w", pady=(0, 18))

        self._methods = SegmentedControl(self, (COFACTORES, LU), self._choose_method)
        self._methods.pack(anchor="w", pady=(0, 16))

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)

        self._input = SystemInput(
            inside,
            split=False,
            values=EXAMPLE_MATRIX,
            title="Matriz A",
            example="x - 4y + 2z = 0\n-2x + 8y - 9z = 0\n-x + 7y = 0",
            on_change=self._retyped,
        )
        self._input.pack(fill="x")

        # El consejo va aqui, encima del boton y debajo de la matriz, porque la
        # tarea pide saber cual conviene antes de elegir, no despues de calcular.
        self._advice = ctk.CTkFrame(inside, fg_color=theme.FIELD, corner_radius=14)
        self._advice.pack(fill="x", pady=(16, 0))
        self._advice_title = ctk.CTkLabel(
            self._advice, text="", font=theme.font("body"), text_color=theme.INK, anchor="w"
        )
        self._advice_title.pack(anchor="w", padx=16, pady=(12, 2))
        self._advice_text = ctk.CTkLabel(
            self._advice,
            text="",
            font=theme.font("small"),
            text_color=theme.MUTED,
            justify="left",
            anchor="w",
        )
        self._advice_text.pack(anchor="w", padx=16, pady=(0, 12))

        self._error = ErrorBanner(inside)

        self._buttons = ctk.CTkFrame(inside, fg_color="transparent")
        self._buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(self._buttons, "Calcular  →", self._calculate).pack(side="right")
        self._error.appear_before(self._buttons)

        self._advise()

    # ----- El consejo, antes de elegir -----

    def _retyped(self) -> None:
        """Cambiar la matriz borra el resultado y vuelve a pesar los dos metodos."""
        self._clear_output()
        self._advise()

    def _advise(self) -> None:
        """
        Lo que costaria cada metodo con la matriz que hay escrita ahora.

        El tamano se lee de la cuadricula, que es lo unico que hace falta: el
        costo depende del orden y no de los numeros. Si lo escrito son ecuaciones
        todavia sin leer, se avisa de eso en vez de inventar un tamano.
        """
        size = self._input.size()
        if size is None:
            self._advice_title.configure(text="Dos caminos para el mismo número")
            self._advice_text.configure(
                text="Escribe las ecuaciones y pulsa Calcular: con el tamaño de la matriz "
                "se puede decir cuál de los dos métodos conviene."
            )
            return

        rows, cols = size
        if rows != cols:
            self._advice_title.configure(text=f"La matriz es {rows} × {cols}")
            self._advice_text.configure(
                text="Solo las matrices cuadradas tienen determinante. Ajusta las filas o "
                "las columnas para que coincidan."
            )
            return

        self._advice_title.configure(text=self._headline(costs(rows)))
        self._advice_text.configure(text=self._reasoning(costs(rows)))

    def _headline(self, cost: Costs) -> str:
        advised = "cofactores" if cost.advised == "cofactores" else "LU"
        return f"Para una matriz {cost.order} × {cost.order} conviene {advised}"

    def _reasoning(self, cost: Costs) -> str:
        """
        Por que conviene uno u otro, con los dos numeros a la vista.

        Un desarrollo por cofactores pide del orden de n! multiplicaciones y LU
        del orden de n^3 / 3. Hasta 3 x 3 los cofactores salen igual de baratos y
        ademas se siguen a mano; de 4 x 4 en adelante la diferencia ya se nota, y
        crece sin parar.
        """
        line = (
            f"Cofactores: {cost.cofactor:,} multiplicaciones (del orden de n!).   "
            f"LU: {cost.lu:,} (del orden de n³/3)."
        ).replace(",", " ")
        if cost.order <= 2:
            return line + "\nCon este tamaño los dos son inmediatos: det A = ad − bc."
        if cost.advised == "cofactores":
            return line + (
                "\nEstán parejos, y el desarrollo por cofactores es el que se sigue a mano."
            )
        if cost.order >= COFACTOR_LIMIT:
            return line + (
                f"\nLU es unas {cost.times:,} veces más barato. Por cofactores, una matriz de "
                "25 × 25 pediría unas 1.5 × 10²⁵ multiplicaciones: ni una computadora que "
                "haga un billón por segundo terminaría en 500 000 años."
            ).replace(",", " ")
        return line + f"\nLU es unas {cost.times} veces más barato, y la distancia crece con n."

    # ----- Calcular -----

    def _choose_method(self, method: str) -> None:
        self._method = method
        self._header.set_subtitle(DETERMINANT_SUBTITLES[method])
        self._clear_output()

    def _calculate(self) -> None:
        self._clear_output()
        try:
            matrix = self._input.read().matrix
            if matrix.rows != matrix.cols:
                raise NotSquare(matrix.rows, matrix.cols)
            if self._method == COFACTORES and matrix.rows > COFACTOR_LIMIT:
                raise ValueError(
                    f"Una matriz {matrix.rows} × {matrix.rows} por cofactores pide "
                    f"{costs(matrix.rows).cofactor:,} multiplicaciones. Usa LU."
                    .replace(",", " ")
                )
        except NotSquare as problem:
            self._error.show(
                f"Solo las matrices cuadradas tienen determinante, y esta es "
                f"{problem.rows} × {problem.cols}."
            )
            return
        except UNREADABLE as problem:
            self._error.show(str(problem))
            return

        self._error.hide()
        self._advise()

        if self._method == COFACTORES:
            expansion = by_cofactors(matrix)
            self._draw_answer(expansion.value, matrix.rows)
            self._draw_cofactors(expansion)
        else:
            factorization = by_lu(matrix)
            self._draw_answer(factorization.value, matrix.rows)
            self._draw_lu(factorization)

        if matrix.rows <= CHECK_LIMIT:
            self._draw_check(matrix)

    # ----- El resultado -----

    def _draw_answer(self, value: Any, order: int) -> None:
        """El determinante, y lo que dice de la matriz: invertible o no."""
        inside = self._card("Resultado", f"{order} × {order}")
        line = ctk.CTkFrame(inside, fg_color="transparent")
        line.pack(anchor="w")
        ctk.CTkLabel(
            line, text="det A  =  ", font=theme.font("title"), text_color=theme.INK
        ).pack(side="left")
        ctk.CTkLabel(
            line,
            text=format_scalar(value),
            font=theme.font("title"),
            text_color=theme.ACCENT if value != 0 else theme.RED,
        ).pack(side="left")

        invertible = value != 0
        Chip(
            inside,
            "det A ≠ 0: A es invertible" if invertible else "det A = 0: A no es invertible",
            theme.GREEN if invertible else theme.RED,
        ).pack(anchor="w", pady=(14, 0))
        self._muted(
            inside,
            "Una matriz cuadrada es invertible si y solo si su determinante no es cero."
            if invertible
            else "El determinante es cero: las filas son linealmente dependientes y la "
            "matriz no tiene inversa.",
        ).pack_configure(pady=(10, 0))

    # ----- Por cofactores -----

    def _draw_cofactors(self, expansion: Cofactors) -> None:
        """Cada entrada de la linea elegida, con su menor, su signo y su aporte."""
        line = "fila" if expansion.along == ROW else "columna"
        inside = self._card(
            f"Desarrollo por la {line} {expansion.index}", f"{len(expansion.terms)} sumandos"
        )
        self._muted(
            inside,
            f"Se desarrolla por la {line} {expansion.index} porque es la que más ceros "
            "tiene: cada cero se salta un menor entero. El cofactor de una entrada es "
            "C = (−1)ⁱ⁺ʲ · M, donde el menor M es el determinante de lo que queda al "
            "tachar su fila y su columna.",
        ).pack_configure(pady=(0, 14))

        if not expansion.terms:
            self._muted(inside, "Todas las entradas son cero, así que el determinante es cero.")
            return

        for term in expansion.terms:
            block = ctk.CTkFrame(inside, fg_color="transparent")
            block.pack(anchor="w", pady=(0, 12))
            sign = "+" if term.sign > 0 else "−"
            (
                Expression(block)
                .symbol(f"a{_subscript(term.row)}{_subscript(term.col)} = "
                        f"{format_scalar(term.entry)}", theme.ACCENT)
                .symbol(f"·  (−1){_superscript(term.row)}⁺{_superscript(term.col)} = {sign}1")
                .symbol("·  det")
                .matrix(term.minor, f"M{_subscript(term.row)}{_subscript(term.col)}")
                .symbol(f"=  {format_scalar(term.minor_value)}")
            ).pack(anchor="w")
            MathChip(
                block,
                f"{format_factor(term.entry)} · ({sign}1) · "
                f"{format_factor(term.minor_value)}  =  {format_scalar(term.amount)}",
            ).pack(anchor="w", pady=(8, 0))

        total = " + ".join(format_scalar(term.amount) for term in expansion.terms)
        self._muted(inside, "Sumando los aportes:").pack_configure(pady=(4, 6))
        ctk.CTkLabel(
            inside,
            text=f"det A  =  {total}  =  {format_scalar(expansion.value)}".replace("+ -", "− "),
            font=theme.font("mono"),
            text_color=theme.ACCENT,
            anchor="w",
        ).pack(anchor="w")

    # ----- Por LU -----

    def _draw_lu(self, lu: Factorization) -> None:
        """La reduccion, las dos matrices, y la diagonal que da el determinante."""
        name = "P A = L U" if lu.permuted else "A = L U"
        inside = self._card(f"Factorización  {name}", f"{len(lu.steps)} operaciones")
        self._muted(
            inside,
            "Se hacen ceros debajo de cada pivote con reemplazos de fila, que no cambian "
            "el determinante, y cada multiplicador se guarda en L."
            + (
                " Hubo que intercambiar filas, así que lo que se factoriza es P A y cada "
                "intercambio cambia el signo del determinante."
                if lu.permuted
                else " No hizo falta ningún intercambio, así que P es la identidad."
            ),
        ).pack_configure(pady=(0, 12))

        for step in lu.steps:
            ctk.CTkLabel(
                inside,
                text="  " + pretty_label(step.label),
                font=theme.font("mono"),
                text_color=theme.ORANGE if step.swap else theme.MUTED,
                anchor="w",
            ).pack(anchor="w")

        written = Expression(inside)
        if lu.permuted:
            written.matrix(lu.permutation, "P").symbol("·")
        (
            written.matrix(lu.matrix, "A")
            .symbol("=")
            .matrix(lu.lower, "L")
            .symbol("·")
            .matrix(lu.upper, "U", highlight=False)
        ).pack(anchor="w", pady=(14, 0))

        inside = self._card("La diagonal de U")
        self._muted(
            inside,
            "U es triangular, y el determinante de una triangular es el producto de su "
            "diagonal principal."
            + (
                f" Hubo {lu.swaps} intercambio{'s' if lu.swaps != 1 else ''}, así que el "
                f"producto se multiplica por (−1){_superscript(lu.swaps)}."
                if lu.permuted
                else ""
            ),
        ).pack_configure(pady=(0, 12))

        # Un factor negativo va entre parentesis, como en el resto del proyecto:
        # 1 · 3 · (-5) y no 1 · 3 · -5.
        product = " · ".join(format_factor(entry) for entry in lu.diagonal)
        sign = f"(−1){_superscript(lu.swaps)} · " if lu.permuted else ""
        ctk.CTkLabel(
            inside,
            text=f"det A  =  {sign}{product}  =  {format_scalar(lu.value)}",
            font=theme.font("mono"),
            text_color=theme.ACCENT,
            anchor="w",
        ).pack(anchor="w")

    # ----- La comprobacion con el otro metodo -----

    def _draw_check(self, matrix: Any) -> None:
        """
        El mismo determinante por el otro camino, que tiene que dar lo mismo.

        Son dos procedimientos distintos sobre los mismos numeros exactos, asi
        que coincidir no es una casualidad: es lo que demuestra que ninguno de
        los dos se equivoco.
        """
        other = LU if self._method == COFACTORES else COFACTORES
        named = "LU" if other == LU else "cofactores"
        value = by_lu(matrix).value if other == LU else by_cofactors(matrix).value
        inside = self._card("Comprobación con el otro método")
        self._muted(
            inside,
            f"El mismo determinante calculado por {named}, que es un camino distinto "
            "sobre los mismos números:",
        ).pack_configure(pady=(0, 12))
        Chip(
            inside, f"por {named}:  det A = {format_scalar(value)}  ✓", theme.GREEN
        ).pack(anchor="w")

    # ----- Mantenimiento -----

    def _card(self, title: str, badge: str = "") -> ctk.CTkFrame:
        card = Card(self)
        card.pack(fill="x", pady=(16, 0))
        self._output.append(card)
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, title, badge).pack(fill="x", pady=(0, 12))
        return inside

    def _muted(self, master: Any, text: str) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            master, text=text, font=theme.font("small"), text_color=theme.MUTED,
            justify="left", anchor="w", wraplength=660,
        )
        label.pack(anchor="w")
        return label

    def _clear_output(self) -> None:
        """Un resultado deja de ser cierto en cuanto se cambia la matriz."""
        for card in self._output:
            card.destroy()
        self._output = []

def _subscript(number: int) -> str:
    """El indice de una entrada, escrito debajo: a₃₂."""
    return str(number).translate(SUBSCRIPTS)

def _superscript(number: int) -> str:
    """El exponente de un signo, escrito arriba: (−1)³."""
    return str(number).translate(SUPERSCRIPTS)
