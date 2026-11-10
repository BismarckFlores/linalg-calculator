"""Herramientas de vectores, bases y aritmética romana."""

from PySide6.QtCore import Qt

from core import bases, roman, vectors
from core.matrix import Matrix
from core.scalar import to_scalar
from ui.presentation import describe, render_general, render_linear_sum, render_system, render_values, subscript

from .forms import Result, ToolPage, matrix_steps, matrix_text, text_input
from .math_input import MathInput
from .widgets import SegmentedControl, Stepper, Toggle, label


def vectors_page() -> ToolPage:
    operation = SegmentedControl("u + v", "u − v", "k · u", "Combinación lineal")
    operation.setAccessibleName("Operación vectorial")
    first = MathInput("1, -2, 3", "u =", "vector", inline=True)
    second = MathInput("4, 0, -1/2", "v =", "vector", inline=True)
    scalar = MathInput("1/2", "k =", "number", inline=True)
    target = MathInput("1, -2, 3", "b =", "vector", inline=True)
    for editor in (first, second, target):
        editor.setMaximumWidth(434)
    scalar.setMaximumWidth(164)
    generators = text_input("Vectores generadores", "1, 0, 0\n0, 1, 0\n0, 0, 1", multiline=True)
    generators.setPlaceholderText("Un vector generador por línea")

    def show_fields() -> None:
        index = operation.currentIndex()
        first.setVisible(index != 3)
        target.setVisible(index == 3)
        second.setVisible(index < 2)
        scalar.setVisible(index == 2)
        generators.setVisible(index == 3)

    def read_vector(text: str):
        vector = vectors.parse_vector(text)
        if len(vector) > 10:
            raise ValueError("Se admiten hasta 10 componentes por vector.")
        return vector

    def calculate() -> Result:
        index = operation.currentIndex()
        u = read_vector(target.value() if index == 3 else first.value())
        if index == 3:
            lines = [line for line in generators.toPlainText().splitlines() if line.strip()]
            if not 1 <= len(lines) <= 10:
                raise ValueError("Escribe de 1 a 10 vectores, uno por línea.")
            found = vectors.combine([read_vector(line) for line in lines], u)
            solution = found.solution
            names = [f"c_{i}" for i in range(1, len(lines) + 1)]
            symbols = [f"v{subscript(i)}" for i in range(1, len(lines) + 1)]
            setup = render_system(solution.augmented, solution.unknowns, names)
            parts = [describe(solution), render_values(solution, names)]
            details = []
            if found.general:
                parts.extend(("Familia de escalares", render_general(found.general, names)))
            weights = found.weights
            if weights is not None:
                check = vectors.linear_sum(weights, found.vectors)
                details.extend((
                    "Comprobación con los escalares libres en cero" if found.general else "Comprobación",
                    f"b = {render_linear_sum(weights, symbols)}",
                    matrix_text(Matrix.column_vector(check)),
                    "La suma reproduce el vector objetivo." if check == u else "La suma difiere del vector objetivo.",
                ))
                for i, components in enumerate(zip(*found.vectors), 1):
                    terms = " + ".join(f"({k})({entry})" for k, entry in zip(weights, components))
                    details.append(f"b{subscript(i)} = {terms} = {check[i - 1]}")
            return Result("\n".join(parts), matrix_steps(solution.log), sections=(setup, "", "\n".join(details)))
        if index == 2:
            factor = to_scalar(scalar.value())
            result = vectors.scale(factor, u)
            title = "k · u"
            operations = [f"({factor})({entry})" for entry in u]
        else:
            v = read_vector(second.value())
            if index == 0:
                result, sign = vectors.add(u, v), "+"
            else:
                result, sign = vectors.subtract(u, v), "−"
            title = f"u {sign} v"
            operations = [f"({left}) {sign} ({right})" for left, right in zip(u, v)]
        lines = [f"{title} = ({', '.join(map(str, result))})", matrix_text(Matrix.column_vector(result))]
        details = "\n".join(
            f"Componente {i}: {expression} = {value}"
            for i, (expression, value) in enumerate(zip(operations, result), 1)
        )
        return Result("\n".join(lines), sections=("", details))

    help_text = label("Separa las componentes con comas o espacios, y usa punto decimal: 1, -2, 0.5, 1/3.\n"
                      "La dimensión es la cantidad de componentes que escribas.", "muted")
    page = ToolPage("↗", "Operaciones Vectoriales", "Suma dos vectores de ℝⁿ, componente a componente.",
                    [scalar, first, second, target, generators, help_text], "Calcular", calculate, above=(operation,),
                    before=("Planteamiento",), after=("Componente a componente", "Comprobación"))
    page.form.setSpacing(8)
    operation.currentIndexChanged.connect(show_fields)
    show_fields()
    return page


def roman_pieces(number: roman.Numeral) -> str:
    return f"{number.text} = {' + '.join(piece.text for piece in number.pieces)} = {number.value}"


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
