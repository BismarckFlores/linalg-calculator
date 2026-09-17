"""
Moving a whole number between base 10 and any base from 2 to 36, working shown.

From decimal, by repeated division: every division is written out as the
equation it is, and the remainders are read from the bottom up. To decimal, by
the linear combination of powers the numeral stands for, written out in full
and then worked down to a single number.

Each direction checks itself with the other. A number converted to base 2 is
read back into decimal right under it, which proves the digits without trusting
the divisions that produced them.

Binary, octal and hexadecimal are one click away, because they are the ones the
course asks for. Any other base is typed into a field of its own.

A negative number is converted the way it is by hand: the digits are those of
its absolute value, and the minus goes in front of them and in front of the
whole combination, `-2B₁₆ = -(2·16¹ + 11·16⁰) = -43`.

The Spanish lives here because no other front end says any of it.
"""

from typing import Any

import customtkinter as ctk

from core.bases import (
    DIGITS,
    HIGHEST_BASE,
    LOWEST_BASE,
    BadDigit,
    EmptyNumeral,
    FromBase,
    NumeralError,
    ToBase,
    from_base,
    to_base,
)
from ui.presentation import SUBSCRIPTS

from .. import theme
from ..theme import Color
from ..widgets import (
    Card,
    Chip,
    ErrorBanner,
    PageHeader,
    PrimaryButton,
    SectionTitle,
    SegmentedControl,
)

TO_BASE = "Decimal → otra base"
TO_DECIMAL = "Otra base → decimal"

DIRECTION_SUBTITLES = {
    TO_BASE: "Escribir un número decimal en binario, octal, hexadecimal o cualquier base "
    f"del {LOWEST_BASE} al {HIGHEST_BASE}, por divisiones sucesivas.",
    TO_DECIMAL: "Leer un número en binario, octal, hexadecimal o cualquier base del "
    f"{LOWEST_BASE} al {HIGHEST_BASE} como la combinación lineal que representa.",
}

CAPTIONS = {TO_BASE: "NÚMERO DECIMAL", TO_DECIMAL: "NÚMERO"}
BASE_CAPTIONS = {TO_BASE: "CONVERTIR A", TO_DECIMAL: "ESTÁ ESCRITO EN"}

# The bases on offer, by the name somebody picks them by, and the choice that
# opens a field for any other.
BASE_NAMES = {"Binario (2)": 2, "Octal (8)": 8, "Hexadecimal (16)": 16}
CUSTOM = "Otra base"

# What the custom field holds before anybody types: a base none of the others is.
CUSTOM_EXAMPLE = "5"

# The number every example is, written in whichever base is showing, so the
# first click works in all of them.
EXAMPLE_NUMBER = 43

# Which digits the bases with a name write with, for when somebody uses another.
ALLOWED = {
    2: "En binario solo se usan las cifras 0 y 1.",
    8: "En octal se usan las cifras del 0 al 7.",
    10: "Escribe un número entero con las cifras del 0 al 9, y un signo menos delante si es negativo.",
    16: "En hexadecimal se usan las cifras del 0 al 9 y las letras de la A a la F.",
}

BAD_BASE = f"La base tiene que ser un número entero del {LOWEST_BASE} al {HIGHEST_BASE}."

# Long enough for any number worth converting by hand, short enough to draw.
LENGTH_LIMIT = 32

# How many terms of a combination fit on one line before it wraps.
TERMS_PER_LINE = 6

SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

def written(numeral: str, base: int) -> str:
    """A numeral with its base written under it: `101011₂`."""
    return numeral + str(base).translate(SUBSCRIPTS)

def allowed(base: int) -> str:
    """Which digits a base writes with, said the way a person would."""
    if base in ALLOWED:
        return ALLOWED[base]
    if base <= 10:
        return f"En base {base} se usan las cifras del 0 al {base - 1}."
    if base == 11:
        return "En base 11 se usan las cifras del 0 al 9 y la letra A."
    return (
        f"En base {base} se usan las cifras del 0 al 9 y las letras de la A a la "
        f"{DIGITS[base - 1]}."
    )

def letters_note(base: int) -> str:
    """What the remainders past 9 are written as, or nothing if there are none."""
    if base <= 10:
        return ""
    if base == 11:
        return " El residuo 10 se escribe con la letra A."
    return (
        f" Los residuos del 10 al {base - 1} se escriben con las letras de la A a la "
        f"{DIGITS[base - 1]}."
    )

def written_digit(remainder: int) -> str:
    """A remainder as the digit it becomes: 11 is `B`."""
    return DIGITS[remainder]

def power(base: int, exponent: int) -> str:
    """A power the way it is written by hand: `2⁵`."""
    return str(base) + str(exponent).translate(SUPERSCRIPTS)

