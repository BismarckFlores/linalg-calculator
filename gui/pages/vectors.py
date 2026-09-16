"""
Vectors of R^n: adding them, subtracting them, scaling them, and deciding
whether one is a linear combination of others.

The dimension is never asked for. It is however many components the vectors
typed turn out to have, which is the point the assignment makes of it, and the
page only insists that every vector of one calculation has the same.

The operations are shown the two ways they are written by hand: as columns side
by side, and component by component. A combination is shown as the vector
equation it is, then as the system that equation stands for, then solved with
the same elimination as the Eliminación Gaussiana page, and finally put back
together to check that it gives b.

The Spanish lives here because no other front end says any of it.
"""

from typing import Any

import customtkinter as ctk

from core.matrix import Matrix
from core.scalar import Scalar, format_factor, format_scalar
from core.systems import SystemKind
from core.vectors import (
    Combination,
    EmptyVector,
    UnreadableComponent,
    Vector,
    VectorError,
    add,
    combine,
    parse_vector,
    scale,
    subtract,
)
from core.verification import verify
from ui.presentation import (
    SUBSCRIPTS,
    pretty_label,
    render_general,
    render_linear_sum,
    render_system,
    render_values,
    render_verification,
    typographic_rows,
)

from .. import theme
from ..widgets import (
    SIZE_LIMIT,
    Card,
    Chip,
    ErrorBanner,
    Expression,
    MathBlock,
    MathChip,
    MathLine,
    PageHeader,
    PrimaryButton,
    SectionTitle,
    SegmentedControl,
    StepWalker,
)

SUM = "u + v"
DIFFERENCE = "u − v"
MULTIPLE = "k · u"
COMBINATION = "Combinación lineal"

VECTOR_SUBTITLES = {
    SUM: "Suma de dos vectores de ℝⁿ, componente a componente.",
    DIFFERENCE: "Resta de dos vectores de ℝⁿ, componente a componente.",
    MULTIPLE: "Un vector de ℝⁿ multiplicado por un escalar: cada componente por el mismo número.",
    COMBINATION: "¿Es b una combinación lineal de v₁, v₂, …, vₖ? Se resuelve como un sistema.",
}

VECTOR_HELP = (
    "Separa las componentes con comas o espacios, y usa punto decimal: 1, -2, 0.5, 1/3.\n"
    "No hace falta decir la dimensión n: es la cantidad de componentes que escribas."
)
SET_HELP = (
    "Un vector por línea: v₁ en la primera, v₂ en la segunda, y así. Todos tienen que\n"
    "tener tantas componentes como b."
)

# What the boxes hold before anybody types, so the first click shows something.
FIRST_VECTOR = "1, -2, 3"
SECOND_VECTOR = "4, 0, -1/2"
SCALAR_EXAMPLE = "-3"
TARGET_EXAMPLE = "7, 4, -3"
SET_EXAMPLE = "1, -2, -5\n2, 5, 6"

# How many vectors of a combination fit on one line before it wraps.
TERMS_PER_ROW = 4

# A colour per answer, so it is legible before it is read.
ANSWER_COLORS = {
    SystemKind.UNIQUE: theme.GREEN,
    SystemKind.INFINITE: theme.ORANGE,
    SystemKind.INCONSISTENT: theme.RED,
}

SUPERSCRIPT_DIGITS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

def subscript(name: str, index: int) -> str:
    """`v` and 2 written as `v₂`."""
    return name + str(index).translate(SUBSCRIPTS)

def vector_text(vector: Vector) -> str:
    """A vector written in a line, the way it is in a text: `(1, -2, 1/3)`."""
    return "(" + ", ".join(format_scalar(value) for value in vector) + ")"

def folded(first: Scalar, sign: str, second: Scalar) -> str:
    """
    `a + b` or `a - b` with the sign of b folded into the operation.

    `2 + (-3)` is written `2 - 3` and `2 - (-3)` is written `2 + 3`, the way
    it is by hand once the brackets have done their job.
    """
    if second < 0:
        sign = "-" if sign == "+" else "+"
        second = -second
    return f"{format_scalar(first)} {sign} {format_scalar(second)}"

def folded_sign(weight: Scalar) -> str:
    """A scalar after the first, with its sign as the operation: `+ 2`, `- 1/3`."""
    return f"- {format_scalar(-weight)}" if weight < 0 else f"+ {format_scalar(weight)}"

