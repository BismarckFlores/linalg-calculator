"""
Todo lo que lee una persona, escrito en castellano.

El motor devuelve datos y nunca una frase; aqui es donde se deciden las
palabras, una sola vez, para que todas las interfaces digan exactamente lo
mismo. Estas funciones construyen cadenas de texto y nada mas: ni print ni
widgets.

Las tres clasificaciones estan redactadas tal como las pide el enunciado, hasta
en las mayusculas.
"""

import re
from collections.abc import Sequence

from core.matrix import Matrix
from core.parametric import General
from core.scalar import Scalar, format_factor, format_scalar
from core.steps import StepLog
from core.systems import Solution, SystemKind
from core.verification import RowCheck, Verification

# Con los nombres del pizarron mientras quepan; a partir de ahi x5, x6...
UNKNOWN_NAMES = ("x", "y", "z", "w")

# Los digitos como subindices, para escribir f_12 como f₁₂ donde se pueda.
SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

# Y como superindices, para un exponente: 2⁵, (−1)³⁺².
SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

def subscript(number: int) -> str:
    """Un indice escrito debajo: f₂, a₃₂, v₁."""
    return str(number).translate(SUBSCRIPTS)

def superscript(number: int) -> str:
    """Un exponente escrito arriba: 2⁵, (−1)³."""
    return str(number).translate(SUPERSCRIPTS)

CLASSIFICATIONS = {
    SystemKind.UNIQUE: "Sistema Consistente Determinado: Presenta Solución Única.",
    SystemKind.INFINITE: "Sistema Consistente Indeterminado: Presenta Infinitas Soluciones.",
    SystemKind.INCONSISTENT: "Sistema Inconsistente: Sin Solución.",
}

def unknown_name(column: int, names: Sequence[str] = ()) -> str:
    """
    El nombre de la incognita que ocupa esa columna, contando desde 1.

    El que le haya puesto quien escribio el sistema, cuando lo escribio como
    ecuaciones y hay un nombre que usar. Si no, los del pizarron de siempre:
    x, y, z, w, y de ahi en adelante x5, x6...
    """
    if column <= len(names):
        return names[column - 1]
    if column <= len(UNKNOWN_NAMES):
        return UNKNOWN_NAMES[column - 1]
    return f"x{column}"

def render_augmented(matrix: Matrix, unknowns: int, indent: str = "  ") -> str:
    """
    La matriz aumentada con la barra que separa A de b: [ 1  -2   1 |  0 ].

    La barra se dibuja aqui y no en Matrix.__str__ porque solo un sistema
    sabe que su ultima columna significa algo distinto que las demas.
    """
    texts = [[format_scalar(value) for value in row] for row in matrix.data]
    # A y b llevan su propio ancho, para que un coeficiente largo no estire tambien b.
    left_width = max((len(text) for row in texts for text in row[:unknowns]), default=1)
    right_width = max((len(text) for row in texts for text in row[unknowns:]), default=1)

    lines = []
    for row in texts:
        left = "  ".join(text.rjust(left_width) for text in row[:unknowns])
        right = "  ".join(text.rjust(right_width) for text in row[unknowns:])
        lines.append(f"{indent}[ {left} | {right} ]")
    return "\n".join(lines)

def render_steps(log: StepLog, unknowns: int) -> str:
    """La eliminacion completa, un bloque numerado por operacion elemental."""
    if log.is_empty():
        return "No hizo falta ninguna operación: la matriz ya estaba escalonada."

    blocks = []
    for number, step in enumerate(log, start=1):
        blocks.append(
            f"Paso {number}:  {step.label}\n{render_augmented(step.after, unknowns)}"
        )
    return "\n\n".join(blocks)

# Una fila nombrada al principio de una linea, en un bloque ya alineado.
_ROW_TAG = re.compile(r"f_(\d+):")

