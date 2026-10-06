"""
Las piezas con las que se construye cada pagina.

CustomTkinter trae botones y cajas de texto; no trae matrices. Aqui estan las
pocas formas que esta calculadora necesita y la libreria no da (la tarjeta, el
contador de filas y columnas, una cuadricula de celdas entre corchetes, una
matriz ya calculada), cada una sabiendo dibujarse a si misma y nada mas.

Aqui no vive ninguna aritmetica. MatrixEntryGrid.matrix() devuelve una Matrix y
MatrixDisplay recibe una; lo que pasa en medio es asunto de core.
"""

import re
import tkinter
from collections.abc import Callable, Sequence
from typing import Any, Literal

import customtkinter as ctk

from core.matrix import Matrix
from core.roman import Numeral
from core.scalar import Scalar, format_scalar, to_scalar
from core.steps import StepLog
from ui.presentation import pretty_label

from . import theme
from .theme import Color

# Diez filas y diez columnas: el mismo tope que pide la version de terminal.
SIZE_LIMIT = 10

# Cuanto mueve una muesca de la rueda, en unidades de 30 pixeles: unas tres
# lineas de texto, que es lo que hace todo lo demas en un escritorio. Vale para
# la ventana entera hacia abajo y para una franja ancha hacia los lados.
WHEEL_STEP = 3

# Las dos maneras de leer un paso a paso: de uno en uno, o todo de una vez.
ALL_STEPS = "Ver todos los pasos  ▾"
ONE_STEP = "Ver uno a uno  ▴"

class CellError(ValueError):
    """Una casilla de una matriz escrita no tiene un numero. El mensaje va en castellano."""

class Card(ctk.CTkFrame):
    """El panel blanco redondeado dentro del que va cada seccion de una pagina."""

    def __init__(self, master: Any, **kwargs: Any) -> None:
        super().__init__(
            master,
            corner_radius=theme.CARD_RADIUS,
            fg_color=theme.CARD,
            border_width=1,
            border_color=theme.BORDER,
            **kwargs,
        )

class PageHeader(ctk.CTkFrame):
    """El titulo de una pagina y la linea de debajo que explica lo que hace."""

    def __init__(self, master: Any, glyph: str, title: str, subtitle: str) -> None:
        super().__init__(master, fg_color="transparent")
        heading = ctk.CTkFrame(self, fg_color="transparent")
        heading.pack(anchor="w")
        self._glyph = ctk.CTkLabel(
            heading, text=glyph, font=theme.font("title"), text_color=theme.ACCENT
        )
        self._glyph.pack(side="left", padx=(0, 8))
        self._title = ctk.CTkLabel(
            heading, text=title, font=theme.font("title"), text_color=theme.INK
        )
        self._title.pack(side="left")
        self._subtitle = ctk.CTkLabel(
            self, text=subtitle, font=theme.font("body"), text_color=theme.MUTED
        )
        self._subtitle.pack(anchor="w", pady=(2, 0))

    def set_subtitle(self, subtitle: str) -> None:
        """Explicar otra cosa bajo el mismo titulo: una pagina, dos metodos."""
        self._subtitle.configure(text=subtitle)

class SectionTitle(ctk.CTkFrame):
    """El encabezado de una tarjeta, con una etiqueta gris opcional a la derecha."""

    def __init__(self, master: Any, text: str, badge: str = "") -> None:
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(
            self, text=text, font=theme.font("heading"), text_color=theme.INK
        ).pack(side="left")
        self._badge = ctk.CTkLabel(
            self,
            text=badge,
            font=theme.font("label"),
            text_color=theme.MUTED,
            fg_color=theme.FIELD,
            corner_radius=10,
            padx=10,
            pady=3,
        )
        if badge:
            self._badge.pack(side="right")

    def set_badge(self, text: str) -> None:
        self._badge.configure(text=text)
        if not self._badge.winfo_ismapped():
            self._badge.pack(side="right")

class Bracket(ctk.CTkCanvas):
    """
    Una de las dos mitades de los corchetes [ ] dentro de los que va una matriz.

    Son tres lineas rectas sobre un lienzo, y es lo unico de este paquete que hay
    que repintar a mano al cambiar de tema: un lienzo guarda un color, no una
    pareja de ellos.
    """

    def __init__(
        self,
        master: Any,
        side: Literal["left", "right"],
        background: Color = theme.CARD,
    ) -> None:
        super().__init__(master, width=9, height=10, highlightthickness=0, borderwidth=0)
        self._side = side
        self._background = background
        self.bind("<Configure>", lambda _event: self._repaint())
        self.bind("<Destroy>", lambda _event: theme.off_change(self._repaint))
        theme.on_change(self._repaint)

    def _repaint(self) -> None:
        if not self.winfo_exists():
            return
        self.delete("all")
        self.configure(background=theme.resolve(self._background))

        colour = theme.resolve(theme.INK)
        width = self.winfo_width()
        height = self.winfo_height()
        spine = 2 if self._side == "left" else width - 2
        tip = width if self._side == "left" else 0

        self.create_line(spine, 1, spine, height - 1, fill=colour, width=2)
        self.create_line(spine, 2, tip, 2, fill=colour, width=2)
        self.create_line(spine, height - 2, tip, height - 2, fill=colour, width=2)