def product(factor: Scalar, value: Scalar) -> str:
    """
    `k` times one component: `3(2)`, `-3(2)`, `(1/2)(-4)`.

    The component always goes in brackets, since two numbers next to each other
    would run together. A whole negative scalar goes in front as it is, the way
    a line starts by hand; a fraction goes in brackets of its own.
    """
    if factor.denominator == 1:
        return f"{format_scalar(factor)}({format_scalar(value)})"
    return f"{format_factor(factor)}({format_scalar(value)})"

class VectorsPage(ctk.CTkFrame):
    """The page of vector operations in R^n and linear combinations."""

    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._operation = SUM
        self._output: list[ctk.CTkBaseClass] = []

        self._header = PageHeader(self, "↗", "Vectores en ℝⁿ", VECTOR_SUBTITLES[SUM])
        self._header.pack(anchor="w", pady=(0, 18))

        SegmentedControl(
            self, (SUM, DIFFERENCE, MULTIPLE, COMBINATION), self._choose
        ).pack(anchor="w", pady=(0, 16))

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)

        # The three fields of the operations, and the two of a combination.
        self._pair = ctk.CTkFrame(inside, fg_color="transparent")
        self._pair.pack(fill="x")
        self._scalar_row = self._row(self._pair, "k", SCALAR_EXAMPLE, 0, width=90)
        self._first_row = self._row(self._pair, "u", FIRST_VECTOR, 1)
        self._second_row = self._row(self._pair, "v", SECOND_VECTOR, 2)
        self._scalar_row[0].grid_remove()
        self._scalar_row[1].grid_remove()
        self._help(self._pair, VECTOR_HELP).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(10, 0)
        )

        self._set = ctk.CTkFrame(inside, fg_color="transparent")
        target = ctk.CTkFrame(self._set, fg_color="transparent")
        target.pack(fill="x")
        self._target_row = self._row(target, "b", TARGET_EXAMPLE, 0)
        ctk.CTkLabel(
            self._set,
            text="VECTORES  v₁, v₂, …, vₖ",
            font=theme.font("label"),
            text_color=theme.MUTED,
        ).pack(anchor="w", pady=(16, 8))
        self._vectors = ctk.CTkTextbox(
            self._set,
            height=130,
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
        self._vectors.insert("1.0", SET_EXAMPLE)
        self._vectors.bind("<KeyRelease>", lambda _event: self._clear_output())
        self._vectors.pack(fill="x")
        self._help(self._set, SET_HELP).pack(anchor="w", pady=(8, 0))

        self._error = ErrorBanner(inside)

        self._buttons = ctk.CTkFrame(inside, fg_color="transparent")
        self._buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(self._buttons, "Calcular  →", self._calculate).pack(side="right")
        self._error.appear_before(self._buttons)

    def _row(
        self, master: Any, name: str, example: str, row: int, width: int = 360
    ) -> tuple[ctk.CTkLabel, ctk.CTkEntry]:
        """A name and the box its value is typed into, on one line of a grid."""
        label = ctk.CTkLabel(
            master, text=f"{name} =", font=theme.font("mono"), text_color=theme.MUTED
        )
        label.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        entry = ctk.CTkEntry(
            master,
            width=width,
            height=38,
            corner_radius=theme.FIELD_RADIUS,
            fg_color=theme.FIELD,
            border_width=1,
            border_color=theme.BORDER,
            text_color=theme.INK,
            font=theme.font("mono"),
        )
        entry.insert(0, example)
        entry.bind("<KeyRelease>", self._typed)
        entry.bind("<Return>", lambda _event: self._calculate())
        entry.grid(row=row, column=1, sticky="w", pady=4)
        return label, entry

    def _help(self, master: Any, text: str) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            master,
            text=text,
            font=theme.font("small"),
            text_color=theme.MUTED,
            justify="left",
            anchor="w",
        )

    # ----- Choosing what to calculate -----

    def _choose(self, operation: str) -> None:
        self._operation = operation
        self._header.set_subtitle(VECTOR_SUBTITLES[operation])
        self._clear_output()
        self._error.hide()

        # The error banner was just hidden, so the buttons are the next thing
        # down, and the fields go straight above them.
        if operation == COMBINATION:
            self._pair.pack_forget()
            self._set.pack(fill="x", before=self._buttons)
            return
        self._set.pack_forget()
        self._pair.pack(fill="x", before=self._buttons)

        # k u has a scalar and no v; the other two have v and no scalar.
        scalar = operation == MULTIPLE
        shown, hidden = (
            (self._scalar_row, self._second_row) if scalar else (self._second_row, self._scalar_row)
        )
        for widget in shown:
            widget.grid()
        for widget in hidden:
            widget.grid_remove()

    def _typed(self, event: Any) -> None:
        if event.keysym != "Return":
            self._clear_output()

    # ----- Reading what was typed -----

    def _read(self, entry: ctk.CTkEntry, name: str) -> Vector:
        """One vector, or a Spanish sentence about why it is not one."""
        try:
            vector = parse_vector(entry.get())
        except EmptyVector:
            raise ValueError(f"Escribe las componentes de {name}.") from None
        except UnreadableComponent as problem:
            raise ValueError(
                f"En {name}, '{problem.text}' no es un número. Prueba con 3, -2.5 o 1/3."
            ) from None
        if len(vector) > SIZE_LIMIT:
            raise ValueError(
                f"{name} tiene {len(vector)} componentes y el máximo es {SIZE_LIMIT}."
            )
        return vector

    def _read_scalar(self) -> Scalar:
        text = self._scalar_row[1].get().strip()
        try:
            (value,) = parse_vector(text)
        except (EmptyVector, UnreadableComponent, ValueError):
            raise ValueError(
                f"El escalar k tiene que ser un solo número, como 3, -2.5 o 1/3 ('{text}')."
            ) from None
        return value

    def _read_set(self, target: Vector) -> list[Vector]:
        """v₁ to vₖ, one per line, each with as many components as b."""
        lines = [line.strip() for line in self._vectors.get("1.0", "end").splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            raise ValueError("Escribe al menos un vector v₁ para combinar.")
        if len(lines) > SIZE_LIMIT:
            raise ValueError(f"Son {len(lines)} vectores y el máximo es {SIZE_LIMIT}.")

        vectors = []
        for index, line in enumerate(lines, start=1):
            name = subscript("v", index)
            try:
                vector = parse_vector(line)
            except UnreadableComponent as problem:
                raise ValueError(
                    f"En {name}, '{problem.text}' no es un número. Prueba con 3, -2.5 o 1/3."
                ) from None
            except VectorError:
                raise ValueError(f"La línea de {name} no tiene componentes.") from None
            if len(vector) != len(target):
                raise ValueError(
                    f"{name} tiene {len(vector)} componentes y b tiene {len(target)}: "
                    f"todos los vectores tienen que ser de "
                    f"ℝ{str(len(target)).translate(SUPERSCRIPT_DIGITS)}."
                )
            vectors.append(vector)
        return vectors

    # ----- Calculating -----

    def _calculate(self) -> None:
        self._clear_output()
        try:
            if self._operation == COMBINATION:
                target = self._read(self._target_row[1], "b")
                self._draw_combination(combine(self._read_set(target), target))
            elif self._operation == MULTIPLE:
                factor = self._read_scalar()
                self._draw_multiple(factor, self._read(self._first_row[1], "u"))
            else:
                u = self._read(self._first_row[1], "u")
                v = self._read(self._second_row[1], "v")
                if len(u) != len(v):
                    verb = "sumar" if self._operation == SUM else "restar"
                    raise ValueError(
                        f"Para {verb}, u y v tienen que ser del mismo ℝⁿ: u tiene "
                        f"{len(u)} componentes y v tiene {len(v)}."
                    )
                self._draw_pair(u, v)
        except ValueError as problem:
            self._clear_output()
            self._error.show(str(problem))
            return
        self._error.hide()

    # ----- Sum and difference -----

    def _draw_pair(self, u: Vector, v: Vector) -> None:
        adding = self._operation == SUM
        result = add(u, v) if adding else subtract(u, v)
        sign = "+" if adding else "−"
        name = f"u {sign} v"

        inside = self._card("Resultado", f"n = {len(u)}")
        (
            Expression(inside)
            .matrix(Matrix.column_vector(u), "u")
            .symbol(sign)
            .matrix(Matrix.column_vector(v), "v")
            .symbol("=")
            .matrix(Matrix.column_vector(result), name, highlight=True)
        ).pack(anchor="w")
        MathLine(inside, f"{name} = {vector_text(result)}", "mono", theme.ACCENT).pack(
            anchor="w", pady=(16, 0)
        )

        rows = [
            (
                f"{subscript('u', i)} {sign} {subscript('v', i)}",
                folded(a, "+" if adding else "-", b),
                c,
            )
            for i, (a, b, c) in enumerate(zip(u, v, result), start=1)
        ]
        self._draw_components(rows)

    # ----- A scalar times a vector -----

    def _draw_multiple(self, factor: Scalar, u: Vector) -> None:
        result = scale(factor, u)
        inside = self._card("Resultado", f"n = {len(u)}")
        (
            Expression(inside)
            .symbol(f"{format_scalar(factor)} ·")
            .matrix(Matrix.column_vector(u), "u")
            .symbol("=")
            .matrix(Matrix.column_vector(result), "k u", highlight=True)
        ).pack(anchor="w")
        MathLine(
            inside,
            f"{render_linear_sum([factor], ['u'])} = {vector_text(result)}",
            "mono",
            theme.ACCENT,
        ).pack(anchor="w", pady=(16, 0))

        rows = [
            (f"k·{subscript('u', i)}", product(factor, a), c)
            for i, (a, c) in enumerate(zip(u, result), start=1)
        ]
        self._draw_components(rows)

    def _draw_components(self, rows: list[tuple[str, str, Scalar]]) -> None:
        """The same operation, one component at a time, as three lined-up columns."""
        inside = self._card("Componente a componente")
        grid = ctk.CTkFrame(inside, fg_color="transparent")
        grid.pack(anchor="w")
        for row, (name, work, value) in enumerate(rows):
            MathLine(grid, name, "mono", theme.MUTED).grid(row=row, column=0, sticky="e", pady=3)
            ctk.CTkLabel(grid, text="=", font=theme.font("mono"), text_color=theme.MUTED).grid(
                row=row, column=1, padx=10
            )
            MathLine(grid, work).grid(row=row, column=2, sticky="w")
            ctk.CTkLabel(grid, text="=", font=theme.font("mono"), text_color=theme.MUTED).grid(
                row=row, column=3, padx=10
            )
            MathLine(grid, format_scalar(value), "mono", theme.ACCENT).grid(
                row=row, column=4, sticky="w"
            )

    # ----- Linear combination -----

    def _draw_combination(self, found: Combination) -> None:
        solution = found.solution
        count = len(found.vectors)
        names = [subscript("c", index) for index in range(1, count + 1)]
        vectors = [subscript("v", index) for index in range(1, count + 1)]
        listed = ", ".join(vectors)

        # The question, written as the vector equation and as the system it is.
        inside = self._card("Planteamiento", f"n = {len(found.target)} · k = {count}")
        self._muted(
            inside,
            f"b es combinación lineal de {listed} si existen escalares "
            f"{', '.join(names)} tales que:",
        )
        equation = Expression(inside)
        for index, vector in enumerate(found.vectors):
            if index and index % TERMS_PER_ROW == 0:
                equation.new_line()
            equation.symbol(f"+ {names[index]}" if index else names[index], theme.ACCENT)
            equation.matrix(Matrix.column_vector(vector), vectors[index])
        equation.symbol("=").matrix(Matrix.column_vector(found.target), "b")
        equation.pack(anchor="w", pady=(12, 16))
        self._muted(inside, "Igualando componente por componente, es el sistema:")
        MathBlock(
            inside, typographic_rows(render_system(solution.augmented, count, names))
        ).pack(anchor="w", pady=(10, 0))

        # The system, solved by the same elimination as everywhere else.
        inside = self._card("Paso a paso")
        StepWalker(
            inside,
            solution.log,
            bar_after=count,
            first_caption=f"Matriz aumentada  [ {' '.join(vectors)} | b ]",
        ).pack(fill="x")

        self._draw_answer(found, names, vectors)
        if found.weights is not None:
            self._draw_check(found, names, vectors)

    def _draw_answer(self, found: Combination, names: list[str], vectors: list[str]) -> None:
        solution = found.solution
        listed = ", ".join(vectors)
        inside = self._card("Resultado")

        ranks = ctk.CTkFrame(inside, fg_color="transparent")
        ranks.pack(anchor="w", pady=(0, 14))
        for text in (
            f"rango(A) = {solution.coefficient_rank}",
            f"rango(A|b) = {solution.rank}",
            f"escalares = {solution.unknowns}",
        ):
            Chip(ranks, text, theme.MUTED).pack(side="left", padx=(0, 8))

        sentence = {
            SystemKind.UNIQUE: f"b es combinación lineal de {listed}, de una única manera.",
            SystemKind.INFINITE: f"b es combinación lineal de {listed}, de infinitas maneras.",
            SystemKind.INCONSISTENT: f"b no es combinación lineal de {listed}.",
        }[solution.kind]
        headline = ctk.CTkFrame(inside, fg_color="transparent")
        headline.pack(anchor="w")
        ctk.CTkLabel(
            headline, text="●", font=theme.font("body"), text_color=ANSWER_COLORS[solution.kind]
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            headline, text=sentence, font=theme.font("heading"), text_color=theme.INK
        ).pack(side="left")

        if solution.kind is SystemKind.INCONSISTENT:
            self._muted(
                inside,
                pretty_label(render_values(solution, names))
                + "\nNingún valor de los escalares hace que la combinación dé b.",
            ).pack_configure(pady=(12, 0))
            return

        weights = found.weights
        assert weights is not None
        if solution.kind is SystemKind.INFINITE:
            assert found.general is not None
            self._muted(inside, pretty_label(render_values(solution, names))).pack_configure(
                pady=(12, 10)
            )
            MathBlock(inside, render_general(found.general, names)).pack(anchor="w")
            free = ", ".join(f"{names[column - 1]} = 0" for column in found.general.free)
            self._muted(inside, f"Por ejemplo, con {free}:").pack_configure(pady=(14, 0))

        chips = ctk.CTkFrame(inside, fg_color="transparent")
        chips.pack(anchor="w", pady=(12, 0))
        for name, weight in zip(names, weights):
            MathChip(chips, f"{name} = {format_scalar(weight)}").pack(side="left", padx=(0, 8))
        MathLine(
            inside, f"b = {render_linear_sum(weights, vectors)}", "mono", theme.ACCENT
        ).pack(anchor="w", pady=(14, 0))

    def _draw_check(self, found: Combination, names: list[str], vectors: list[str]) -> None:
        """The scalars put back: every vector scaled, then all of them added up."""
        weights = found.weights
        assert weights is not None
        title = (
            "Comprobación"
            if found.solution.kind is SystemKind.UNIQUE
            else "Comprobación del ejemplo"
        )
        inside = self._card(title)
        self._muted(inside, "Cada vector multiplicado por su escalar, y los productos sumados:")

        scaled = [scale(weight, vector) for weight, vector in zip(weights, found.vectors)]
        total = scaled[0]
        for vector in scaled[1:]:
            total = add(total, vector)

        written = Expression(inside)
        for index, (weight, vector) in enumerate(zip(weights, found.vectors)):
            if index and index % TERMS_PER_ROW == 0:
                written.new_line()
            text = format_scalar(weight) if index == 0 else folded_sign(weight)
            written.symbol(f"{text} ·").matrix(Matrix.column_vector(vector), vectors[index])
        written.pack(anchor="w", pady=(12, 0))

        added = Expression(inside)
        for index, vector in enumerate(scaled):
            if index and index % TERMS_PER_ROW == 0:
                added.new_line()
            added.symbol("=" if index == 0 else "+")
            added.matrix(Matrix.column_vector(vector), f"{names[index]}{vectors[index]}")
        added.symbol("=").matrix(Matrix.column_vector(total), "b", highlight=True)
        added.pack(anchor="w", pady=(12, 0))

        holds = total == found.target
        Chip(
            inside,
            f"{render_linear_sum(weights, vectors)} = b  ✓" if holds else "No da b",
            theme.GREEN if holds else theme.RED,
        ).pack(anchor="w", pady=(14, 16))

        self._muted(inside, "Y en el sistema, componente por componente:")
        checked = verify(found.solution.coefficients, found.solution.constants, weights)
        MathBlock(inside, render_verification(checked), "left").pack(anchor="w", pady=(10, 0))

    # ----- Housekeeping -----

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
            master,
            text=text,
            font=theme.font("small"),
            text_color=theme.MUTED,
            justify="left",
            anchor="w",
            wraplength=640,
        )
        label.pack(anchor="w")
        return label

    def _clear_output(self) -> None:
        """A result stops being true the moment anything is retyped."""
        for card in self._output:
            card.destroy()
        self._output = []