def typographic_rows(block: str) -> str:
    """
    f_2: escrito f₂: sin mover nada de lo que estaba alineado debajo.

    presentation.py coloca estos bloques en columnas contando caracteres, y un
    subindice ocupa un caracter menos que f_2. El hueco que dejaba el guion bajo
    se devuelve despues de los dos puntos, para que las lineas que estaban
    sangradas para cuadrar sigan cuadrando.
    """
    return _ROW_TAG.sub(lambda match: f"f{match[1].translate(SUBSCRIPTS)}: ", block)

def pretty_label(label: str) -> str:
    """
    Una etiqueta de paso en notacion tipografica: f₂ → f₂ + 3 · f₁.

    La misma operacion que el curso escribe como f_2 -> f_2 + 3*f_1, que es lo
    que produce steps.py y lo que imprime el archivo entregado. Una ventana
    tiene los caracteres para escribirlo y una transcripcion de texto plano no
    necesariamente, asi que la decision es de quien dibuja, no del motor.
    """
    text = label.replace("<->", "↔").replace("->", "→").replace("*", " · ")
    return re.sub(r"f_(\d+)", lambda match: "f" + match[1].translate(SUBSCRIPTS), text)

def describe(solution: Solution) -> str:
    """La clasificacion, con las palabras exactas que pide el enunciado."""
    return CLASSIFICATIONS[solution.kind]

def render_values(solution: Solution, names: Sequence[str] = ()) -> str:
    """El valor de cada incognita, o cuales son libres si hay infinitas soluciones."""
    if solution.kind is SystemKind.INCONSISTENT:
        row = _contradictory_row(solution)
        constant = format_scalar(solution.result.elem(row, solution.unknowns + 1))
        return (
            f"La fila f_{row} quedó como  0 = {constant}, que ningún valor de las\n"
            "incógnitas puede cumplir. No hay solución que mostrar."
        )

    if solution.kind is SystemKind.INFINITE:
        free = ", ".join(unknown_name(col, names) for col in solution.free_columns)
        count = len(solution.free_columns)
        return (
            f"El sistema tiene {_plural(solution.unknowns, 'incógnita', 'incógnitas')} "
            f"y {_plural(solution.coefficient_rank, 'pivote', 'pivotes')}, así que "
            f"{'queda' if count == 1 else 'quedan'} "
            f"{_plural(count, 'variable libre', 'variables libres')}: {free}\n"
            "Cada valor que se les dé produce una solución distinta del sistema."
        )

    lines = [f"  {unknown_name(i + 1, names)} = {format_scalar(value)}"
             for i, value in enumerate(solution.values)]
    if solution.homogeneous:
        lines.append("\nEl sistema es homogéneo, y esta es su solución trivial.")
    return "\n".join(lines)

def render_equations(solution: Solution, names: Sequence[str] = ()) -> str:
    """La matriz escalonada escrita otra vez como el sistema de ecuaciones que representa."""
    return render_system(solution.result, solution.unknowns, names)

def render_system(matrix: Matrix, unknowns: int, names: Sequence[str] = ()) -> str:
    """Cualquier matriz aumentada escrita como el sistema de ecuaciones que representa."""
    constants = unknowns + 1
    rows: list[tuple[str, str, str]] = []

    for row in range(1, matrix.rows + 1):
        pieces = [
            _term(matrix.elem(row, col), unknown_name(col, names))
            for col in range(1, constants)
            if matrix.elem(row, col) != 0
        ]
        left = _sum(pieces)
        rows.append((f"f_{row}", left, format_scalar(matrix.elem(row, constants))))

    width = max(len(left) for _tag, left, _constant in rows)
    lines = [f"  {tag}:  {left:>{width}} = {constant}" for tag, left, constant in rows]
    return "\n".join(lines)

