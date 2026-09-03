"""
The pieces every page is built from.

CustomTkinter has buttons and entries; it has no matrix. What is here is the
handful of shapes this calculator needs and the toolkit does not provide — a
card, a stepper, a grid of cells inside brackets, a matrix drawn read-only —
each one knowing how to draw itself and nothing else.

No arithmetic lives here. `MatrixEntryGrid.matrix()` hands back a `Matrix` and
`MatrixDisplay` takes one; what happens in between is `core`'s business.
"""

from collections.abc import Callable, Sequence
from typing import Any, Literal

import customtkinter as ctk

from core.matrix import Matrix
from core.scalar import format_scalar, to_scalar

from . import theme
from .theme import Color

# Ten rows and ten columns: the same ceiling the terminal asks for.
SIZE_LIMIT = 10

class CellError(ValueError):
    """A cell of a typed matrix does not hold a number. The message is Spanish."""

class Card(ctk.CTkFrame):
    """The rounded white panel every section of a page sits inside."""

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
    """The title of a page and the line underneath explaining what it does."""

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
        """Explain something else under the same title: one page, two methods."""
        self._subtitle.configure(text=subtitle)

class SectionTitle(ctk.CTkFrame):
    """The heading of a card, with an optional grey pill on the right."""

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
    One half of the `[ ]` a matrix is written inside.

    Three straight lines on a canvas, which is the one thing in this package
    that has to be repainted by hand when the theme changes: a canvas holds a
    colour, not a pair of them.
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
    """`−  3  +`: how many rows or columns a matrix has."""

    def __init__(
        self,
        master: Any,
        value: int,
        minimum: int,
        maximum: int,
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
        """Move the readout without calling back: for a size that followed another."""
        self._value = max(self._minimum, min(self._maximum, value))
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
        value = max(self._minimum, min(self._maximum, self._value + delta))
        if value == self._value:
            return
        self._value = value
        self._refresh()
        self._command(value)

    def _refresh(self) -> None:
        self._readout.configure(text=str(self._value))
        self._less.configure(state="normal" if self._value > self._minimum else "disabled")
        self._more.configure(state="normal" if self._value < self._maximum else "disabled")

class MatrixEntryGrid(ctk.CTkFrame):
    """
    A matrix somebody types into, with the steppers that resize it.

    The text of the cells outlives the widgets: growing from 2x2 to 3x3 and back
    finds the four original numbers still there, because what was typed is kept
    in a dictionary and the entries are rebuilt around it.
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
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.title = title
        self._rows = rows
        self._cols = cols
        self._on_change = on_change
        self._on_resize = on_resize
        self._entries: list[list[ctk.CTkEntry]] = []
        self._texts: dict[tuple[int, int], str] = {
            (i, j): str(text)
            for i, row in enumerate(values)
            for j, text in enumerate(row)
        }

        # The header is packed above the body rather than spanning its columns:
        # a header wider than the matrix would otherwise stretch the cells and
        # leave the brackets standing away from them.
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

    # ----- Reading -----

    def matrix(self) -> Matrix:
        """What was typed, as a `Matrix`. Raises `CellError` naming a bad cell."""
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

    # ----- Resizing -----

    def set_size(self, rows: int, cols: int) -> None:
        """Resize from outside, for the matrix whose shape follows another one."""
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
        stepper = Stepper(header, value, 1, SIZE_LIMIT, command)
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

    # ----- Drawing -----

    def _typed(self, _event: object) -> None:
        """Any keystroke undoes the result: it was computed from other numbers."""
        if self._on_change is not None:
            self._on_change()

    def _capture(self) -> None:
        """Remember what is in the entries before they are thrown away."""
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

class MatrixDisplay(ctk.CTkFrame):
    """A matrix the program wrote, in brackets, with an optional bar down it."""

    def __init__(
        self,
        master: Any,
        matrix: Matrix,
        bar_after: int | None = None,
        background: Color = theme.CARD,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        Bracket(self, "left", background).grid(row=0, column=0, sticky="ns")
        cells = ctk.CTkFrame(self, fg_color="transparent")
        cells.grid(row=0, column=1, padx=1, pady=4)
        Bracket(self, "right", background).grid(row=0, column=2, sticky="ns")

        # The bar between A and b is one line down the whole matrix, not one per
        # row: a piece of it in every row would set the height of every row. Two
        # pixels wide because CustomTkinter draws nothing at all for one.
        bar = bar_after if bar_after is not None and 0 < bar_after < matrix.cols else None
        places: dict[int, int] = {}
        column = 0
        for j in range(1, matrix.cols + 1):
            if bar is not None and j == bar + 1:
                column += 1
            places[j] = column
            column += 1

        for i in range(1, matrix.rows + 1):
            for j in range(1, matrix.cols + 1):
                ctk.CTkLabel(
                    cells,
                    text=format_scalar(matrix.elem(i, j)),
                    font=theme.font("mono"),
                    text_color=theme.INK,
                    anchor="e",
                ).grid(row=i - 1, column=places[j], sticky="e", padx=9, pady=1)

        if bar is not None:
            ctk.CTkFrame(cells, width=2, height=1, corner_radius=0, fg_color=theme.RULE).grid(
                row=0,
                column=places[bar + 1] - 1,
                rowspan=matrix.rows,
                sticky="ns",
                padx=4,
                pady=2,
            )

class SegmentedControl(ctk.CTkSegmentedButton):
    """The pill of choices at the top of a page: an operation, or a method."""

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
    """The blue button that starts the calculation."""

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
    """The red line that appears when what was typed cannot be used."""

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
        """Where the banner belongs once it has something to say."""
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
    """A small rounded box for one short fact: `x = 29`, `Dimensión: 2 × 3`."""

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

class MonoBlock(ctk.CTkLabel):
    """A block of text the presentation layer already laid out, kept as it is."""

    def __init__(self, master: Any, text: str) -> None:
        super().__init__(
            master,
            text=text,
            font=theme.font("mono_small"),
            text_color=theme.INK,
            justify="left",
            anchor="w",
        )
