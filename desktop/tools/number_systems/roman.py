"""Aritmética con números romanos."""

from PySide6.QtCore import Qt

from core.number_systems import roman

from desktop.core.forms import Result, ToolPage, text_input
from desktop.core.widgets import SegmentedControl, Toggle, label

from .core.results import roman_pieces


def roman_page() -> ToolPage:
    operation = SegmentedControl("Suma", "Resta", "Multiplicación")
    operation.setAccessibleName("Operación romana")
    left, right = text_input("Primer número", "XIV"), text_input("Segundo número", "IX")
    left.setPlaceholderText("Primer número")
    right.setPlaceholderText("Segundo número")
    for field in (left, right):
        field.setMaximumWidth(200)
        field.setAlignment(Qt.AlignmentFlag.AlignCenter)
    sign_label = label("+", "heading")
    sign_label.setFixedWidth(20)
    repeated = Toggle("Mostrar notación de suma")
    repeated.setChecked(True)

    def calculate() -> Result:
        fn = (roman.sum_of, roman.difference_of, roman.product_of)[operation.currentIndex()]
        found = fn(left.text(), right.text())
        sign = ("+", "−", "×")[operation.currentIndex()]
        reading = "\n".join((roman_pieces(found.left), roman_pieces(found.right)))
        parts = [f"{found.left.value} {sign} {found.right.value} = {found.value}"]
        check = ""
        if found.numeral:
            parts.append(f"{found.numeral} = {found.value}")
            check = roman_pieces(roman.read(found.numeral))
        else:
            parts.append("El resultado queda fuera del rango romano de 1 a 3999.")
        steps = ()
        if repeated.isVisible() and repeated.isChecked():
            terms = found.terms[:30]
            total = " + ".join(str(term) for term in terms)
            if len(found.terms) > len(terms):
                total += f" + … ({len(found.terms)} sumandos en total)"
            steps = (f"Suma repetida\n{total}\nTotal: {found.value}",)
        return Result("\n".join(parts), steps, sections=(reading, check))

    def show_fields(index: int) -> None:
        repeated.setVisible(index == 2)
        sign_label.setText(("+", "−", "×")[index])

    help_text = label("Símbolos: I = 1, V = 5, X = 10, L = 50, C = 100, D = 500, M = 1000.\n"
                      "Las restas permitidas son IV, IX, XL, XC, CD y CM.", "muted")
    page = ToolPage("Ⅻ", "Aritmética Romana", "Sumar dos números romanos: se leen, se suman sus valores y el total se escribe en romano.",
                    [(left, sign_label, right), repeated, help_text], "Calcular", calculate, above=(operation,),
                    after=("Cómo se lee cada número", "Comprobación"), walk_title="Notación de suma")
    operation.currentIndexChanged.connect(show_fields)
    repeated.hide()
    return page