def render_substitutions(solution: Solution, names: Sequence[str] = ()) -> str:
    """El despeje, escrito linea a linea como se hace en papel."""
    lines: list[str] = []

    for step in solution.substitutions:
        name = unknown_name(step.column, names)
        constant = format_scalar(step.constant)
        head = f"  f_{step.row}:  "
        indent = " " * len(head)

        if not step.terms:
            lines.extend([f"{head}{name} = {constant}", ""])
            continue

        values = [solution.values[col - 1] for _coefficient, col in step.terms]
        symbolic = " ".join(
            _term(coefficient, unknown_name(col, names))
            for coefficient, col in step.terms
        )
        replaced = " ".join(
            _substitution(coefficient, value)
            for (coefficient, _col), value in zip(step.terms, values)
        )
        moved = [
            _substitution(coefficient, value, flip=True)
            for (coefficient, _col), value in zip(step.terms, values)
        ]
        # Un termino independiente cero no se escribe: x = 0 + 2(16) - 3 no es letra
        # de nadie. Solo se quita cuando queda algo que sostenga la linea.
        cleared = _sum(moved) if step.constant == 0 and moved else f"{constant} " + " ".join(moved)

        lines.append(f"{head}{name} {symbolic} = {constant}")
        lines.append(f"{indent}{name} {replaced} = {constant}")
        # Despejar el termino independiente y resolver la suma son dos lineas solo
        # cuando dicen cosas distintas. Nadie escribe dos veces la misma linea.
        if cleared.strip() != format_scalar(step.value):
            lines.append(f"{indent}{name} = {cleared.strip()}")
        lines.append(f"{indent}{name} = {format_scalar(step.value)}")
        lines.append("")

    return "\n".join(lines).rstrip()

def render_general(family: General, names: Sequence[str] = ()) -> str:
    """x = 1 + 4z, una linea por variable basica, con los nombres alineados en el igual."""
    width = max(
        (len(unknown_name(item.column, names)) for item in family.basic),
        default=1,
    )

    lines = []
    for item in family.basic:
        pieces = [f"+ {format_scalar(item.constant)}"] + [
            _term(coefficient, unknown_name(column, names))
            for coefficient, column in item.terms
        ]
        # Una constante cero solo se quita cuando queda otra cosa que escribir.
        if item.constant == 0 and len(pieces) > 1:
            pieces = pieces[1:]
        name = unknown_name(item.column, names)
        lines.append(f"  {name:>{width}} = {_sum(pieces)}")

    return "\n".join(lines)

def render_linear_sum(weights: Sequence[Scalar], names: Sequence[str]) -> str:
    """
    3v₁ - v₂ + (1/2)v₃: cada escalar delante de su nombre, sin los ceros.

    Una suma en la que todos los escalares son cero es el vector cero, y se escribe 0.
    """
    return _sum([
        _term(weight, name) for weight, name in zip(weights, names) if weight != 0
    ])

def render_verification(verification: Verification) -> str:
    """
    Cada ecuacion del sistema original con los valores sustituidos.

    Dos lineas por ecuacion: la sustitucion tal como se escribe, y cuanto
    suma cada lado. La idea es que se pueda seguir la aritmetica, no solo
    leer que salio bien.
    """
    lines = []
    # Se rellena la numeracion para que la ecuacion 9 y la 10 sigan cuadrando.
    digits = len(str(len(verification.checks)))
    for check in verification.checks:
        head = f"  Ecuación {check.row:>{digits}}:  "
        mark = "correcto" if check.holds else "NO SE CUMPLE"
        lines.append(f"{head}{_substituted(check)} = {format_scalar(check.right)}")
        lines.append(
            f"{' ' * len(head)}{format_scalar(check.left)} = "
            f"{format_scalar(check.right)}   {mark}"
        )

    lines.append("")
    if verification.holds:
        lines.append("Todas las ecuaciones se cumplen: la solución es correcta.")
    else:
        failed = ", ".join(str(check.row) for check in verification.failures())
        lines.append(f"La comprobación falla en la(s) ecuación(es) {failed}.")
    return "\n".join(lines)