class Stepper(ctk.CTkFrame):
    """−  3  +: cuantas filas o cuantas columnas tiene una matriz."""

    def __init__(
        self,
        master: Any,
        value: int,
        minimum: int,
        maximum: int | None,
        command: Callable[[int], None],
    ) -> None:
        super().__init__(
            master,
            fg_color=theme.FIELD,
            corner_radius=theme.FIELD_RADIUS,
            border_width=1,
            border_color=theme.BORDER,
        )
        self._value = value
        self._minimum = minimum
        self._maximum = maximum
        self._command = command

        self._less = self._arrow("−", -1)
        self._less.pack(side="left", padx=(3, 0), pady=3)
        self._readout = ctk.CTkLabel(
            self, text=str(value), width=20, font=theme.font("label"), text_color=theme.INK
        )
        self._readout.pack(side="left")
        self._more = self._arrow("+", 1)
        self._more.pack(side="left", padx=(0, 3), pady=3)
        self._refresh()

    def set(self, value: int) -> None:
        """Mueve el numero sin avisar a nadie: para un tamano que siguio a otro."""
        self._value = max(self._minimum, value)
        if self._maximum is not None:
            self._value = min(self._maximum, self._value)
        self._refresh()

    def _arrow(self, text: str, delta: int) -> ctk.CTkButton:
        return ctk.CTkButton(
            self,
            text=text,
            width=24,
            height=24,
            corner_radius=8,
            fg_color="transparent",
            hover_color=theme.FIELD_HOVER,
            text_color=theme.INK,
            font=theme.font("button"),
            command=lambda: self._step(delta),
        )

    def _step(self, delta: int) -> None:
        value = max(self._minimum, self._value + delta)
        if self._maximum is not None:
            value = min(self._maximum, value)
        if value == self._value:
            return
        self._value = value
        self._refresh()
        self._command(value)

    def _refresh(self) -> None:
        self._readout.configure(text=str(self._value))
        self._less.configure(state="normal" if self._value > self._minimum else "disabled")
        self._more.configure(
            state="normal" if self._maximum is None or self._value < self._maximum else "disabled"
        )