def wrapped(first: str, pieces: list[str], indent: int) -> str:
    """
    A sum written out term by term, broken into lines of a few terms each.

    Every line after the first starts under the first term, with the `+` in
    front, so a long binary number still reads as one expression.
    """
    lines = []
    for start in range(0, len(pieces), TERMS_PER_LINE):
        chunk = " + ".join(pieces[start:start + TERMS_PER_LINE])
        lines.append(first + chunk if start == 0 else " " * indent + "+ " + chunk)
    return "\n".join(lines)

class BasesPage(ctk.CTkFrame):
    """The page that converts a whole number between base 10 and any base from 2 to 36."""

    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._direction = TO_BASE
        self._base = 2
        self._custom = False
        self._example = True
        self._output: list[ctk.CTkBaseClass] = []

        self._header = PageHeader(self, "⇄", "Sistemas Numéricos", DIRECTION_SUBTITLES[TO_BASE])
        self._header.pack(anchor="w", pady=(0, 18))

        SegmentedControl(self, (TO_BASE, TO_DECIMAL), self._choose_direction).pack(
            anchor="w", pady=(0, 16)
        )

        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)

        self._caption = ctk.CTkLabel(
            inside, text=CAPTIONS[TO_BASE], font=theme.font("label"), text_color=theme.MUTED
        )
        self._caption.pack(anchor="w", pady=(0, 8))

        self._number = self._field(inside, width=360, height=42)
        self._number.insert(0, str(EXAMPLE_NUMBER))
        self._number.bind("<KeyRelease>", self._typed)
        self._number.bind("<Return>", lambda _event: self._convert())
        self._number.pack(anchor="w")

        self._base_caption = ctk.CTkLabel(
            inside, text=BASE_CAPTIONS[TO_BASE], font=theme.font("label"),
            text_color=theme.MUTED,
        )
        self._base_caption.pack(anchor="w", pady=(18, 8))
        choice = ctk.CTkFrame(inside, fg_color="transparent")
        choice.pack(anchor="w")
        SegmentedControl(choice, (*BASE_NAMES, CUSTOM), self._choose_base).pack(side="left")

        # Packed only while "Otra base" is the choice.
        self._custom_field = ctk.CTkFrame(choice, fg_color="transparent")
        ctk.CTkLabel(
            self._custom_field, text="b =", font=theme.font("mono"), text_color=theme.MUTED
        ).pack(side="left", padx=(16, 8))
        self._custom_base = self._field(self._custom_field, width=72, height=34)
        self._custom_base.insert(0, CUSTOM_EXAMPLE)
        self._custom_base.bind("<KeyRelease>", self._base_typed)
        self._custom_base.bind("<Return>", lambda _event: self._convert())
        self._custom_base.pack(side="left")
        ctk.CTkLabel(
            self._custom_field,
            text=f"entre {LOWEST_BASE} y {HIGHEST_BASE}",
            font=theme.font("small"),
            text_color=theme.FAINT,
        ).pack(side="left", padx=(10, 0))

        self._error = ErrorBanner(inside)

        buttons = ctk.CTkFrame(inside, fg_color="transparent")
        buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(buttons, "Convertir  →", self._convert).pack(side="right")
        self._error.appear_before(buttons)

    # ----- Choosing what to convert -----

    def _choose_direction(self, direction: str) -> None:
        self._direction = direction
        self._header.set_subtitle(DIRECTION_SUBTITLES[direction])
        self._caption.configure(text=CAPTIONS[direction])
        self._base_caption.configure(text=BASE_CAPTIONS[direction])
        self._show_example()

    def _choose_base(self, name: str) -> None:
        self._custom = name == CUSTOM
        if self._custom:
            self._custom_field.pack(side="left")
            self._custom_base.focus_set()
        else:
            self._custom_field.pack_forget()
            self._base = BASE_NAMES[name]
        self._base_changed()

    def _base_typed(self, event: Any) -> None:
        if event.keysym != "Return":
            self._base_changed()

    def _base_changed(self) -> None:
        if self._direction == TO_DECIMAL:
            self._show_example()
        else:
            self._clear_output()
            self._error.hide()

    def _chosen_base(self) -> int | None:
        """
        The base picked, or None while the custom field does not hold one.

        The field is read as a decimal numeral by the same `from_base` the page
        is about, so not even the base goes through `int`.
        """
        if not self._custom:
            return self._base
        try:
            base = from_base(self._custom_base.get(), 10).value
        except NumeralError:
            return None
        return base if LOWEST_BASE <= base <= HIGHEST_BASE else None

    def _show_example(self) -> None:
        """
        Put an example in the box, unless somebody has typed their own number.

        `43` means nothing in base 2, so switching direction or base with the
        example still showing swaps it for 43 written in the new base. While the
        custom field holds no base, the example is left as it is.
        """
        self._clear_output()
        self._error.hide()
        if not self._example:
            return
        base = 10 if self._direction == TO_BASE else self._chosen_base()
        if base is None:
            return
        self._number.delete(0, "end")
        self._number.insert(0, to_base(EXAMPLE_NUMBER, base).numeral)

    def _typed(self, event: Any) -> None:
        if event.keysym == "Return":
            return
        self._example = False
        self._clear_output()

    # ----- Converting -----

    def _convert(self) -> None:
        self._clear_output()
        text = self._number.get()
        base = self._chosen_base()
        if base is None:
            self._error.show(BAD_BASE)
            return
        read_in = 10 if self._direction == TO_BASE else base
        # The sign is not a digit, so it does not count towards the limit.
        if len("".join(text.split()).lstrip("+-")) > LENGTH_LIMIT:
            self._error.show(f"El número puede tener como mucho {LENGTH_LIMIT} cifras.")
            return
        try:
            number = from_base(text, read_in)
        except EmptyNumeral:
            self._error.show("Escribe un número.")
            return
        except BadDigit as problem:
            if problem.digit in "+-":
                self._error.show(
                    f"'{problem.digit}' no es una cifra: el signo solo puede ir una vez, "
                    "al principio del número."
                )
                return
            self._error.show(
                f"'{problem.digit}' no es una cifra en base {problem.base}. "
                f"{allowed(problem.base)}"
            )
            return

        self._error.hide()
        if self._direction == TO_BASE:
            self._draw_to_base(to_base(number.value, base))
        else:
            self._draw_to_decimal(number)

    # ----- From decimal -----

    def _draw_to_base(self, result: ToBase) -> None:
        self._draw_answer(written(str(result.value), 10), written(result.numeral, result.base))

        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(
            inside,
            f"Divisiones sucesivas entre {result.base}",
            f"{len(result.divisions)} divisiones",
        ).pack(fill="x", pady=(0, 6))

        self._muted(
            inside,
            f"Se divide entre {result.base} hasta que el cociente es 0. Cada residuo "
            "es una cifra del resultado." + letters_note(result.base),
        )
        if result.negative:
            self._muted(
                inside,
                f"El número es negativo: se divide su valor absoluto, "
                f"|{result.value}| = {-result.value}, y el signo menos se pone delante "
                "del resultado.",
            ).pack_configure(pady=(4, 0))

        rows = ctk.CTkFrame(inside, fg_color="transparent")
        rows.pack(anchor="w", pady=(12, 0))
        for header, column in (("División", 0), ("Residuo", 1), ("Cifra", 2)):
            ctk.CTkLabel(
                rows, text=header.upper(), font=theme.font("label"), text_color=theme.MUTED
            ).grid(row=0, column=column, sticky="w", padx=(0, 28), pady=(0, 6))

        for row, step in enumerate(result.divisions, start=1):
            self._mono(
                rows, f"{step.dividend} = {result.base} · {step.quotient} + {step.remainder}"
            ).grid(row=row, column=0, sticky="w", padx=(0, 28), pady=2)
            self._mono(rows, str(step.remainder), theme.MUTED).grid(
                row=row, column=1, sticky="w", padx=(0, 28)
            )
            Chip(rows, written_digit(step.remainder), theme.ACCENT, theme.ACCENT_SOFT).grid(
                row=row, column=2, sticky="w", pady=2
            )

        digits = " ".join(written_digit(step.remainder) for step in reversed(result.divisions))
        if result.negative:
            digits = f"-( {digits} )"
        self._muted(inside, "Leídos de abajo hacia arriba:").pack_configure(pady=(14, 4))
        self._mono(
            inside, f"{digits}   →   {written(result.numeral, result.base)}", theme.ACCENT
        ).pack(anchor="w")

        # The divisions are not trusted with their own answer: read it back.
        self._draw_combination(
            from_base(result.numeral, result.base),
            "Comprobación",
            f"El resultado, leído de vuelta como combinación lineal, da {result.value}: "
            "el número del que se partió.",
        )

    # ----- To decimal -----

    def _draw_to_decimal(self, number: FromBase) -> None:
        self._draw_answer(written(number.numeral, number.base), written(str(number.value), 10))
        self._draw_combination(
            number,
            "Combinación lineal",
            "Cada cifra se multiplica por la base elevada a su posición, contando desde 0 "
            "por la derecha, y los productos se suman.",
        )
        self._draw_positions(number)

    def _draw_combination(self, number: FromBase, title: str, note: str) -> None:
        """The numeral written out as a sum of powers, and worked down to one number."""
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, title).pack(fill="x", pady=(0, 6))
        if number.negative:
            note += " El signo menos multiplica a toda la combinación."
        self._muted(inside, note)

        # A negative numeral wraps each stage in -( ... ), so the sign is seen
        # to apply to the whole sum and not to its first term.
        opening, closing = ("-(", ")") if number.negative else ("", "")
        left = written(number.numeral, number.base) + " = "
        pad = " " * (len(left) - 2) + "= "
        indent = len(left) + len(opening)
        powers = [f"{term.value}·{power(number.base, term.position)}" for term in number.terms]
        weights = [f"{term.value}·{term.power}" for term in number.terms]
        amounts = [str(term.amount) for term in number.terms]

        block = [
            wrapped(left + opening, powers, indent) + closing,
            wrapped(pad + opening, weights, indent) + closing,
            wrapped(pad + opening, amounts, indent) + closing,
        ]
        if number.negative:
            block.append(f"{pad}-{number.magnitude}")
        else:
            block.append(f"{pad}{number.value}")
        self._mono(inside, "\n".join(block)).pack(anchor="w", pady=(12, 0))

        letters = sorted({term.digit for term in number.terms if not term.digit.isdigit()})
        if letters:
            chips = ctk.CTkFrame(inside, fg_color="transparent")
            chips.pack(anchor="w", pady=(12, 0))
            for letter in letters:
                value = next(term.value for term in number.terms if term.digit == letter)
                Chip(chips, f"{letter} = {value}", theme.MUTED).pack(side="left", padx=(0, 8))

    def _draw_positions(self, number: FromBase) -> None:
        """The same combination as a table: one row per digit, from the left."""
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, "Valor de cada posición").pack(fill="x", pady=(0, 12))

        table = ctk.CTkFrame(inside, fg_color="transparent")
        table.pack(anchor="w")
        for column, header in enumerate(("Cifra", "Posición", "Potencia", "Aporte")):
            ctk.CTkLabel(
                table, text=header.upper(), font=theme.font("label"), text_color=theme.MUTED
            ).grid(row=0, column=column, sticky="e", padx=(0, 32), pady=(0, 6))

        for row, term in enumerate(number.terms, start=1):
            digit = term.digit if term.digit.isdigit() else f"{term.digit} ({term.value})"
            cells = (
                digit,
                str(term.position),
                f"{power(number.base, term.position)} = {term.power}",
                f"{term.value} · {term.power} = {term.amount}",
            )
            for column, text in enumerate(cells):
                self._mono(table, text, theme.INK if column else theme.ACCENT).grid(
                    row=row, column=column, sticky="e", padx=(0, 32), pady=2
                )

        total = len(number.terms) + 1
        ctk.CTkFrame(table, height=2, fg_color=theme.BORDER, corner_radius=0).grid(
            row=total, column=0, columnspan=4, sticky="ew", pady=6
        )
        self._mono(
            table, f"Suma = {number.magnitude}", theme.INK if number.negative else theme.ACCENT
        ).grid(row=total + 1, column=3, sticky="e", padx=(0, 32))
        if number.negative:
            self._mono(table, f"Con el signo: -{number.magnitude}", theme.ACCENT).grid(
                row=total + 2, column=3, sticky="e", padx=(0, 32), pady=(4, 0)
            )

    # ----- Pieces shared by both directions -----

    def _draw_answer(self, given: str, found: str) -> None:
        """The conversion in one line, large, before the working that justifies it."""
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, "Resultado").pack(fill="x", pady=(0, 10))
        line = ctk.CTkFrame(inside, fg_color="transparent")
        line.pack(anchor="w")
        ctk.CTkLabel(line, text=given, font=theme.font("title"), text_color=theme.INK).pack(
            side="left"
        )
        ctk.CTkLabel(line, text="  =  ", font=theme.font("title"), text_color=theme.MUTED).pack(
            side="left"
        )
        ctk.CTkLabel(
            line, text=found, font=theme.font("title"), text_color=theme.ACCENT
        ).pack(side="left")

    def _field(self, master: Any, width: int, height: int) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            master,
            width=width,
            height=height,
            corner_radius=theme.FIELD_RADIUS,
            fg_color=theme.FIELD,
            border_width=1,
            border_color=theme.BORDER,
            text_color=theme.INK,
            font=theme.font("mono"),
        )

    def _mono(self, master: Any, text: str, color: Color = theme.INK) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            master, text=text, font=theme.font("mono"), text_color=color,
            justify="left", anchor="w",
        )

    def _muted(self, master: Any, text: str) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            master, text=text, font=theme.font("small"), text_color=theme.MUTED,
            justify="left", anchor="w", wraplength=640,
        )
        label.pack(anchor="w")
        return label

    def _add_card(self) -> Card:
        card = Card(self)
        card.pack(fill="x", pady=(16, 0))
        self._output.append(card)
        return card

    def _clear_output(self) -> None:
        """A conversion stops being true the moment the number or the base changes."""
        for card in self._output:
            card.destroy()
        self._output = []
