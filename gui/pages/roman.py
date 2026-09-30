"""
Adding, subtracting and multiplying Roman numerals, working shown.

A sum or a difference is done on what the numerals are worth: each one is read
as the sum of its pieces, the two values are operated, and the answer is
written back as a numeral. A multiplication of one symbol by another is done
as the repeated addition it was taught as, so the sum itself is the working.

Two things the Romans did not write come up as answers rather than as errors:
zero and negative numbers, and anything above MMMCMXCIX. The page says which
one it is and gives the value in our numbers, because that a difference cannot
be written is the answer to `V - X`.

The Spanish lives here because no other front end says any of it.
"""

from typing import Any

import customtkinter as ctk

from core.roman import (
    LARGEST,
    SYMBOLS,
    BadLetter,
    BadOrder,
    EmptyRoman,
    NotCanonical,
    NotOneSymbol,
    Numeral,
    Operation,
    difference_of,
    product_of,
    read,
    sum_of,
    to_roman,
)

from .. import theme
from ..widgets import (
    Card,
    Chip,
    ErrorBanner,
    PageHeader,
    PrimaryButton,
    SectionTitle,
    SegmentedControl,
)

PLUS = "Suma"
MINUS = "Resta"
TIMES = "Multiplicación"

ROMAN_SUBTITLES = {
    PLUS: "Sumar dos números romanos: se leen, se suman sus valores y el total se escribe en romano.",
    MINUS: "Restar dos números romanos: los romanos no escribían el cero ni los negativos.",
    TIMES: "Multiplicar dos símbolos romanos por notación de suma: X × V es X + X + X + X + X.",
}

# The sign each operation is written with, and the call that does it.
ROMAN_SIGNS = {PLUS: "+", MINUS: "−", TIMES: "×"}
ROMAN_OPERATIONS = {PLUS: sum_of, MINUS: difference_of, TIMES: product_of}

# What the boxes hold before anybody types, so the first click shows something.
FIRST_EXAMPLE = "XIV"
SECOND_EXAMPLE = "IX"
FIRST_SYMBOL = "X"
SECOND_SYMBOL = "V"

# What each symbol is worth, said once under the boxes.
ROMAN_HELP = (
    "Símbolos: I = 1, V = 5, X = 10, L = 50, C = 100, D = 500, M = 1000.\n"
    "Se escriben del mayor al menor, y las únicas restas son IV, IX, XL, XC, CD y CM."
)
SYMBOL_HELP = "Un solo símbolo en cada casilla: I, V, X, L, C, D o M."

# A thousand X's on screen say nothing that the first few do not; M × M would
# ask for exactly that.
TERMS_SHOWN = 30

# How many terms of the repeated addition fit on one line before it wraps.
ROMAN_TERMS_PER_LINE = 10

