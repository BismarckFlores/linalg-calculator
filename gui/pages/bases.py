"""
Llevar un numero entero de la base 10 a cualquier base del 2 al 36 y de vuelta,
con el procedimiento a la vista.

Desde decimal, por divisiones sucesivas: cada division se escribe como la
ecuacion que es, y los residuos se leen de abajo hacia arriba. Hacia decimal,
por la combinacion lineal de potencias que representa el numero, escrita entera
y despues resuelta hasta un solo numero.

Cada sentido se comprueba con el otro. Un numero convertido a base 2 se lee de
vuelta a decimal justo debajo, lo que demuestra las cifras sin fiarse de las
divisiones que las produjeron.

Binario, octal y hexadecimal estan a un clic, porque son las que pide el curso.
Cualquier otra base se escribe en un campo propio.

Los numeros romanos estan en el mismo selector, y son la unica opcion que no es
una base: no hay posiciones ni potencias, asi que no valen ni las divisiones ni
la combinacion. Un numero se escribe tomando la pieza mas grande que quepa, una
y otra vez, y se lee de vuelta como la suma de las piezas que lo forman.

Un numero negativo se convierte como se hace a mano: las cifras son las de su
valor absoluto, y el menos va delante de ellas y delante de toda la
combinacion, -2B(16) = -(2*16^1 + 11*16^0) = -43.

El castellano vive aqui porque ninguna otra interfaz dice nada de esto.
"""

from typing import Any

import customtkinter as ctk

from core.roman import (
    LARGEST,
    Numeral,
    OutOfRange,
    RomanError,
    Written,
    read,
    write,
)
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
from ui.presentation import subscript, superscript

from .. import theme
from ..theme import Color
from ..widgets import (
    Card,
    Chip,
    ErrorBanner,
    PageHeader,
    PrimaryButton,
    ResultsPage,
    RomanNumeral,
    SectionTitle,
    SegmentedControl,
)
from .roman import roman_complaint

TO_BASE = "Decimal → otra base"
TO_DECIMAL = "Otra base → decimal"

DIRECTION_SUBTITLES = {
    TO_BASE: "Escribir un número decimal en binario, octal, hexadecimal, cualquier base "
    f"del {LOWEST_BASE} al {HIGHEST_BASE} o números romanos.",
    TO_DECIMAL: "Leer un número escrito en otra base, o en números romanos, y llevarlo "
    "a decimal.",
}

CAPTIONS = {TO_BASE: "NÚMERO DECIMAL", TO_DECIMAL: "NÚMERO"}
BASE_CAPTIONS = {TO_BASE: "CONVERTIR A", TO_DECIMAL: "ESTÁ ESCRITO EN"}

# Las bases disponibles, con el nombre con que se eligen, y las dos opciones
# que no son una base: un campo para cualquier otra, y los numeros romanos,
# que no tienen numero de base. ROMAN hace de base para ellos en el selector.
BASE_NAMES = {"Binario (2)": 2, "Octal (8)": 8, "Hexadecimal (16)": 16}
CUSTOM = "Otra base"
ROMAN = "Romano"
ROMAN_BASE = 0

# Lo que tiene el campo de otra base antes de escribir: una base que no es ninguna de las demas.
CUSTOM_EXAMPLE = "5"

# El numero que es cada ejemplo, escrito en la base que este a la vista, para
# que el primer clic funcione en todas.
EXAMPLE_NUMBER = 43

# Que cifras usan las bases con nombre, para cuando alguien escribe otra.
ALLOWED = {
    2: "En binario solo se usan las cifras 0 y 1.",
    8: "En octal se usan las cifras del 0 al 7.",
    10: "Escribe un número entero con las cifras del 0 al 9, y un signo menos delante si es negativo.",
    16: "En hexadecimal se usan las cifras del 0 al 9 y las letras de la A a la F.",
}

BAD_BASE = f"La base tiene que ser un número entero del {LOWEST_BASE} al {HIGHEST_BASE}."

# Suficiente para cualquier numero que se convierta a mano, y corto para dibujarlo.
LENGTH_LIMIT = 32

# Cuantos terminos de una combinacion caben en una linea antes de partirla.
TERMS_PER_LINE = 6

def written(numeral: str, base: int) -> str:
    """Un numero con su base escrita debajo: 101011₂."""
    return numeral + subscript(base)

def allowed(base: int) -> str:
    """Que cifras usa una base, dicho como lo diria una persona."""
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
    """Como se escriben los residuos mayores que 9, o nada si no los hay."""
    if base <= 10:
        return ""
    if base == 11:
        return " El residuo 10 se escribe con la letra A."
    return (
        f" Los residuos del 10 al {base - 1} se escriben con las letras de la A a la "
        f"{DIGITS[base - 1]}."
    )