def _contradictory_row(solution: Solution) -> int:
    """
    La fila que queda como  0 ... 0 | k  con k distinto de cero, contando desde 1.

    Esa fila es toda la razon por la que un sistema es inconsistente, asi que
    se le ensena al lector por su nombre en vez de decirle que hay una.
    """
    echelon = solution.result
    for row in range(1, echelon.rows + 1):
        coefficients_are_zero = all(
            echelon.elem(row, col) == 0 for col in range(1, solution.unknowns + 1)
        )
        if coefficients_are_zero and echelon.elem(row, solution.unknowns + 1) != 0:
            return row
    raise ValueError("An inconsistent system must have a contradictory row.")

def _plural(count: int, singular: str, plural: str) -> str:
    """'1 pivote' o '3 pivotes', para que nunca se lea '1 pivote(s)'."""
    return f"{count} {singular if count == 1 else plural}"

def _substituted(check: RowCheck) -> str:
    """
    Una ecuacion con cada incognita sustituida por su valor: 1(29) - 2(16).

    El coeficiente se mantiene aunque valga 1, porque lo que ensena la linea es
    la ecuacion original con numeros donde estaban las incognitas. El signo sale
    delante en vez de quedarse dentro del coeficiente, para que la fila se lea
    como una suma, igual que se escribiria a mano.
    """
    pieces = []
    for coefficient, value, _col in check.terms:
        sign = "-" if coefficient < 0 else "+"
        magnitude = -coefficient if coefficient < 0 else coefficient
        pieces.append(f"{sign} {format_factor(magnitude)}({format_scalar(value)})")
    return _sum(pieces)

def _sum(pieces: list[str]) -> str:
    """
    Los terminos de una suma unidos, con el signo del primero arreglado.

    Cada termino se escribe con su signo delante para poder unirlos en cualquier
    orden, lo que deja al primero con un signo que no precede a nada: un + inicial
    se quita, y un - inicial se pega a su numero.
    """
    if not pieces:
        return "0"
    text = " ".join(pieces)
    if text.startswith("+ "):
        return text[2:]
    if text.startswith("- "):
        return "-" + text[2:]
    return text

def _substitution(coefficient: Scalar, value: Scalar, flip: bool = False) -> str:
    """
    Un termino de un despeje, con el valor puesto donde estaba la incognita.

    Un coeficiente de 1 no se escribe, y entonces el signo del valor pasa a ser
    el del termino: 1*(-17/12) se escribe - 17/12, como se haria a mano, y nunca
    + (-17/12). Lo demas conserva los parentesis, porque un 2 pegado a un 16 se
    leeria como 216.
    """
    negative = (coefficient < 0) != flip
    magnitude = -coefficient if coefficient < 0 else coefficient
    if magnitude == 1:
        product = -value if negative else value
        sign = "-" if product < 0 else "+"
        return f"{sign} {format_scalar(-product if product < 0 else product)}"
    return f"{'-' if negative else '+'} {format_factor(magnitude)}({format_scalar(value)})"

def _term(coefficient: Scalar, text: str, flip: bool = False) -> str:
    """
    Un termino con su signo delante: + y, - 3z, + (1/3)x, - 2(16).

    La multiplicacion se escribe poniendo las dos cosas juntas, que es como se
    escribe a mano. Eso solo se lee bien cuando lo que sigue es un nombre o un
    parentesis: contra un numero suelto el coeficiente se pegaria a el y 2*16
    saldria como 216. Por eso todo el que pasa un numero lo pasa entre
    parentesis.
    """
    negative = coefficient < 0
    if flip:
        negative = not negative
    magnitude = -coefficient if coefficient < 0 else coefficient
    sign = "-" if negative else "+"
    if magnitude == 1:
        return f"{sign} {text}"
    return f"{sign} {format_factor(magnitude)}{text}"
