"""Conversiones de bases y números romanos."""

from core.number_systems import bases, roman
from ui.presentation import subscript

from desktop.core.forms import Result, ToolPage, text_input
from desktop.core.widgets import SegmentedControl, Stepper, label

from .core.results import roman_pieces


def bases_page() -> ToolPage:
    direction = SegmentedControl("Decimal → otra base", "Otra base → decimal")
    direction.setAccessibleName("Sentido de la conversión")
    radix = SegmentedControl("Binario (2)", "Octal (8)", "Hexadecimal (16)", "Otra base", "Romano")
    radix.setAccessibleName("Sistema numérico")
    custom = Stepper("Base", 2, 36, 5, editable=True)
    number = text_input("Número", "43")
    number.setPlaceholderText("Escribe un número")
    number.setMaximumWidth(360)
    number_caption = label("NÚMERO DECIMAL", "fieldTitle")
    base_caption = label("CONVERTIR A", "fieldTitle")

    def selected_base() -> int:
        return (2, 8, 16, custom.value(), 0)[radix.currentIndex()]

    showing_example = True

    def mark_edited() -> None:
        nonlocal showing_example
        showing_example = False

    def show_fields() -> None:
        custom.setVisible(radix.currentIndex() == 3)
        number_caption.setText("NÚMERO DECIMAL" if direction.currentIndex() == 0 else "NÚMERO EN OTRA BASE")
        base_caption.setText("CONVERTIR A" if direction.currentIndex() == 0 else "BASE DE ORIGEN")
        if showing_example:
            base = selected_base()
            numeral = "43"
            if direction.currentIndex() == 1:
                numeral = bases.to_base(43, base).numeral if base else roman.to_roman(43)
            number.setText(numeral)

    def calculate() -> Result:
        value = number.text()
        if len("".join(value.split()).lstrip("+-")) > 32:
            raise ValueError("Escribe un número de hasta 32 cifras.")
        base = selected_base()
        to_other = direction.currentIndex() == 0
        if not base:
            if to_other:
                decimal = bases.from_base(value, 10).value
                written = roman.write(decimal)
                check = roman.read(written.numeral)
                return Result(
                    f"{decimal} = {written.numeral}\nComprobación: {roman_pieces(check)}",
                    headers=("Pieza", "Valor", "Antes", "Después"),
                    rows=tuple((piece.text, piece.value, piece.before, piece.after) for piece in written.taken),
                )
            numeral = roman.read(value)
            return Result(
                f"{roman_pieces(numeral)}\nComprobación: {numeral.value} = {roman.to_roman(numeral.value)}",
                headers=("Pieza", "Valor"),
                rows=tuple((piece.text, piece.value) for piece in numeral.pieces),
            )
        if to_other:
            decimal = bases.from_base(value, 10).value
            written = bases.to_base(decimal, base)
            checked = bases.from_base(written.numeral, base)
            digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            return Result(
                f"{decimal}₁₀ = {written.numeral}{subscript(base)}\n"
                f"Lee los residuos de abajo hacia arriba y conserva el signo.\n"
                f"Comprobación: {written.numeral}{subscript(base)} = {checked.value}₁₀",
                headers=("Dividendo", "Base", "Cociente", "Residuo", "Dígito"),
                rows=tuple((step.dividend, base, step.quotient, step.remainder, digits[step.remainder])
                           for step in written.divisions),
            )
        read = bases.from_base(value, base)
        terms = [f"{term.value} · {base}^{term.position}" for term in read.terms]
        chunks = [" + ".join(terms[i:i + 6]) for i in range(0, len(terms), 6)]
        expansion = "\n+ ".join(chunks)
        if read.negative:
            expansion = f"−({expansion})"
        return Result(
            f"{read.numeral}{subscript(base)} = {read.value}₁₀\n"
            f"Desarrollo: {expansion}\n"
            f"Comprobación: {read.value}₁₀ = {bases.to_base(read.value, base).numeral}{subscript(base)}",
            headers=("Dígito", "Valor", "Posición", "Potencia", "Aporte"),
            rows=tuple((term.digit, term.value, term.position, term.power, term.amount) for term in read.terms),
        )

    page = ToolPage("⇄", "Conversiones",
                    "Escribir un número decimal en binario, octal, hexadecimal, cualquier base del 2 al 36 o números romanos.",
                    [number_caption, number, base_caption, radix, custom], "Convertir", calculate, above=(direction,))
    for control in (direction, radix):
        control.currentIndexChanged.connect(show_fields)
    custom.valueChanged.connect(show_fields)
    number.textEdited.connect(mark_edited)
    show_fields()
    return page
