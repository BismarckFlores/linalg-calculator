"""
Everything a person reads, written in Spanish.

The engine returns data and never a sentence; this is where the wording is
decided, once, so that every front end says exactly the same thing. These
helpers build strings and nothing else: no `print`, no widgets.

The three classifications are worded exactly as the assignment demands them,
down to the capital letters.
"""

import re
from collections.abc import Sequence

from core.matrix import Matrix
from core.scalar import Scalar, format_factor, format_scalar
from core.steps import StepLog
from core.systems import Solution, SystemKind
from core.verification import RowCheck, Verification

# Named after the blackboard for the sizes that fit on it; x5, x6... beyond.
UNKNOWN_NAMES = ("x", "y", "z", "w")

# Digits as subscripts, for writing f_12 as f₁₂ where the glyphs are available.
SUBSCRIPTS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

CLASSIFICATIONS = {
    SystemKind.UNIQUE: "Sistema Consistente Determinado: Presenta Solución Única.",
    SystemKind.INFINITE: "Sistema Consistente Indeterminado: Presenta Infinitas Soluciones.",
    SystemKind.INCONSISTENT: "Sistema Inconsistente: Sin Solución.",
}

def unknown_name(column: int, names: Sequence[str] = ()) -> str:
    """
    The name of the unknown sitting in a 1-based column.

    Whatever the person called it, when they wrote the system out as equations
    and there is a name to use. Otherwise the blackboard default: x, y, z, w,
    and x5 upwards once those run out.
    """
    if column <= len(names):
        return names[column - 1]
    if column <= len(UNKNOWN_NAMES):
        return UNKNOWN_NAMES[column - 1]
    return f"x{column}"

def render_augmented(matrix: Matrix, unknowns: int, indent: str = "  ") -> str:
    """
    The augmented matrix with the bar between A and b: `[ 1  -2   1 |  0 ]`.

    The bar is drawn here and not in `Matrix.__str__` because only a system
    knows that its last column means something different from the rest.
    """
    texts = [[format_scalar(value) for value in row] for row in matrix.data]
    # A and b get their own width, so a wide coefficient does not stretch b too.
    left_width = max((len(text) for row in texts for text in row[:unknowns]), default=1)
    right_width = max((len(text) for row in texts for text in row[unknowns:]), default=1)

    lines = []
    for row in texts:
        left = "  ".join(text.rjust(left_width) for text in row[:unknowns])
        right = "  ".join(text.rjust(right_width) for text in row[unknowns:])
        lines.append(f"{indent}[ {left} | {right} ]")
    return "\n".join(lines)

def render_steps(log: StepLog, unknowns: int) -> str:
    """The whole elimination, one numbered block per elementary operation."""
    if log.is_empty():
        return "No hizo falta ninguna operación: la matriz ya estaba escalonada."

    blocks = []
    for number, step in enumerate(log, start=1):
        blocks.append(
            f"Paso {number}:  {step.label}\n{render_augmented(step.after, unknowns)}"
        )
    return "\n\n".join(blocks)

def pretty_label(label: str) -> str:
    """
    A step label in typographic notation: `f₂ → f₂ + 3 · f₁`.

    The same operation the course writes as `f_2 -> f_2 + 3*f_1`, which is what
    `core/steps.py` produces and what the handed-in file prints. A window has the
    glyphs for it and a plain transcript cannot be trusted to, so the choice
    belongs to whoever is drawing rather than to the engine.
    """
    text = label.replace("<->", "↔").replace("->", "→").replace("*", " · ")
    return re.sub(r"f_(\d+)", lambda match: "f" + match[1].translate(SUBSCRIPTS), text)

def describe(solution: Solution) -> str:
    """The classification, in the exact words the assignment asks for."""
    return CLASSIFICATIONS[solution.kind]

def render_values(solution: Solution, names: Sequence[str] = ()) -> str:
    """The value of each unknown, or the free ones when there are infinitely many."""
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
    """The echelon matrix written back as the system of equations it stands for."""
    echelon = solution.result
    constants = solution.unknowns + 1
    rows: list[tuple[str, str, str]] = []

    for row in range(1, echelon.rows + 1):
        pieces = [
            _term(echelon.elem(row, col), unknown_name(col, names))
            for col in range(1, constants)
            if echelon.elem(row, col) != 0
        ]
        left = " ".join(pieces).removeprefix("+ ") if pieces else "0"
        rows.append((f"f_{row}", left, format_scalar(echelon.elem(row, constants))))

    width = max(len(left) for _tag, left, _constant in rows)
    lines = [f"  {tag}:  {left:>{width}} = {constant}" for tag, left, constant in rows]
    return "\n".join(lines)

def render_substitutions(solution: Solution, names: Sequence[str] = ()) -> str:
    """The clearing, written out line by line the way it is done on paper."""
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
            _term(coefficient, format_factor(value))
            for (coefficient, _col), value in zip(step.terms, values)
        )
        moved = " ".join(
            _term(coefficient, format_factor(value), flip=True)
            for (coefficient, _col), value in zip(step.terms, values)
        )

        lines.append(f"{head}{name} {symbolic} = {constant}")
        lines.append(f"{indent}{name} {replaced} = {constant}")
        lines.append(f"{indent}{name} = {constant} {moved}")
        lines.append(f"{indent}{name} = {format_scalar(step.value)}")
        lines.append("")

    return "\n".join(lines).rstrip()

def render_verification(verification: Verification) -> str:
    """
    Each equation of the original system with the values put into it.

    Two lines per equation: the substitution as it is written, and what each
    side adds up to. The point is that the reader can follow the arithmetic,
    not just be told that it worked.
    """
    lines = []
    # Pad the numbering so equation 9 and equation 10 still line up.
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
    The 1-based row that reads `0 ... 0 | k` with k not zero.

    That row is the whole reason an inconsistent system is inconsistent, so the
    reader is shown it by name rather than told that one exists somewhere.
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
    """'1 pivote' or '3 pivotes', so nothing ever reads as '1 pivote(s)'."""
    return f"{count} {singular if count == 1 else plural}"

def _substituted(check: RowCheck) -> str:
    """One equation with every unknown replaced by its value: `1*(29) + (-2)*(16)`."""
    pieces = [
        f"{format_factor(coefficient)}*({format_scalar(value)})"
        for coefficient, value, _col in check.terms
    ]
    return " + ".join(pieces) if pieces else "0"

def _term(coefficient: Scalar, text: str, flip: bool = False) -> str:
    """One term with its sign in front: '+ y', '- 3*z', '+ (1/3)*x'."""
    negative = coefficient < 0
    if flip:
        negative = not negative
    magnitude = -coefficient if coefficient < 0 else coefficient
    sign = "-" if negative else "+"
    if magnitude == 1:
        return f"{sign} {text}"
    return f"{sign} {format_factor(magnitude)}*{text}"