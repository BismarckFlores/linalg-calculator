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
from core.scalar import Scalar, format_scalar, to_scalar
from core.steps import StepLog
from ui.presentation import pretty_label

from . import theme
from .theme import Color

# Ten rows and ten columns: the same ceiling the terminal asks for.
SIZE_LIMIT = 10

# The two ways of reading a step by step: one at a time, or all of it at once.
ALL_STEPS = "Ver todos los pasos  ▾"
ONE_STEP = "Ver uno a uno  ▴"

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

class FractionCell(ctk.CTkFrame):
    """
    One entry written the way a fraction is written by hand: one number over
    another, with a rule between them.

    `1/3` on a single line is what a terminal can manage and what the file
    handed in prints. A window can do better, and a column of `22/15` and
    `-17/15` is much easier to read stacked than slashed.

    The rule is a two-pixel frame rather than a line on a canvas: it takes the
    same (light, dark) colour pair as everything else and follows the theme
    without anybody repainting it. One pixel would draw nothing at all.
    """

    def __init__(
        self,
        master: Any,
        value: Scalar,
        color: Color = theme.INK,
        background: Color = "transparent",
    ) -> None:
        super().__init__(master, fg_color=background, corner_radius=7)
        ctk.CTkLabel(
            self,
            text=str(value.numerator),
            font=theme.font("mono"),
            text_color=color,
        ).pack(padx=7)
        # width=1 because a CTkFrame asks for 200 pixels when nobody says
        # otherwise, and `fill="x"` would then set the width of the whole cell.
        ctk.CTkFrame(self, width=1, height=2, fg_color=color, corner_radius=0).pack(
            fill="x", padx=7
        )
        ctk.CTkLabel(
            self,
            text=str(value.denominator),
            font=theme.font("mono"),
            text_color=color,
        ).pack(padx=7, pady=(0, 2))

class MatrixDisplay(ctk.CTkFrame):
    """A matrix the program wrote, in brackets, with an optional bar down it."""

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
                    cell = FractionCell(cells, value, colour, background)
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

class StepWalker(ctk.CTkFrame):
    """
    One elimination, walked one operation at a time.

    All of it is `StepLog.snapshot(k)`: the log already holds the matrix after
    every operation, so moving back and forth recomputes nothing and cannot
    disagree with what the elimination actually did.

    The starting matrix counts as a step. It is what the first operation acts
    on, and a walk that began after it would never show what was typed.
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

        self._operation = ctk.CTkLabel(
            self,
            text="",
            font=theme.font("mono"),
            text_color=theme.INK,
            fg_color=theme.FIELD,
            corner_radius=12,
            anchor="w",
            padx=16,
            pady=12,
        )
        self._operation.pack(fill="x")

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
        Swap walking the steps for reading them all at once.

        Somebody following the method wants one operation at a time; somebody
        checking an answer wants to scroll past the lot. Neither is the right
        default for the other, so both are here and the choice is one click.
        """
        # Everything is put back in front of the row of controls, which never
        # moves: that is what keeps the two views in the same order on screen.
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
        """Every step under the one before it, captioned and drawn."""
        for widget in self._list.winfo_children():
            widget.destroy()

        for index in range(self.total()):
            block = ctk.CTkFrame(self._list, fg_color="transparent")
            block.pack(fill="x", pady=(0, 16))
            ctk.CTkLabel(
                block,
                text=self._first_caption
                if index == 0
                else f"Paso {index}:   {pretty_label(self._log[index - 1].label)}",
                font=theme.font("mono"),
                text_color=theme.INK,
                fg_color=theme.FIELD,
                corner_radius=12,
                anchor="w",
                padx=16,
                pady=10,
            ).pack(fill="x")
            MatrixDisplay(
                block, self._log.snapshot(index), bar_after=self._bar_after
            ).pack(anchor="w", pady=(10, 0))

    def total(self) -> int:
        """How many matrices there are to walk, the starting one included."""
        return len(self._log) + 1

    def go(self, index: int) -> None:
        """Jump straight to one of them."""
        self._index = max(0, min(self.total() - 1, index))
        self.show()

    def move(self, delta: int) -> None:
        self.go(self._index + delta)

    def caption(self) -> str:
        """What the operation box says right now."""
        return self._operation.cget("text")

    def show(self) -> None:
        """Draw the step the walk stands on."""
        self._operation.configure(
            text=self._first_caption
            if self._index == 0
            else pretty_label(self._log[self._index - 1].label)
        )

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
        """One dot per step, while there are few enough for it to help."""
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