class MatrixEntryGrid(ctk.CTkFrame):
    """
    Una matriz que alguien escribe, con los contadores que la redimensionan.

    El texto de las casillas sobrevive a los propios recuadros: crecer de 2x2 a
    3x3 y volver encuentra los cuatro numeros originales donde estaban, porque lo
    escrito se guarda en un diccionario y los recuadros se rehacen alrededor.
    """

    def __init__(
        self,
        master: Any,
        title: str,
        rows: int,
        cols: int,
        values: Sequence[Sequence[str]] = (),
        resizable_rows: bool = True,
        resizable_cols: bool = True,
        on_change: Callable[[], None] | None = None,
        on_resize: Callable[[int, int], None] | None = None,
        background: Color = theme.CARD,
        max_size: int | None = SIZE_LIMIT,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.title = title
        self._rows = rows
        self._cols = cols
        self._on_change = on_change
        self._on_resize = on_resize
        self._max_size = max_size
        self._entries: list[list[ctk.CTkEntry]] = []
        self._texts: dict[tuple[int, int], str] = {
            (i, j): str(text)
            for i, row in enumerate(values)
            for j, text in enumerate(row)
        }

        # El encabezado va encima del cuerpo en vez de ocupar sus columnas:
        # un encabezado mas ancho que la matriz estiraria las casillas y dejaria
        # los corchetes separados de los numeros.
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(
            header, text=title.upper(), font=theme.font("label"), text_color=theme.MUTED
        ).pack(side="left", padx=(0, 14))

        self._row_stepper: Stepper | None = None
        self._col_stepper: Stepper | None = None
        if resizable_rows:
            self._row_stepper = self._sized(header, "Filas", rows, self._rows_changed)
        if resizable_cols:
            self._col_stepper = self._sized(header, "Columnas", cols, self._cols_changed)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(anchor="w")
        Bracket(body, "left", background).grid(row=0, column=0, sticky="ns")
        self._cells = ctk.CTkFrame(body, fg_color="transparent")
        self._cells.grid(row=0, column=1, padx=1)
        Bracket(body, "right", background).grid(row=0, column=2, sticky="ns")
        self._build()

    # ----- Lectura -----

    def matrix(self) -> Matrix:
        """Lo escrito, como Matrix. Lanza CellError nombrando la casilla que falla."""
        self._capture()
        data = []
        for i in range(self._rows):
            row = []
            for j in range(self._cols):
                text = self._texts.get((i, j), "0").strip() or "0"
                try:
                    row.append(to_scalar(text))
                except (ValueError, TypeError):
                    raise CellError(
                        f"{self.title}: la casilla de la fila {i + 1}, columna {j + 1} "
                        f"no tiene un número válido ('{text}')."
                    ) from None
            data.append(row)
        return Matrix(data)

    def size(self) -> tuple[int, int]:
        return self._rows, self._cols

    # ----- Redimensionado -----

    def set_size(self, rows: int, cols: int) -> None:
        """Redimensiona desde fuera, para la matriz cuya forma sigue a la de otra."""
        if (rows, cols) == (self._rows, self._cols):
            return
        self._capture()
        self._rows, self._cols = rows, cols
        if self._row_stepper is not None:
            self._row_stepper.set(rows)
        if self._col_stepper is not None:
            self._col_stepper.set(cols)
        self._build()

    def _sized(
        self, header: ctk.CTkFrame, caption: str, value: int, command: Callable[[int], None]
    ) -> Stepper:
        ctk.CTkLabel(
            header, text=caption, font=theme.font("small"), text_color=theme.MUTED
        ).pack(side="left", padx=(0, 6))
        stepper = Stepper(header, value, 1, self._max_size, command)
        stepper.pack(side="left", padx=(0, 14))
        return stepper

    def _rows_changed(self, rows: int) -> None:
        self._capture()
        self._rows = rows
        self._build()
        self._announce()

    def _cols_changed(self, cols: int) -> None:
        self._capture()
        self._cols = cols
        self._build()
        self._announce()

    def _announce(self) -> None:
        if self._on_resize is not None:
            self._on_resize(self._rows, self._cols)
        if self._on_change is not None:
            self._on_change()

    # ----- Dibujo -----

    def _typed(self, _event: object) -> None:
        """Cualquier tecla deshace el resultado: se calculo con otros numeros."""
        if self._on_change is not None:
            self._on_change()

    def _capture(self) -> None:
        """Recuerda lo que hay en los recuadros antes de tirarlos."""
        for i, row in enumerate(self._entries):
            for j, entry in enumerate(row):
                self._texts[(i, j)] = entry.get()

    def _build(self) -> None:
        for row in self._entries:
            for entry in row:
                entry.destroy()
        self._entries = []

        for i in range(self._rows):
            row: list[ctk.CTkEntry] = []
            for j in range(self._cols):
                entry = ctk.CTkEntry(
                    self._cells,
                    width=54,
                    height=34,
                    corner_radius=theme.FIELD_RADIUS,
                    fg_color=theme.FIELD,
                    border_width=1,
                    border_color=theme.BORDER,
                    text_color=theme.INK,
                    font=theme.font("mono"),
                    justify="center",
                )
                entry.insert(0, self._texts.get((i, j), "0"))
                entry.grid(row=i, column=j, padx=3, pady=3)
                entry.bind("<KeyRelease>", self._typed)
                row.append(entry)
            self._entries.append(row)

class FractionCell(ctk.CTkFrame):
    """
    Una entrada escrita como se escribe una fraccion a mano: un numero encima
    del otro, con una raya en medio.

    1/3 en una sola linea es lo que puede hacer una terminal y lo que imprime el
    archivo entregado. Una ventana puede hacerlo mejor, y una columna de 22/15 y
    -17/15 se lee mucho mejor apilada que con barras.

    La raya es un marco de dos pixeles y no una linea sobre un lienzo: asi toma
    la misma pareja de colores (claro, oscuro) que todo lo demas y sigue al tema
    sin que nadie la repinte. Con un pixel no se dibujaria nada.

    Nada lleva relleno de un solo lado: la raya tiene que caer en el centro de la
    casilla, porque ahi es donde va un numero entero de la misma fila y las dos
    cosas tienen que leerse como si estuvieran en la misma linea.

    El signo menos es de la fraccion entera y no del numero de arriba, asi que va
    a la izquierda de los dos, sobre la raya. -1/4 es un numero dividido entre
    otro y luego cambiado de signo, que es lo que parece asi y no lo que parece
    cuando el signo va apilado con el numerador.
    """

    def __init__(
        self,
        master: Any,
        value: Scalar,
        color: Color = theme.INK,
        background: Color = "transparent",
        font: str = "mono_small",
    ) -> None:
        super().__init__(master, fg_color=background, corner_radius=7)
        stack = ctk.CTkFrame(self, fg_color="transparent")

        if value < 0:
            ctk.CTkLabel(
                self, text="-", font=theme.font(font), text_color=color
            ).pack(side="left", padx=(7, 1))
            stack.pack(side="left", padx=(0, 7))
        else:
            stack.pack(side="left", padx=7)

        ctk.CTkLabel(
            stack, text=str(abs(value.numerator)), font=theme.font(font),
            text_color=color,
        ).pack(padx=2)
        # width=1 porque un CTkFrame pide 200 pixeles cuando nadie dice otra cosa,
        # y entonces el fill="x" acabaria fijando el ancho de toda la casilla.
        ctk.CTkFrame(stack, width=1, height=2, fg_color=color, corner_radius=0).pack(
            fill="x", padx=2
        )
        ctk.CTkLabel(
            stack, text=str(value.denominator), font=theme.font(font), text_color=color
        ).pack(padx=2)

# Una fraccion se compone un cuerpo menor que la linea en la que va, como en
# imprenta: dos digitos apilados a tamano completo descuellan sobre su linea.
SMALLER = {"mono": "mono_small", "mono_small": "mono_tiny"}

# Una fraccion tal como la escribe format_scalar: el unico sitio donde
# aparece una barra entre digitos en lo que produce la presentacion.
_FRACTION = re.compile(r"(-?\d+)/(\d+)")

# Lo que abre una linea y va en su propia columna: f_2:, Ecuacion 1:.
# Acotado a proposito, para que una frase con dos puntos siga siendo prosa.
_TAG = re.compile(r"^(\s{0,4}\S[^=]{0,12}?:)\s")

def _pieces(text: str) -> list[tuple[str, Scalar | None]]:
    """La linea partida en tramos de texto llano y las fracciones que hay entre ellos."""
    runs: list[tuple[str, Scalar | None]] = []
    position = 0
    for match in _FRACTION.finditer(text):
        runs.append((text[position:match.start()], None))
        runs.append(("", Scalar(int(match[1]), int(match[2]))))
        position = match.end()
    runs.append((text[position:], None))
    return _unwrap(runs)

def _unwrap(runs: list[tuple[str, Scalar | None]]) -> list[tuple[str, Scalar | None]]:
    """
    Quita los parentesis que solo necesitaba una linea de texto.

    (1/2)y lleva parentesis porque 1/2y en una sola linea podria leerse como uno
    entre dos-y. Apilada, la fraccion dice sola donde termina y los parentesis
    sobran, asi que se van; pero solo donde nada mas se apoya en ellos. Contra un
    digito u otro parentesis siguen haciendo falta: 3(-17/12) quedaria 3-17/12, y
    (1/2)(23/12) se juntaria consigo mismo.
    """
    joined = "".join(run for run, fraction in runs if fraction is None)
    tidied = list(runs)
    for index in range(1, len(tidied) - 1, 2):
        before, after = tidied[index - 1][0], tidied[index + 1][0]
        if not before.endswith("(") or not after.startswith(")"):
            continue
        outside = (before[-2:-1] or " ") + (after[1:2] or " ")
        if any(character.isdigit() or character in "()" for character in outside):
            continue
        tidied[index - 1] = (before[:-1], None)
        tidied[index + 1] = (after[1:], None)
    return tidied if joined else runs

class MathLine(ctk.CTkFrame):
    """
    Una linea de texto con todas sus fracciones apiladas en vez de con barra.

    El texto viene ya escrito de presentation.py; aqui solo se compone, partiendolo
    donde aparece una fraccion y poniendo un FractionCell en el hueco. Todo lo que
    hay entre fracciones se queda en la tipografia de ancho fijo en la que se
    coloco, asi que lo que estaba cuadrado dentro de un tramo sigue cuadrado.
    """

    def __init__(
        self,
        master: Any,
        text: str,
        font: str = "mono",
        color: Color = theme.INK,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        for run, fraction in _pieces(text):
            if fraction is not None:
                FractionCell(
                    self, fraction, color, "transparent", SMALLER.get(font, font)
                ).pack(side="left", padx=1)
            elif run:
                ctk.CTkLabel(
                    self, text=run, font=theme.font(font), text_color=color
                ).pack(side="left")

class MathBlock(ctk.CTkFrame):
    """
    Un bloque de lineas que coloco la capa de presentacion, compuesto con sus
    fracciones apiladas.

    Esos bloques estan cuadrados contando caracteres, y eso deja de ser cierto en
    cuanto una fraccion ocupa dos lineas en vez de una. Asi que aqui se cuadran
    otra vez, con una rejilla: el nombre de la fila se queda en su columna y los
    signos igual en otra.

    align es lo unico que la rejilla no puede deducir sola. Un sistema de
    ecuaciones se escribe con los lados izquierdos empujados a la derecha, para
    que los iguales queden uno debajo de otro; un despeje se escribe con sus
    lineas empezando en el mismo sitio. Las dos cosas eran ciertas del texto
    antes de llegar aqui, y quien lo entrega sabe cual de las dos es.
    """

    def __init__(
        self,
        master: Any,
        text: str,
        align: Literal["left", "right"] = "right",
        font: str = "mono_small",
        color: Color = theme.INK,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        for row, line in enumerate(text.splitlines()):
            if not line.strip():
                ctk.CTkFrame(self, width=1, height=10, fg_color="transparent").grid(
                    row=row, column=0
                )
                continue

            tag = ""
            match = _TAG.match(line)
            if match:
                tag, line = match[1], line[match.end() - 1:]
            if tag:
                MathLine(self, tag, font, color).grid(row=row, column=0, sticky="w")

            left, equals, right = line.partition("=")
            if align == "left" or not equals:
                # Escrito como estaba escrito: de corrido, conservando sus espacios.
                MathLine(self, line.strip(), font, color).grid(
                    row=row, column=1, columnspan=3, sticky="w", padx=(10, 0)
                )
                continue

            MathLine(self, left.strip(), font, color).grid(
                row=row, column=1, sticky="e", padx=(10, 0)
            )
            ctk.CTkLabel(
                self, text="=", font=theme.font(font), text_color=color
            ).grid(row=row, column=2, padx=6)
            MathLine(self, right.strip(), font, color).grid(row=row, column=3, sticky="w")

class MathChip(ctk.CTkFrame):
    """Una etiqueta cuyo unico dato puede ser una fraccion: x = 1/3."""

    def __init__(
        self,
        master: Any,
        text: str,
        color: Color = theme.INK,
        background: Color = theme.FIELD,
    ) -> None:
        super().__init__(master, fg_color=background, corner_radius=12)
        MathLine(self, text, "mono", color).pack(padx=14, pady=6)

class MatrixDisplay(ctk.CTkFrame):
    """Una matriz escrita por el programa, entre corchetes y con una barra opcional."""

    def __init__(
        self,
        master: Any,
        matrix: Matrix,
        bar_after: int | None = None,
        background: Color = theme.CARD,
        highlight: Sequence[tuple[int, int]] = (),
    ) -> None:
        super().__init__(master, fg_color="transparent")
        Bracket(self, "left", background).grid(row=0, column=0, sticky="ns")
        cells = ctk.CTkFrame(self, fg_color="transparent")
        cells.grid(row=0, column=1, padx=1, pady=4)
        Bracket(self, "right", background).grid(row=0, column=2, sticky="ns")

        # La barra entre A y b es una sola linea de arriba abajo, no un trozo por
        # fila: un trozo en cada fila fijaria la altura de todas. Dos pixeles de
        # ancho porque con uno CustomTkinter no dibuja absolutamente nada.
        bar = bar_after if bar_after is not None and 0 < bar_after < matrix.cols else None
        places: dict[int, int] = {}
        column = 0
        for j in range(1, matrix.cols + 1):
            if bar is not None and j == bar + 1:
                column += 1
            places[j] = column
            column += 1

        marked = set(highlight)
        for i in range(1, matrix.rows + 1):
            for j in range(1, matrix.cols + 1):
                value = matrix.elem(i, j)
                inside = (i, j) in marked
                colour = theme.ACCENT if inside else theme.INK
                background = theme.ACCENT_SOFT if inside else "transparent"
                if value.denominator == 1:
                    cell = ctk.CTkLabel(
                        cells,
                        text=format_scalar(value),
                        font=theme.font("mono"),
                        text_color=colour,
                        fg_color=background,
                        corner_radius=7,
                        padx=6,
                        anchor="e",
                    )
                else:
                    cell = FractionCell(
                        cells, value, colour, background, SMALLER["mono"]
                    )
                cell.grid(row=i - 1, column=places[j], sticky="e", padx=4, pady=1)

        if bar is not None:
            ctk.CTkFrame(cells, width=2, height=1, corner_radius=0, fg_color=theme.RULE).grid(
                row=0,
                column=places[bar + 1] - 1,
                rowspan=matrix.rows,
                sticky="ns",
                padx=4,
                pady=2,
            )

class ColumnDisplay(ctk.CTkFrame):
    """
    Una columna entre corchetes cuyas entradas son texto y no numeros: las
    incognitas x, y, z de A x = b, puestas donde iria un vector.

    Cada entrada pasa por MathLine, asi que una fraccion escrita en ella se
    apila igual que dentro de un MatrixDisplay.
    """

    def __init__(
        self,
        master: Any,
        entries: Sequence[str],
        color: Color = theme.INK,
        background: Color = theme.CARD,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        Bracket(self, "left", background).grid(row=0, column=0, sticky="ns")
        cells = ctk.CTkFrame(self, fg_color="transparent")
        cells.grid(row=0, column=1, padx=1, pady=4)
        Bracket(self, "right", background).grid(row=0, column=2, sticky="ns")
        for row, entry in enumerate(entries):
            MathLine(cells, entry, "mono", color).grid(
                row=row, column=0, sticky="e", padx=8, pady=1
            )

class Expression(ctk.CTkFrame):
    """
    Matrices y los simbolos entre ellas, escritos en fila como se escribe una
    ecuacion entre vectores: A · x = b, 3 · v₁ + 2 · v₂ = b.

    Cada pieza va centrada en su fila, asi que un + queda a la altura del centro
    de las columnas de al lado, y una matriz puede llevar debajo un rotulo con
    su nombre. Una combinacion larga se parte con new_line y sigue debajo de la
    primera pieza de la linea anterior.

    Cada metodo devuelve la propia expresion, asi que se escribe en cadena en el
    mismo orden en que se lee.
    """

    def __init__(self, master: Any, background: Color = theme.CARD) -> None:
        super().__init__(master, fg_color="transparent")
        self._background = background
        self._line = 0
        self._column = 0

    def matrix(self, matrix: Matrix, caption: str = "", highlight: bool = False) -> "Expression":
        marked = (
            [(i, j) for i in range(1, matrix.rows + 1) for j in range(1, matrix.cols + 1)]
            if highlight
            else []
        )
        return self._place(
            MatrixDisplay(self, matrix, background=self._background, highlight=marked),
            caption,
        )

    def column(
        self, entries: Sequence[str], caption: str = "", color: Color = theme.INK
    ) -> "Expression":
        return self._place(ColumnDisplay(self, entries, color, self._background), caption)

    def symbol(self, text: str, color: Color = theme.INK) -> "Expression":
        return self._place(MathLine(self, text, "mono", color), "", padx=6)

    def new_line(self) -> "Expression":
        self._line += 1
        self._column = 0
        return self

    def _place(self, widget: Any, caption: str, padx: int = 2) -> "Expression":
        row = self._line * 2
        widget.grid(row=row, column=self._column, padx=padx, pady=(0 if row == 0 else 12, 0))
        if caption:
            MathLine(self, caption, "mono_small", theme.MUTED).grid(
                row=row + 1, column=self._column, pady=(2, 0)
            )
        self._column += 1
        return self

class Wide(ctk.CTkFrame):
    """
    Una franja que se desliza a lo ancho cuando lo que lleva no cabe en ella.

    Una matriz de 6 x 6 con fracciones, o cuatro matrices en fila como P A = L U,
    pasan de largo del ancho de la ventana. Hasta ahora eso se cortaba sin decir
    nada: el dibujo seguia ahi, pero tapado por el borde de la tarjeta.

    Lo que hay dentro vive sobre un lienzo, que es lo unico en Tk que puede ser
    mas ancho que su hueco, y debajo aparece una barra cuando hace falta y solo
    entonces. Si el contenido cabe, esto no se nota: el lienzo se estira hasta el
    ancho disponible para que lo de dentro se siga alineando igual.

    Como el lienzo guarda un color y no una pareja, se repinta al cambiar de
    tema, igual que los corchetes de una matriz.
    """

    def __init__(self, master: Any, background: Color = theme.CARD) -> None:
        super().__init__(master, fg_color="transparent")
        self._background = background

        self._strip = tkinter.Canvas(self, highlightthickness=0, borderwidth=0, height=1)
        self._strip.pack(fill="both", expand=True)
        # Los dos colores puestos a mano, y ninguno "transparent": lo de dentro
        # resuelve su fondo preguntandole al padre, y un lienzo de Tk no sabe
        # responder a eso. Sin el bg_color asoma el gris por defecto en el canto,
        # una raya de un pixel por donde termina lo dibujado.
        #
        # Y el lienzo se llama _strip y no _canvas porque CTkFrame ya tiene un
        # _canvas suyo, el que dibuja su fondo: llamar igual al nuestro se lo
        # pisaba, y entonces winfo_children() dejaba de ver lo que hay dentro.
        self.content = ctk.CTkFrame(
            self._strip, fg_color=background, bg_color=background, corner_radius=0
        )
        self._window = self._strip.create_window(0, 0, anchor="nw", window=self.content)

        self._bar = ctk.CTkScrollbar(
            self,
            orientation="horizontal",
            command=self._strip.xview,
            height=10,
            button_color=theme.RULE,
            button_hover_color=theme.MUTED,
            fg_color="transparent",
        )
        self._strip.configure(xscrollcommand=self._bar.set)

        self.content.bind("<Configure>", lambda _event: self._fit())
        self._strip.bind("<Configure>", lambda _event: self._fit())
        for sequence in ("<Shift-Button-4>", "<Shift-Button-5>", "<Shift-MouseWheel>"):
            self._strip.bind_all(sequence, self._wheel, add=True)
        self.bind("<Destroy>", lambda _event: theme.off_change(self._repaint))
        theme.on_change(self._repaint)
        self._repaint()

    def _fit(self) -> None:
        """
        Ajusta el lienzo a lo que lleva dentro, y pone o quita la barra.

        El alto es el del contenido, porque esto no desliza hacia abajo: de eso
        se encarga la pagina entera. El ancho de lo de dentro es el suyo propio o
        el del hueco, el que sea mayor, para que lo que cabe siga ocupando todo
        el ancho como antes de existir esta franja.
        """
        if not self.winfo_exists():
            return
        needed = self.content.winfo_reqwidth()
        available = self._strip.winfo_width()
        self._strip.configure(height=self.content.winfo_reqheight())
        self._strip.itemconfigure(self._window, width=max(needed, available))
        self._strip.configure(scrollregion=(0, 0, max(needed, available), self.content.winfo_reqheight()))

        if needed > available + 1:
            self._bar.pack(fill="x", pady=(6, 0))
        else:
            self._bar.pack_forget()
            self._strip.xview_moveto(0.0)

    def _wheel(self, event: Any) -> None:
        """Con Shift, la rueda mueve a lo ancho la franja que este debajo del puntero."""
        if not self.winfo_exists() or not self._bar.winfo_ismapped():
            return
        under = event.widget.winfo_containing(event.x_root, event.y_root)
        while under is not None:
            if under is self:
                right = event.num == 5 or getattr(event, "delta", 0) < 0
                self._strip.xview_scroll(WHEEL_STEP if right else -WHEEL_STEP, "units")
                return
            under = getattr(under, "master", None)

    def _repaint(self) -> None:
        if self.winfo_exists():
            self._strip.configure(background=theme.resolve(self._background))

class ResultsPage(ctk.CTkFrame):
    """
    Lo que toda pagina de resultados hace igual: dibujar tarjetas y borrarlas.

    Debajo de la tarjeta de entrada, cada pagina apila tarjetas con lo que
    calculo, y las tira todas en cuanto alguien cambia un dato: un resultado
    deja de ser cierto en el momento en que deja de corresponder a lo escrito.
    Eso era siete copias del mismo metodo, una por pagina, hasta que una octava
    las hizo evidentes.

    `_add_card` da la tarjeta vacia, para quien dibuja dentro de ella a su
    manera; `_card` la da ya con margenes y titulo, que es lo que quiere casi
    todo el mundo; y `_titled_card` devuelve ademas el titulo, para el paso a
    paso, que escribe la cuenta en su insignia.
    """

    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._output: list[ctk.CTkBaseClass] = []

    def _add_card(self) -> Card:
        """La tarjeta vacia, para quien dibuja dentro de ella a su manera."""
        card = Card(self)
        card.pack(fill="x", pady=(16, 0))
        self._output.append(card)
        return card

    def _card(self, title: str = "", badge: str = "") -> ctk.CTkFrame:
        inside, _heading = self._titled_card(title, badge)
        return inside

    def _titled_card(self, title: str, badge: str = "") -> tuple[ctk.CTkFrame, SectionTitle]:
        """
        La tarjeta con su titulo, y dentro la franja donde se dibuja el resultado.

        El titulo se queda quieto y lo de abajo se desliza: una matriz de 6 x 6
        con fracciones, o cuatro matrices en fila como P A = L U, pasan del ancho
        de la ventana, y antes eso se cortaba sin avisar. Al deslizar, el titulo
        tiene que seguir diciendo que es lo que se esta mirando.
        """
        inside = ctk.CTkFrame(self._add_card(), fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        heading = SectionTitle(inside, title, badge)
        heading.pack(fill="x", pady=(0, 12))
        wide = Wide(inside)
        wide.pack(fill="x")
        return wide.content, heading

    def _muted(self, master: Any, text: str, width: int = 640) -> ctk.CTkLabel:
        """Una linea de explicacion, en gris y debajo de lo que explica."""
        label = ctk.CTkLabel(
            master, text=text, font=theme.font("small"), text_color=theme.MUTED,
            justify="left", anchor="w", wraplength=width,
        )
        label.pack(anchor="w")
        return label

    def _clear_output(self) -> None:
        """Un resultado deja de ser cierto en cuanto cambia lo que se escribio."""
        for card in self._output:
            card.destroy()
        self._output = []

class RomanNumeral(ctk.CTkFrame):
    """
    Un numero romano leido como la suma de sus piezas: XIV = X + IV = 14.

    Las seis parejas de resta van en el color de acento, porque son el unico sitio
    donde un simbolo menor va antes de uno mayor y la razon de que el numero no se
    lea simplemente de izquierda a derecha.

    Las dos paginas que muestran un numero romano usan esto, asi que XIV se
    presenta igual se este operando o convirtiendo.
    """

    def __init__(self, master: Any, numeral: Numeral, width: int = 90) -> None:
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(
            self, text=numeral.text, font=theme.font("mono"), text_color=theme.INK,
            width=width, anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            self, text="=", font=theme.font("mono"), text_color=theme.MUTED
        ).pack(side="left", padx=(0, 10))
        for index, piece in enumerate(numeral.pieces):
            if index:
                ctk.CTkLabel(
                    self, text="+", font=theme.font("mono"), text_color=theme.MUTED
                ).pack(side="left", padx=6)
            Chip(
                self,
                f"{piece.text} = {piece.value}",
                theme.ACCENT if piece.subtractive else theme.INK,
                theme.ACCENT_SOFT if piece.subtractive else theme.FIELD,
            ).pack(side="left")
        ctk.CTkLabel(
            self, text=f"=  {numeral.value}", font=theme.font("mono"), text_color=theme.ACCENT
        ).pack(side="left", padx=(12, 0))

class SegmentedControl(ctk.CTkSegmentedButton):
    """La fila de opciones de la parte de arriba de una pagina: una operacion, o un metodo."""

    def __init__(
        self,
        master: Any,
        values: Sequence[str],
        command: Callable[[str], None],
    ) -> None:
        super().__init__(
            master,
            values=list(values),
            command=command,
            height=34,
            corner_radius=theme.PILL_RADIUS,
            border_width=3,
            font=theme.font("body"),
            fg_color=theme.FIELD,
            selected_color=theme.CARD,
            selected_hover_color=theme.CARD,
            unselected_color=theme.FIELD,
            unselected_hover_color=theme.FIELD_HOVER,
            text_color=theme.INK,
        )
        self.set(values[0])

class PrimaryButton(ctk.CTkButton):
    """El boton azul que lanza el calculo."""

    def __init__(self, master: Any, text: str, command: Callable[[], None]) -> None:
        super().__init__(
            master,
            text=text,
            command=command,
            height=38,
            corner_radius=19,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.ON_ACCENT,
            font=theme.font("button"),
        )

class ErrorBanner(ctk.CTkLabel):
    """La linea roja que aparece cuando lo que se escribio no sirve."""

    def __init__(self, master: Any) -> None:
        super().__init__(
            master,
            text="",
            font=theme.font("body"),
            text_color=theme.RED,
            fg_color=theme.RED_SOFT,
            corner_radius=12,
            justify="left",
            anchor="w",
            padx=14,
            pady=10,
        )
        self._before: Any = None

    def appear_before(self, widget: Any) -> None:
        """Donde va el aviso una vez que tiene algo que decir."""
        self._before = widget

    def show(self, message: str) -> None:
        self.configure(text=message)
        if not self.winfo_ismapped():
            if self._before is not None:
                self.pack(fill="x", pady=(14, 0), before=self._before)
            else:
                self.pack(fill="x", pady=(14, 0))

    def hide(self) -> None:
        self.pack_forget()

class Chip(ctk.CTkLabel):
    """Una cajita redondeada para un solo dato corto: x = 29, Dimension: 2 x 3."""

    def __init__(
        self,
        master: Any,
        text: str,
        color: Color = theme.INK,
        background: Color = theme.FIELD,
    ) -> None:
        super().__init__(
            master,
            text=text,
            font=theme.font("mono"),
            text_color=color,
            fg_color=background,
            corner_radius=12,
            padx=14,
            pady=8,
        )

class StepWalker(ctk.CTkFrame):
    """
    Una eliminacion, recorrida operacion por operacion.

    Todo esto es StepLog.snapshot(k): el registro ya guarda la matriz despues de
    cada operacion, asi que ir y venir no recalcula nada y no puede contradecir
    lo que la eliminacion hizo de verdad.

    La matriz inicial cuenta como paso. Es sobre la que actua la primera
    operacion, y un recorrido que empezara despues nunca ensenaria lo escrito.
    """

    def __init__(
        self,
        master: Any,
        log: StepLog,
        bar_after: int | None = None,
        first_caption: str = "Matriz inicial",
        on_step: Callable[[int, int], None] | None = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._log = log
        self._bar_after = bar_after
        self._first_caption = first_caption
        self._on_step = on_step
        self._index = 0

        self._operation = ctk.CTkFrame(self, fg_color=theme.FIELD, corner_radius=12)
        self._operation.pack(fill="x")
        self._caption = ""

        self._holder = ctk.CTkFrame(self, fg_color="transparent")
        self._holder.pack(anchor="w", pady=(14, 0))

        self._dots = ctk.CTkFrame(self, fg_color="transparent")
        self._dots.pack(pady=(14, 0))

        self._list = ctk.CTkFrame(self, fg_color="transparent")

        self._navigation = ctk.CTkFrame(self, fg_color="transparent")
        self._navigation.pack(fill="x", pady=(14, 0))
        self._previous = self._link(self._navigation, "‹  Anterior", -1)
        self._previous.pack(side="left")
        self._next = self._link(self._navigation, "Siguiente  ›", 1)
        self._next.pack(side="right")
        self._unfold = ctk.CTkButton(
            self._navigation,
            text=ALL_STEPS,
            width=1,
            height=30,
            corner_radius=15,
            fg_color="transparent",
            hover_color=theme.FIELD,
            text_color=theme.MUTED,
            font=theme.font("button"),
            command=self._toggle_all,
        )
        self._unfold.pack(side="left", expand=True)

        self.show()

    def _toggle_all(self) -> None:
        """
        Cambia recorrer los pasos por leerlos todos de una vez.

        Quien sigue el metodo quiere una operacion cada vez; quien comprueba una
        respuesta quiere pasar la vista por todas. Ninguna de las dos es el modo
        correcto para la otra, asi que estan las dos y elegir cuesta un clic.
        """
        # Todo se vuelve a colocar delante de la fila de controles, que no se
        # mueve: eso es lo que mantiene las dos vistas en el mismo orden.
        if self._list.winfo_ismapped():
            self._list.pack_forget()
            self._operation.pack(fill="x", before=self._navigation)
            self._holder.pack(anchor="w", pady=(14, 0), before=self._navigation)
            self._dots.pack(pady=(14, 0), before=self._navigation)
            self._previous.pack(side="left")
            self._next.pack(side="right")
            self._unfold.configure(text=ALL_STEPS)
            self.show()
            return

        self._operation.pack_forget()
        self._holder.pack_forget()
        self._dots.pack_forget()
        self._previous.pack_forget()
        self._next.pack_forget()
        self._unfold.configure(text=ONE_STEP)
        self._draw_list()
        self._list.pack(fill="x", pady=(4, 0), before=self._navigation)
        if self._on_step is not None:
            self._on_step(self.total() - 1, self.total())

    def _draw_list(self) -> None:
        """Cada paso debajo del anterior, con su titulo y su matriz."""
        for widget in self._list.winfo_children():
            widget.destroy()

        for index in range(self.total()):
            block = ctk.CTkFrame(self._list, fg_color="transparent")
            block.pack(fill="x", pady=(0, 16))
            caption = ctk.CTkFrame(block, fg_color=theme.FIELD, corner_radius=12)
            caption.pack(fill="x")
            MathLine(
                caption,
                self._first_caption
                if index == 0
                else f"Paso {index}:   {pretty_label(self._log[index - 1].label)}",
            ).pack(anchor="w", padx=16, pady=10)
            MatrixDisplay(
                block, self._log.snapshot(index), bar_after=self._bar_after
            ).pack(anchor="w", pady=(10, 0))

    def total(self) -> int:
        """Cuantas matrices hay que recorrer, contando la inicial."""
        return len(self._log) + 1

    def go(self, index: int) -> None:
        """Saltar directamente a una de ellas."""
        self._index = max(0, min(self.total() - 1, index))
        self.show()

    def move(self, delta: int) -> None:
        self.go(self._index + delta)

    def caption(self) -> str:
        """Lo que dice ahora mismo la caja de la operacion."""
        return self._caption

    def show(self) -> None:
        """Dibuja el paso en el que esta el recorrido."""
        self._caption = (
            self._first_caption
            if self._index == 0
            else pretty_label(self._log[self._index - 1].label)
        )
        for widget in self._operation.winfo_children():
            widget.destroy()
        MathLine(self._operation, self._caption).pack(anchor="w", padx=16, pady=10)

        for widget in self._holder.winfo_children():
            widget.destroy()
        MatrixDisplay(
            self._holder, self._log.snapshot(self._index), bar_after=self._bar_after
        ).pack(anchor="w")

        self._draw_dots()
        total = self.total()
        self._previous.configure(state="normal" if self._index > 0 else "disabled")
        self._next.configure(state="normal" if self._index < total - 1 else "disabled")
        if self._on_step is not None:
            self._on_step(self._index, total)

    def _link(self, master: ctk.CTkFrame, text: str, delta: int) -> ctk.CTkButton:
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
            command=lambda: self.move(delta),
        )

    def _draw_dots(self) -> None:
        """Un punto por paso, mientras sean pocos y eso ayude."""
        for widget in self._dots.winfo_children():
            widget.destroy()
        total = self.total()
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
                command=lambda index=index: self.go(index),
            ).pack(side="left", padx=1)