class RomanPage(ctk.CTkFrame):
    """The page that adds, subtracts and multiplies Roman numerals."""

    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._operation = PLUS
        self._output: list[Card] = []

        self._header = PageHeader(self, "Ⅻ", "Números Romanos", ROMAN_SUBTITLES[PLUS])
        self._header.pack(anchor="w", pady=(0, 18))

        SegmentedControl(self, (PLUS, MINUS, TIMES), self._choose).pack(
            anchor="w", pady=(0, 16)
        )

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)

        boxes = ctk.CTkFrame(inside, fg_color="transparent")
        boxes.pack(anchor="w")
        self._first = self._box(boxes, 0, FIRST_EXAMPLE)
        self._sign = ctk.CTkLabel(
            boxes, text=ROMAN_SIGNS[PLUS], font=theme.font("title"), text_color=theme.MUTED
        )
        self._sign.grid(row=0, column=1, padx=16)
        self._second = self._box(boxes, 2, SECOND_EXAMPLE)

        self._help = ctk.CTkLabel(
            inside,
            text=ROMAN_HELP,
            font=theme.font("small"),
            text_color=theme.MUTED,
            justify="left",
            anchor="w",
        )
        self._help.pack(anchor="w", pady=(14, 0))

        self._error = ErrorBanner(inside)

        self._buttons = ctk.CTkFrame(inside, fg_color="transparent")
        self._buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(self._buttons, "Calcular  →", self._calculate).pack(side="right")
        self._error.appear_before(self._buttons)

    def _box(self, master: Any, column: int, example: str) -> ctk.CTkEntry:
        """One of the two numerals, typed in capitals whatever the keyboard sends."""
        entry = ctk.CTkEntry(
            master,
            width=200,
            height=46,
            corner_radius=theme.FIELD_RADIUS,
            fg_color=theme.FIELD,
            border_width=1,
            border_color=theme.BORDER,
            text_color=theme.INK,
            font=theme.font("mono"),
            justify="center",
        )
        entry.insert(0, example)
        entry.bind("<KeyRelease>", self._typed)
        entry.bind("<Return>", lambda _event: self._calculate())
        entry.grid(row=0, column=column)
        return entry

    # ----- Choosing an operation -----

    def _choose(self, operation: str) -> None:
        self._operation = operation
        self._header.set_subtitle(ROMAN_SUBTITLES[operation])
        self._sign.configure(text=ROMAN_SIGNS[operation])
        self._help.configure(
            text=ROMAN_HELP + ("\n" + SYMBOL_HELP if operation == TIMES else "")
        )
        self._clear_output()
        self._error.hide()

        # A multiplication takes one symbol in each box, so the example changes
        # with it: XIV × IX is not something this page offers.
        single = operation == TIMES
        if single and (len(self._first.get().strip()) > 1 or len(self._second.get().strip()) > 1):
            self._write(self._first, FIRST_SYMBOL)
            self._write(self._second, SECOND_SYMBOL)
        elif not single and self._first.get().strip() == FIRST_SYMBOL:
            self._write(self._first, FIRST_EXAMPLE)
            self._write(self._second, SECOND_EXAMPLE)

    def _write(self, entry: ctk.CTkEntry, text: str) -> None:
        entry.delete(0, "end")
        entry.insert(0, text)

    def _typed(self, event: Any) -> None:
        """Roman numerals are capitals, so lowercase is corrected as it is typed."""
        if event.keysym == "Return":
            return
        entry = event.widget.master
        if isinstance(entry, ctk.CTkEntry):
            text = entry.get()
            if text != text.upper():
                position = entry.index("insert")
                self._write(entry, text.upper())
                entry.icursor(position)
        self._clear_output()

    # ----- Calculating -----

    def _calculate(self) -> None:
        self._clear_output()
        try:
            done = ROMAN_OPERATIONS[self._operation](self._first.get(), self._second.get())
        except EmptyRoman:
            self._error.show("Escribe un número romano en las dos casillas.")
            return
        except BadLetter as problem:
            self._error.show(
                f"'{problem.letter}' no es un símbolo romano. "
                "Solo se usan I, V, X, L, C, D y M."
            )
            return
        except NotCanonical as problem:
            self._error.show(
                f"'{problem.numeral}' no se escribe así: ese número es "
                f"{problem.canonical}."
            )
            return
        except BadOrder as problem:
            self._error.show(
                f"'{problem.numeral}' no es un número romano: los símbolos van del mayor "
                "al menor, y las únicas restas son IV, IX, XL, XC, CD y CM."
            )
            return
        except NotOneSymbol as problem:
            self._error.show(
                f"Para multiplicar, cada casilla lleva un solo símbolo, y "
                f"'{problem.numeral}' tiene {len(problem.numeral)}. {SYMBOL_HELP}"
            )
            return

        self._error.hide()
        self._draw_answer(done)
        self._draw_reading(done)
        if done.terms:
            self._draw_terms(done)
        if done.writable:
            self._draw_check(done)

    # ----- The answer -----

    def _draw_answer(self, done: Operation) -> None:
        """The operation in one line, in Roman above and in our numbers below."""
        inside = self._card("Resultado")
        sign = ROMAN_SIGNS[self._operation]

        line = ctk.CTkFrame(inside, fg_color="transparent")
        line.pack(anchor="w")
        written = f"{done.left.text}  {sign}  {done.right.text}  =  "
        ctk.CTkLabel(
            line, text=written, font=theme.font("title"), text_color=theme.INK
        ).pack(side="left")
        ctk.CTkLabel(
            line,
            text=done.numeral if done.writable else "—",
            font=theme.font("title"),
            text_color=theme.ACCENT if done.writable else theme.RED,
        ).pack(side="left")

        self._muted(
            inside,
            f"En nuestros números: {done.left.value} {sign} {done.right.value} = {done.value}",
        ).pack_configure(pady=(10, 0))

        if not done.writable:
            self._draw_unwritable(inside, done)

    def _draw_unwritable(self, inside: Any, done: Operation) -> None:
        """
        Why an answer has no numeral, which is an answer and not a failure.

        Zero and the negatives had no symbol at all, and neither did anything
        above MMMCMXCIX, so the value is given in our numbers and the reason is
        named.
        """
        if done.value <= 0:
            reason = (
                "Los romanos no escribían el cero ni los números negativos, así que "
                f"{done.value} no tiene número romano. Resta al revés para obtener "
                "un resultado que sí se pueda escribir."
            )
        else:
            reason = (
                f"El número romano más grande es MMMCMXCIX = {LARGEST}: no hay símbolo "
                f"para {done.value}, así que este resultado no se puede escribir en romano."
            )
        Chip(inside, "Sin número romano", theme.RED, theme.RED_SOFT).pack(
            anchor="w", pady=(14, 10)
        )
        self._muted(inside, reason)

    # ----- How each numeral is read -----

    def _draw_reading(self, done: Operation) -> None:
        """Each numeral broken into its pieces, which is how its value is read."""
        inside = self._card("Cómo se lee cada número")
        self._muted(
            inside,
            "Cada número romano es la suma de sus piezas. Las seis parejas IV, IX, XL, "
            "XC, CD y CM valen una resta: IX es 10 − 1.",
        ).pack_configure(pady=(0, 14))
        for numeral in (done.left, done.right):
            self._draw_pieces(inside, numeral)

    def _draw_pieces(self, inside: Any, numeral: Numeral) -> None:
        row = ctk.CTkFrame(inside, fg_color="transparent")
        row.pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(
            row, text=numeral.text, font=theme.font("mono"), text_color=theme.INK, width=90,
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            row, text="=", font=theme.font("mono"), text_color=theme.MUTED
        ).pack(side="left", padx=(0, 10))
        for index, piece in enumerate(numeral.pieces):
            if index:
                ctk.CTkLabel(
                    row, text="+", font=theme.font("mono"), text_color=theme.MUTED
                ).pack(side="left", padx=6)
            Chip(
                row,
                f"{piece.text} = {piece.value}",
                theme.ACCENT if piece.subtractive else theme.INK,
                theme.ACCENT_SOFT if piece.subtractive else theme.FIELD,
            ).pack(side="left")
        ctk.CTkLabel(
            row, text=f"=  {numeral.value}", font=theme.font("mono"), text_color=theme.ACCENT
        ).pack(side="left", padx=(12, 0))

    # ----- The repeated addition -----

    def _draw_terms(self, done: Operation) -> None:
        """
        The multiplication written as the sum it stands for.

        `X × V` is X added five times, so the terms are what the operation is,
        not a picture of it. A product that would need hundreds of terms shows
        the first few and says how many there are, because the rest say the
        same thing.
        """
        inside = self._card("Notación de suma", f"{len(done.terms)} sumandos")
        self._muted(
            inside,
            f"Multiplicar por {done.right.text} = {done.right.value} es sumar "
            f"{done.left.text} {done.right.value} veces:",
        ).pack_configure(pady=(0, 12))

        shown = list(done.terms[:TERMS_SHOWN])
        lines = []
        for start in range(0, len(shown), ROMAN_TERMS_PER_LINE):
            lines.append(" + ".join(shown[start:start + ROMAN_TERMS_PER_LINE]))
        text = "\n".join(lines)
        if len(done.terms) > TERMS_SHOWN:
            text += f"\n… y así hasta {len(done.terms)} veces."
        ctk.CTkLabel(
            inside, text=text, font=theme.font("mono"), text_color=theme.INK,
            justify="left", anchor="w",
        ).pack(anchor="w")

        total = f"= {done.numeral}" if done.writable else f"= {done.value} (sin número romano)"
        ctk.CTkLabel(
            inside,
            text=f"{done.left.value} × {done.right.value} = {done.value}   {total}",
            font=theme.font("mono"),
            text_color=theme.ACCENT,
            anchor="w",
        ).pack(anchor="w", pady=(12, 0))

    # ----- Reading the answer back -----

    def _draw_check(self, done: Operation) -> None:
        """
        The answer read back, which checks the writing against the reading.

        The value was turned into a numeral; reading that numeral has to give
        the value again, and it is done with the same code the operands went
        through rather than with the number that produced it.
        """
        inside = self._card("Comprobación")
        back = read(done.numeral)
        self._muted(
            inside,
            f"{done.value} escrito en romano es {to_roman(done.value)}, y leído otra vez "
            f"vuelve a dar {back.value}:",
        ).pack_configure(pady=(0, 14))
        self._draw_pieces(inside, back)
        Chip(inside, f"{done.numeral} = {back.value}  ✓", theme.GREEN).pack(
            anchor="w", pady=(4, 0)
        )

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
            master, text=text, font=theme.font("small"), text_color=theme.MUTED,
            justify="left", anchor="w", wraplength=640,
        )
        label.pack(anchor="w")
        return label

    def _clear_output(self) -> None:
        """A result stops being true the moment either numeral is retyped."""
        for card in self._output:
            card.destroy()
        self._output = []