def written_digit(remainder: int) -> str:
    """Un residuo como la cifra en que se convierte: 11 es B."""
    return DIGITS[remainder]

def power(base: int, exponent: int) -> str:
    """Una potencia como se escribe a mano: 2⁵."""
    return str(base) + superscript(exponent)

def wrapped(first: str, pieces: list[str], indent: int) -> str:
    """
    Una suma escrita termino a termino, partida en lineas de pocos terminos.

    Cada linea despues de la primera empieza debajo del primer termino, con el
    + delante, para que un binario largo se siga leyendo como una sola expresion.
    """
    lines = []
    for start in range(0, len(pieces), TERMS_PER_LINE):
        chunk = " + ".join(pieces[start:start + TERMS_PER_LINE])
        lines.append(first + chunk if start == 0 else " " * indent + "+ " + chunk)
    return "\n".join(lines)

class BasesPage(ResultsPage):
    """La pagina que convierte un numero entero entre la base 10 y cualquier base del 2 al 36."""

    def __init__(self, master: Any) -> None:
        super().__init__(master)
        self._direction = TO_BASE
        self._base = 2
        self._custom = False
        self._example = True

        self._header = PageHeader(self, "⇄", "Conversiones", DIRECTION_SUBTITLES[TO_BASE])
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
        SegmentedControl(
            choice, (*BASE_NAMES, CUSTOM, ROMAN), self._choose_base
        ).pack(side="left")

        # Solo se muestra mientras la opcion elegida es "Otra base".
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

    # ----- Eleccion de lo que se convierte -----

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
            self._base = ROMAN_BASE if name == ROMAN else BASE_NAMES[name]
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
        La base elegida, o None mientras el campo de otra base no tenga una valida.

        El campo se lee como un numero decimal con el mismo from_base del que trata
        la pagina, asi que ni siquiera la base pasa por int.
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
        Pone un ejemplo en la caja, salvo que alguien haya escrito su propio numero.

        43 no significa nada en base 2, asi que al cambiar de sentido o de base con
        el ejemplo todavia a la vista, se cambia por 43 escrito en la base nueva.
        Mientras el campo de otra base no tenga una valida, el ejemplo se queda igual.
        """
        self._clear_output()
        self._error.hide()
        if not self._example:
            return
        base = 10 if self._direction == TO_BASE else self._chosen_base()
        if base is None:
            return
        self._number.delete(0, "end")
        self._number.insert(
            0,
            write(EXAMPLE_NUMBER).numeral if base == ROMAN_BASE
            else to_base(EXAMPLE_NUMBER, base).numeral,
        )

    def _typed(self, event: Any) -> None:
        if event.keysym == "Return":
            return
        self._example = False
        self._clear_output()

    # ----- Conversion -----

    def _convert(self) -> None:
        self._clear_output()
        text = self._number.get()
        base = self._chosen_base()
        if base is None:
            self._error.show(BAD_BASE)
            return
        # Los numeros romanos no son una base, asi que ni leerlos ni escribirlos pasa
        # por las divisiones y las potencias de las que trata el resto de la pagina.
        if base == ROMAN_BASE:
            self._convert_roman(text)
            return

        read_in = 10 if self._direction == TO_BASE else base
        # El signo no es una cifra, asi que no cuenta para el limite.
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

    def _convert_roman(self, text: str) -> None:
        """
        De decimal a romano y de vuelta, la unica conversion que no tiene base.

        Hacia el romano, el numero se lee en base 10 con el mismo from_base que todo
        lo demas, y solo despues se escribe; de vuelta se lee como la suma de sus
        piezas. Lo que no se puede escribir se dice en vez de lanzarse: no hay numero
        romano para el cero, para un negativo ni por encima de MMMCMXCIX.
        """
        try:
            if self._direction == TO_BASE:
                number = from_base(text, 10)
                self._error.hide()
                self._draw_to_roman(write(number.value))
            else:
                numeral = read(text)
                self._error.hide()
                self._draw_from_roman(numeral)
        except EmptyNumeral:
            self._error.show("Escribe un número.")
        except BadDigit as problem:
            self._error.show(
                f"'{problem.digit}' no es una cifra decimal. {ALLOWED[10]}"
            )
        except OutOfRange as problem:
            self._error.show(
                f"{problem.value} no tiene número romano: solo se escriben los números "
                f"del 1 al {LARGEST} (MMMCMXCIX), porque no había símbolo para el cero, "
                "para los negativos ni por encima de M."
            )
        except RomanError as problem:
            self._error.show(roman_complaint(problem))

    # ----- Hacia el romano, y de vuelta -----

    def _draw_to_roman(self, result: Written) -> None:
        """El numero escrito pieza a pieza, cada una tomada de lo que queda."""
        self._draw_answer(written(str(result.value), 10), result.numeral)

        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(
            inside, "Construcción del número", f"{len(result.taken)} piezas"
        ).pack(fill="x", pady=(0, 6))
        self._muted(
            inside,
            "Se toma la pieza más grande que quepa, se resta, y se repite con lo que "
            "queda hasta llegar a 0. Las piezas son I, IV, V, IX, X, XL, L, XC, C, CD, "
            "D, CM y M.",
        )

        rows = ctk.CTkFrame(inside, fg_color="transparent")
        rows.pack(anchor="w", pady=(12, 0))
        for header, column in (("Queda", 0), ("Pieza", 1), ("Se resta", 2), ("Sobra", 3)):
            ctk.CTkLabel(
                rows, text=header.upper(), font=theme.font("label"), text_color=theme.MUTED
            ).grid(row=0, column=column, sticky="w", padx=(0, 28), pady=(0, 6))

        for row, step in enumerate(result.taken, start=1):
            self._mono(rows, str(step.before)).grid(
                row=row, column=0, sticky="e", padx=(0, 28), pady=2
            )
            Chip(rows, step.text, theme.ACCENT, theme.ACCENT_SOFT).grid(
                row=row, column=1, sticky="w", padx=(0, 28), pady=2
            )
            self._mono(rows, f"− {step.value}", theme.MUTED).grid(
                row=row, column=2, sticky="e", padx=(0, 28)
            )
            self._mono(rows, str(step.after)).grid(row=row, column=3, sticky="e", padx=(0, 28))

        self._muted(inside, "Las piezas, una tras otra:").pack_configure(pady=(14, 4))
        self._mono(
            inside,
            "  ".join(step.text for step in result.taken) + f"   →   {result.numeral}",
            theme.ACCENT,
        ).pack(anchor="w")

        # No se confia en las piezas para su propio resultado: se lee de vuelta.
        self._draw_roman_check(read(result.numeral), result.value)

    def _draw_from_roman(self, numeral: Numeral) -> None:
        """Un numero romano leido como la suma de sus piezas, que es lo que siempre fue."""
        self._draw_answer(numeral.text, written(str(numeral.value), 10))

        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, "Suma de sus piezas").pack(fill="x", pady=(0, 6))
        self._muted(
            inside,
            "Un número romano es la suma de sus piezas, escritas de mayor a menor. Las "
            "seis parejas IV, IX, XL, XC, CD y CM valen una resta: IX es 10 − 1.",
        )
        RomanNumeral(inside, numeral).pack(anchor="w", pady=(14, 0))
        self._mono(
            inside,
            " + ".join(str(piece.value) for piece in numeral.pieces)
            + f" = {numeral.value}",
            theme.ACCENT,
        ).pack(anchor="w", pady=(10, 0))

    def _draw_roman_check(self, numeral: Numeral, value: int) -> None:
        """El numero recien escrito, leido de vuelta, que tiene que dar otra vez el numero."""
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, "Comprobación").pack(fill="x", pady=(0, 6))
        self._muted(
            inside,
            f"El resultado, leído de vuelta como suma de sus piezas, da {value}: el "
            "número del que se partió.",
        )
        RomanNumeral(inside, numeral).pack(anchor="w", pady=(14, 0))

    # ----- Desde decimal -----

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

        # No se confia en las divisiones para su propio resultado: se lee de vuelta.
        self._draw_combination(
            from_base(result.numeral, result.base),
            "Comprobación",
            f"El resultado, leído de vuelta como combinación lineal, da {result.value}: "
            "el número del que se partió.",
        )

    # ----- Hacia decimal -----

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
        """El numero escrito como suma de potencias, y resuelto hasta un solo numero."""
        card = self._add_card()
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, title).pack(fill="x", pady=(0, 6))
        if number.negative:
            note += " El signo menos multiplica a toda la combinación."
        self._muted(inside, note)

        # Un numero negativo envuelve cada etapa en -( ... ), para que se vea que el
        # signo se aplica a toda la suma y no solo a su primer termino.
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
        """La misma combinacion en forma de tabla: una fila por cifra, desde la izquierda."""
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

    # ----- Piezas comunes a los dos sentidos -----

    def _draw_answer(self, given: str, found: str) -> None:
        """La conversion en una linea, en grande, antes del procedimiento que la justifica."""
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



