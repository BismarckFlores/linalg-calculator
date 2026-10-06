"""
Las dos maneras de entregar una matriz, en un solo sitio.

Las paginas de esta ventana piden lo mismo de las mismas dos formas (una
cuadricula de numeros, o el sistema escrito como ecuaciones), asi que la tarjeta
que lo pide vive aqui en vez de repetirse. Lo que devuelve es un Typed: la
matriz, los nombres de las incognitas cuando algo las nombro, y cuantas de sus
columnas son coeficientes y no terminos independientes.

El castellano de lo que no se puede leer vive aqui por la misma razon. Son las
mismas palabras que usa ui/prompts.py en la terminal, mas el numero de la linea,
que la terminal no necesita porque acaba de pedir esa ecuacion y la ventana las
tiene todas en pantalla a la vez.
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
    Lo que alguien entrego, lo haya escrito como lo haya escrito.

    unknowns es cuantas columnas son coeficientes, asi que es donde va la barra
    de una matriz aumentada. Vale 0 para una matriz escrita casilla a casilla,
    que no es aumentada y no lleva barra. names viene vacio salvo que las
    ecuaciones hayan dicho como se llaman las incognitas.
    """

    matrix: Matrix
    names: list[str] = field(default_factory=list)
    unknowns: int = 0

class SystemInput(ctk.CTkFrame):
    """
    El selector, las cuadriculas y el cuadro de texto: todo lo que va encima del
    boton de calcular.

    split es la diferencia entre las dos paginas. Una pagina que resuelve A x = b
    quiere A y b en cuadriculas separadas, con b siguiendo a A fila por fila; una
    que lee la forma de una matriz quiere una sola cuadricula y ninguna b. Las
    ecuaciones escritas producen una matriz aumentada por los dos caminos, porque
    eso es un sistema escrito entero.
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
        max_size: int | None = SIZE_LIMIT,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._split = split
        self._way_in = COEFFICIENTS
        self._on_change = on_change
        self._max_size = max_size

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
            max_size=max_size,
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
                max_size=max_size,
            )
            self._b.grid(row=0, column=1, sticky="nw")

        # Una sola cuadricula no dice si su ultima columna es b. Alguien tiene que
        # decirlo, o una matriz aumentada de 3x5 se lee como cinco incognitas y no cuatro.
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
        """El sistema escrito entero, una ecuacion por linea, como se escribe en papel."""
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
            # CTkTextbox declara text_color como un solo color aunque acepta la misma
            # pareja (claro, oscuro) que todo lo demas, y la respeta.
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

        # Se rellena cuando las ecuaciones ya se leyeron, nunca antes: la lista de
        # incognitas es una prueba de lo que se entendio, asi que hay que ganarsela.
        self._found = ctk.CTkLabel(
            frame, text="", font=theme.font("small"), text_color=theme.ACCENT, anchor="w"
        )
        return frame

    # ----- Cambio de una entrada por la otra -----

    def _choose_way_in(self, way_in: str) -> None:
        """
        Cambia las cuadriculas por el cuadro de texto, o al reves. Cada uno conserva
        lo que se habia escrito en el.
        """
        self._way_in = way_in
        if way_in == EQUATIONS:
            self._grids.pack_forget()
            self._typed.pack(fill="x")
        else:
            self._typed.pack_forget()
            self._grids.pack(fill="x")
        self._changed()

    def _retyped(self) -> None:
        """Cambiar una ecuacion invalida las incognitas que se habian leido de ella."""
        self._found.pack_forget()
        self._changed()

    def _changed(self) -> None:
        if self._on_change is not None:
            self._on_change()

    def _a_resized(self, rows: int, _cols: int) -> None:
        """Una ecuacion es una fila de A y una entrada de b: no pueden descuadrarse."""
        if self._b is not None:
            self._b.set_size(rows, 1)
        self._changed()

    def _b_resized(self, rows: int, _cols: int) -> None:
        self._a.set_size(rows, self._a.size()[1])
        self._changed()

    # ----- Lectura de lo escrito -----

    def size(self) -> tuple[int, int] | None:
        """
        El tamano de la cuadricula, o None si lo que hay escrito son ecuaciones.

        Sirve para lo que depende del tamano y no de los numeros, como decidir
        que metodo conviene antes de calcular nada. Unas ecuaciones todavia sin
        leer no tienen tamano: hasta que no se leen no se sabe cuantas
        incognitas mencionan.
        """
        if self._way_in == EQUATIONS:
            return None
        rows, cols = self._a.size()
        if self._b is not None:
            cols += 1
        return rows, cols

    def read(self) -> Typed:
        """
        La matriz, y los nombres de las incognitas cuando los hay.

        Solo las ecuaciones escritas saben como se llaman las incognitas. Unos
        numeros en una cuadricula no lo dicen nunca, asi que por ese camino la lista
        vuelve vacia y presentation.py recurre a x, y, z, w.
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
        Todas las lineas no vacias leidas, o una frase en castellano sobre la primera
        que no se pudo leer.

        equations.py lanza una excepcion por cada tipo de error y no le dice nada a
        nadie; la frase se decide aqui, igual que prompts.py la decide para la
        terminal.
        """
        lines = [line.strip() for line in self._lines.get("1.0", "end").splitlines()]
        lines = [line for line in lines if line]

        if not lines:
            raise ValueError("Escribe al menos una ecuación.")
        if self._max_size is not None and len(lines) > self._max_size:
            raise ValueError(f"Son {len(lines)} ecuaciones y el máximo es {self._max_size}.")

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
        if self._max_size is not None and len(names) > self._max_size:
            raise ValueError(f"Son {len(names)} incógnitas y el máximo es {self._max_size}.")

        self._found.configure(
            text=f"Incógnitas encontradas ({len(names)}): {', '.join(names)}"
        )
        self._found.pack(anchor="w", pady=(10, 0))
        return Typed(to_augmented(equations, names), names, len(names))

# Todo lo que una pagina tiene que capturar al leer lo que se escribio.
UNREADABLE = (CellError, ValueError)
