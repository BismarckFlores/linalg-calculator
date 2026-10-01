"""
Sumar, restar y multiplicar numeros romanos, con el procedimiento a la vista.

Toda operacion se hace sobre lo que valen los numeros: cada uno se lee como la
suma de sus piezas, se operan los dos valores, y la respuesta se vuelve a
escribir en romano. Una multiplicacion puede mostrar ademas la suma repetida que
representa, que es la notacion que pide el enunciado, y va en un interruptor
porque es el procedimiento y no la respuesta.

Dos cosas que los romanos no escribieron aparecen como respuestas y no como
errores: el cero y los negativos, y todo lo que pase de MMMCMXCIX. La pagina
dice cual de las dos es y da el valor en nuestros numeros, porque que una resta
no se pueda escribir es la respuesta a V - X.

El castellano vive aqui porque ninguna otra interfaz dice nada de esto.
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
    Numeral,
    RomanError,
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
    RomanNumeral,
    SectionTitle,
    SegmentedControl,
)

PLUS = "Suma"
MINUS = "Resta"
TIMES = "Multiplicación"

ROMAN_SUBTITLES = {
    PLUS: "Sumar dos números romanos: se leen, se suman sus valores y el total se escribe en romano.",
    MINUS: "Restar dos números romanos: los romanos no escribían el cero ni los negativos.",
    TIMES: "Multiplicar dos números romanos, con la notación de suma que los escribe "
    "como una suma repetida: X × V es X + X + X + X + X.",
}

# El signo con que se escribe cada operacion, y la llamada que la hace.
ROMAN_SIGNS = {PLUS: "+", MINUS: "−", TIMES: "×"}
ROMAN_OPERATIONS = {PLUS: sum_of, MINUS: difference_of, TIMES: product_of}

# Lo que tienen las cajas antes de escribir, para que el primer clic muestre algo.
FIRST_EXAMPLE = "XIV"
SECOND_EXAMPLE = "IX"

# Lo que vale cada simbolo, dicho una vez debajo de las casillas.
ROMAN_HELP = (
    "Símbolos: I = 1, V = 5, X = 10, L = 50, C = 100, D = 500, M = 1000.\n"
    "Se escriben del mayor al menor, y las únicas restas son IV, IX, XL, XC, CD y CM."
)
SUM_NOTATION = "Notación de suma"

# Mil X en pantalla no dicen nada que no digan las primeras; M × M pediria
# exactamente eso, y X × MMM tres mil.
TERMS_SHOWN = 30

# Cuantos sumandos de la suma repetida caben en una linea antes de partirla.
ROMAN_TERMS_PER_LINE = 10

def roman_complaint(problem: RomanError) -> str:
    """
    Que decir de un numero romano que no se pudo leer.

    Las dos paginas que reciben un numero romano lanzan los mismos errores, y
    quien escribio IIII merece la misma frase en cualquiera de las dos.
    """
    if isinstance(problem, EmptyRoman):
        return "Escribe un número romano."
    if isinstance(problem, BadLetter):
        return (
            f"'{problem.letter}' no es un símbolo romano. "
            "Solo se usan I, V, X, L, C, D y M."
        )
    if isinstance(problem, NotCanonical):
        return f"'{problem.numeral}' no se escribe así: ese número es {problem.canonical}."
    if isinstance(problem, BadOrder):
        return (
            f"'{problem.numeral}' no es un número romano: los símbolos van del mayor "
            "al menor, y las únicas restas son IV, IX, XL, XC, CD y CM."
        )
    return str(problem)

class RomanPage(ctk.CTkFrame):
    """La pagina que suma, resta y multiplica numeros romanos."""

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

        # Solo una multiplicacion tiene una suma que escribir, asi que el interruptor
        # va con ella y viene encendido: escribirla es lo que pide el enunciado.
        self._as_sum = ctk.CTkSwitch(
            inside,
            text=SUM_NOTATION,
            font=theme.font("body"),
            text_color=theme.INK,
            progress_color=theme.ACCENT,
            command=self._clear_output,
        )
        self._as_sum.select()

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
        """Uno de los dos numeros, escrito en mayusculas escriba lo que escriba el teclado."""
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

    # ----- Eleccion de la operacion -----

    def _choose(self, operation: str) -> None:
        self._operation = operation
        self._header.set_subtitle(ROMAN_SUBTITLES[operation])
        self._sign.configure(text=ROMAN_SIGNS[operation])
        self._clear_output()
        self._error.hide()

        if operation == TIMES:
            self._as_sum.pack(anchor="w", pady=(14, 0), before=self._help)
        else:
            self._as_sum.pack_forget()

    def _write(self, entry: ctk.CTkEntry, text: str) -> None:
        entry.delete(0, "end")
        entry.insert(0, text)

    def _typed(self, event: Any) -> None:
        """Los numeros romanos van en mayusculas, asi que la minuscula se corrige al escribir."""
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

    # ----- Calculo -----

    def _calculate(self) -> None:
        self._clear_output()
        try:
            done = ROMAN_OPERATIONS[self._operation](self._first.get(), self._second.get())
        except EmptyRoman:
            self._error.show("Escribe un número romano en las dos casillas.")
            return
        except RomanError as problem:
            self._error.show(roman_complaint(problem))
            return

        self._error.hide()
        self._draw_answer(done)
        self._draw_reading(done)
        if done.terms and self._as_sum.get():
            self._draw_terms(done)
        if done.writable:
            self._draw_check(done)

    # ----- La respuesta -----

    def _draw_answer(self, done: Operation) -> None:
        """La operacion en una linea, en romano arriba y en nuestros numeros abajo."""
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
        Por que una respuesta no tiene numero romano, que es una respuesta y no un fallo.

        El cero y los negativos no tenian simbolo, y tampoco lo tenia nada por encima
        de MMMCMXCIX, asi que se da el valor en nuestros numeros y se dice el motivo.
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

    # ----- Como se lee cada numero -----

    def _draw_reading(self, done: Operation) -> None:
        """Cada numero partido en sus piezas, que es como se lee su valor."""
        inside = self._card("Cómo se lee cada número")
        self._muted(
            inside,
            "Cada número romano es la suma de sus piezas. Las seis parejas IV, IX, XL, "
            "XC, CD y CM valen una resta: IX es 10 − 1.",
        ).pack_configure(pady=(0, 14))
        for numeral in (done.left, done.right):
            self._draw_pieces(inside, numeral)

    def _draw_pieces(self, inside: Any, numeral: Numeral) -> None:
        RomanNumeral(inside, numeral).pack(anchor="w", pady=(0, 10))

    # ----- La suma repetida -----

    def _draw_terms(self, done: Operation) -> None:
        """
        La multiplicacion escrita como la suma que representa.

        X * V es X sumado cinco veces, asi que los sumandos son la operacion misma y
        no un dibujo de ella. Un producto que necesitaria cientos de sumandos muestra
        los primeros y dice cuantos son, porque los demas dicen lo mismo.

        La tarjeta solo aparece mientras el interruptor esta encendido: es el
        procedimiento, y quien solo quiere el producto no necesita tres mil sumandos.
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

    # ----- La lectura de vuelta -----

    def _draw_check(self, done: Operation) -> None:
        """
        La respuesta leida de vuelta, que comprueba la escritura contra la lectura.

        El valor se convirtio en numero romano; leer ese numero tiene que dar otra vez
        el valor, y se hace con el mismo codigo por el que pasaron los operandos, no
        con el numero que lo produjo.
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
            justify="left", anchor="w", wraplength=640,
        )
        label.pack(anchor="w")
        return label

    def _clear_output(self) -> None:
        """Un resultado deja de ser cierto en cuanto se cambia cualquiera de los dos numeros."""
        for card in self._output:
            card.destroy()
        self._output = []
