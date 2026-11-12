"""Adaptadores entre MathLive y los lectores existentes del motor."""

import ast
import re

from itertools import groupby

from core.linear_algebra.handlers.equations import parse_equation
from core.numerical_methods.handlers.real_function import TRIG_FUNCTIONS, RealFunction, read_constant_expression
from core.scalar import format_scalar, to_scalar
from core.linear_algebra.vectors import parse_vector

from .number_display import parse_scientific_display


_SLASH_FRACTION = re.compile(r"(?<![\w.])(\d+)\s*/\s*(\d+)(?![\d.])")
_EXPORTED_FRACTION = re.compile(r"\(([+-]?\d+)\)\s*/\s*\(([+-]?\d+)\)")
_SUBSCRIPTS = "₀₁₂₃₄₅₆₇₈₉ₙ₊₋"


def _notation(text: str) -> str:
    text = text.replace("−", "-").replace("·", r"\cdot ").replace("≈", r"\approx ")
    text = re.sub(rf"[{_SUBSCRIPTS}]+", lambda m: "_{" + m[0].translate(
        str.maketrans(_SUBSCRIPTS, "0123456789n+-")
    ) + "}", text.replace("_", r"\_"))
    return _SLASH_FRACTION.sub(lambda m: rf"\frac{{{m[1]}}}{{{m[2]}}}", text)


def matrix_rows(text: str) -> list[list[str]]:
    rows = [
        [cell.strip() for cell in line.split(";")] if ";" in line else line.split()
        for line in text.splitlines() if line.strip()
    ]
    if not rows or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("Escribe una matriz con el mismo número de valores en cada fila.")
    return rows


def to_latex(text: str, kind: str, *, paste: bool = False) -> str:
    """Compone la notación del campo sin sustituir los lectores del motor."""
    text = parse_scientific_display(text)
    if not text.strip():
        return ""
    if kind == "function":
        return formula_latex(text)
    if kind == "equations":
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if paste and len(lines) == 1 and "=" not in lines[0]:
            return _number_latex(lines[0])
        for line in lines:
            parse_equation(line)
        lines = [_notation(re.sub(r"\((\d+/\d+)\)", r"\1", line)).replace(",", ".") for line in lines]
        if paste and len(lines) == 1:
            return lines[0]
        return r"\displaylines{" + r"\\".join(lines) + "}"
    if kind == "matrix":
        if paste and len(text.strip().splitlines()) == 1 and ";" not in text:
            try:
                return _number_latex(text)
            except ValueError:
                pass
        rows = matrix_rows(text)
        cells = ["&".join(_number_latex(cell) for cell in row) for row in rows]
        return r"\begin{bmatrix}" + r"\\".join(cells) + r"\end{bmatrix}"
    if kind == "vector":
        return ",\\ ".join(_notation(format_scalar(number)) for number in parse_vector(text))
    if kind == "integer":
        return str(int(text))
    if kind == "number":
        return _number_latex(text)
    if kind == "constant":
        try:
            return _number_latex(text)
        except ValueError:
            return formula_latex(text, constant=True)
    return _notation(text)


def _number_latex(text: str) -> str:
    text = text.strip()
    normalized = text.replace(",", ".").replace("_", "")
    # Validar primero el exponente mantiene acotada la conversión de Fraction.
    exponent = re.search(r"[eE]([+-]?\d+)$", normalized)
    if len(text) > 128 or exponent and abs(int(exponent[1])) > 10000:
        raise ValueError("El número escrito es demasiado largo.")
    number = to_scalar(text)
    if "/" in text:
        return _notation(format_scalar(number))
    if exponent:
        return rf"{normalized[:exponent.start()]}\times 10^{{{int(exponent[1])}}}"
    return normalized


def from_ascii(text: str, kind: str) -> str:
    if kind in ("function", "constant"):
        for name in ("abs", "arcsec", "arccsc", "arccot"):
            text = text.replace(f"{' '.join(name)} (", f"{name}(")
        return text.replace("l o g10 (", "log10(")

    def fraction(match: re.Match) -> str:
        numerator, denominator = match.groups()
        if denominator.startswith("-"):
            numerator = numerator[1:] if numerator.startswith("-") else "-" + numerator.lstrip("+")
        value = f"{numerator}/{denominator.lstrip('+-')}"
        return f"({value})" if kind == "equations" else value

    text = _EXPORTED_FRACTION.sub(fraction, text)
    if kind == "equations":
        text = re.sub(r"_\(([a-zA-Z0-9_ ]+)\)", r"_\1", text)
        text = re.sub(r"\(\(([+-]?\d+/\d+)\)\)", r"(\1)", text)
    return text


_RESULT_SUPERSCRIPTS = "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺"
_RESULT_CAPTIONS = re.compile(
    r"^(?:f_\d+|Ecuación\s+\d+|Componente \d+|Comprobación(?: por (?:cofactores|LU))?"
    r"|Desarrollo|Total|Posiciones pivote|Columnas (?:libres|pivote)"
    r"|Entradas principales de la matriz original|Error absoluto|Sustitución|Extremos|Evaluación"
    r"|Iteraciones|Criterio de parada|Intervalo final|Cota en x si hay continuidad|Cambio relativo|Orden de las filas):"
)
_RESULT_OPERATORS = re.compile(r"[=≈→↔<>]|\s[+−×·]\s|^\+ |^[−-]\(")


def _result_latex(text: str) -> str:
    """Traduce la notación de los resultados heredados, sin evaluar la expresión."""
    text = re.sub(r"(?<=[A-Za-z])_(\d+)", lambda m: m[1].translate(
        str.maketrans("0123456789", _SUBSCRIPTS[:10])
    ), text)
    text = _notation(text)
    text = re.sub(rf"[{_RESULT_SUPERSCRIPTS}]+", lambda m: "^{" + m[0].translate(
        str.maketrans(_RESULT_SUPERSCRIPTS, "0123456789-+")
    ) + "}", text)
    text = re.sub(r"\^([+-]?\d+)", r"^{\1}", text)
    # Las fórmulas de intervalo contienen productos y evaluaciones entre paréntesis.
    text = text.replace("(b - a) / 2", r"\frac{b-a}{2}")
    text = text.replace("f(b)(a - b) / (f(a) - f(b))", r"\frac{f(b)(a-b)}{f(a)-f(b)}")
    text = re.sub(r"(?<![\w.])\(([^()]+)\) / \(([^()]+)\)", r"\\frac{\1}{\2}", text)
    text = re.sub(r"(f\([^()]+\)) / (f′\([^()]+\))", r"\\frac{\1}{\2}", text)
    text = re.sub(
        r"^(x_\{n\+1\} = .+? - )(.+) / \[(.+)\]",
        r"\1\\frac{\2}{\3}", text,
    )
    text = re.sub(r"\b(det|rango)(?=\b)", r"\\operatorname{\1}", text)
    text = re.sub(r"\b[A-Z]{2,}(?=_(?:\{|\d)|\s*[=+]|$)", r"\\mathrm{\g<0>}", text)
    return (text.replace("×", r"\times ").replace("→", r"\to ")
            .replace("↔", r"\leftrightarrow ").replace("′", "'")
            .replace("…", r"\dots ").replace("<", r"\lt ")
            .replace("%", r"\%").replace("≤", r"\le "))


_FACT_CAPTIONS = {
    "Total", "Posiciones pivote", "Columnas libres", "Columnas pivote",
    "Entradas principales de la matriz original", "Error absoluto", "Extremos",
    "Evaluación", "Iteraciones", "Criterio de parada", "Intervalo final",
    "Cota en x si hay continuidad", "Cambio relativo", "Orden de las filas",
}
_SECTION_TITLES = {
    "Forma reducida", "Solución general", "Familia de escalares", "Matriz A",
    "Vector b", "Vector y", "Solución x", "Comprobación", "Comprobación A · x",
    "Comprobación con los escalares libres en cero",
}
_MATRIX_LABELS = {"A", "L", "U", "P", "A⁻¹", "A · A⁻¹", "A⁻¹ · A", "P · b"}
_STEP_NUMBER = re.compile(r"(?:^|\n\n)((?:Paso|Iteración) \d+)\n")


def _result_line(line: str) -> list[tuple[str, object]]:
    raw = line
    line = line.strip()
    if line.startswith("rango(A) = "):
        facts = []
        for part in line.split(" · "):
            name, _, value = part.partition(" = ")
            latex = _result_latex(name.replace("A|b", r"A\mid b"))
            facts.append(("fact", (name.capitalize(), _result_latex(value), latex if name.startswith("rango") else "", True)))
        return facts
    if line.startswith("Matriz aumentada  "):
        return [("line", "Matriz aumentada"), ("latex", r"\left[A\mid b\right]")]
    if line.startswith("Iteraciones: ") and " · " in line:
        count, threshold = line.split(" · ", 1)
        comparison = re.fullmatch(r"(.+) ([<≤]) (.+)", threshold)
        if comparison:
            criterion, operator, tolerance = comparison.groups()
            return _result_line(count) + [("fact", (criterion, _result_latex(f"E {operator} {tolerance}"), "", True))]
    if line.startswith(("Sistema Consistente", "Sistema Inconsistente")):
        return [("status", line)]
    if line in _SECTION_TITLES:
        return [("heading", line)]
    if line in _MATRIX_LABELS:
        return [("math-heading", _result_latex(line))]
    caption = _RESULT_CAPTIONS.match(line)
    if caption:
        body = line[caption.end():].strip()
        heading = caption[0][:-1]
        if heading.startswith("Ecuación ") or heading.startswith("Componente "):
            return [("heading", heading), ("latex", _result_latex(body))]
        if body and (body[0].isdigit() or body.startswith(("(", "[", "-", "−")) or _RESULT_OPERATORS.search(body)):
            if heading.startswith("f_"):
                return [("latex", _result_latex(f"{heading}: {body}"))]
            if heading in _FACT_CAPTIONS:
                return [("fact", (heading, _result_latex(body), "", True))]
            return [("heading", heading), ("latex", _result_latex(body))]
        if heading in _FACT_CAPTIONS:
            return [("fact", (heading, body, "", False))]
    summands = re.search(r" (\(\d+ sumandos en total\))$", line)
    if summands:
        return [("latex", _result_latex(line[:summands.start()])), ("line", summands[1])]
    for suffix in ("   correcto", "   NO SE CUMPLE"):
        if line.endswith(suffix):
            return [("latex", _result_latex(line[:-len(suffix)])), ("verdict", suffix.strip())]
    if (
        _RESULT_OPERATORS.search(line)
        and not re.search(r"[a-záéíóúñ]{2,}\s+[a-záéíóúñ]{2,}", line)
        and not line.endswith(".")
    ):
        kind = "solution" if raw.startswith("  ") and re.fullmatch(
            r"[a-z][\w₀-₉]* = [+-]?\d+(?:/\d+)?", line
        ) else "latex"
        return [(kind, _result_latex(line))]
    return [("line", line)]


def _result_matrix(rows: list[list[str]], environment: str = "bmatrix") -> str:
    body = r"\\".join("&".join(row) for row in rows)
    return rf"\begin{{{environment}}}{body}\end{{{environment}}}"


def _matrix_block(rows: list[list[str]]) -> tuple[str, object]:
    divider = rows[0].index("|") if "|" in rows[0] else None
    if divider is None:
        return "latex", _result_matrix([list(map(_result_latex, row)) for row in rows])

    left, right = [], []
    for row in rows:
        # Los dos lados reservan la misma altura si una fila contiene fracciones.
        phantom = r"\vphantom{\frac{1}{1}}" if any("/" in cell for cell in row) else ""
        for block, values in ((left, row[:divider]), (right, row[divider + 1:])):
            cells = list(map(_result_latex, values))
            cells[0] += phantom
            block.append(cells)
    return "augmented", (_result_matrix(left, "matrix"), _result_matrix(right, "matrix"))


def result_blocks(text: str) -> list[tuple[str, object]]:
    """Entrega fórmulas LaTeX y conserva los rótulos y explicaciones como texto."""
    if _STEP_NUMBER.match(text):
        steps = _STEP_NUMBER.split(text)
        blocks = []
        for number, content in zip(steps[1::2], steps[2::2]):
            title, separator, body = content.strip().partition("\n")
            heading = _result_line(title) if separator else []
            blocks.append(("step", (number, heading, _result_content(body if separator else title))))
        return blocks
    return _result_content(text)


def _result_content(text: str) -> list[tuple[str, object]]:
    blocks = []
    for is_matrix, group in groupby(
        text.splitlines(), lambda line: line.startswith("[ ") and line.endswith(" ]")
    ):
        if not is_matrix:
            for line in group:
                blocks.extend(_result_line(line))
            continue

        rows = [line[2:-2].split(" ] · [ ") for line in group]

        def cells(lines):
            return [[value.strip() for value in line.split(";")] for line in lines]

        if all(len(row) == 2 and " ] = [ " in row[1] for row in rows):
            variables, constants = zip(*(row[1].split(" ] = [ ", 1) for row in rows))
            a, x, b = (
                _result_matrix([list(map(_result_latex, row)) for row in matrix])
                for matrix in (cells(row[0] for row in rows), cells(variables), cells(constants))
            )
            blocks.append(("latex", rf"{a}\cdot{x}={b}"))
        else:
            blocks.append(_matrix_block(cells(row[0] for row in rows)))
    return blocks


def formula_latex(text: str, *, constant: bool = False) -> str:
    """Convierte una expresión ya validada en LaTeX para el modo visual."""
    if not text.strip():
        return ""
    function = read_constant_expression(text) if constant else RealFunction(text)

    def render(node: ast.expr, minimum: int = 0) -> str:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                return str(node.value)
            token = ast.get_source_segment(function._source, node)
            number = token.replace("_", "") if token else str(node.value)
            if "e" in number.lower():
                mantissa, exponent = number.lower().split("e")
                return rf"\left({mantissa}\times 10^{{{int(exponent)}}}\right)"
            return number
        if isinstance(node, ast.Name):
            return r"\pi" if node.id == "pi" else node.id
        if isinstance(node, ast.UnaryOp):
            sign = "-" if isinstance(node.op, ast.USub) else "+"
            precedence = 3
            content = sign + render(node.operand, precedence)
        elif isinstance(node, ast.Call):
            name = node.func.id
            argument = render(node.args[0])
            if name == "sqrt":
                return rf"\sqrt{{{argument}}}"
            if name == "abs":
                return rf"\left|{argument}\right|"
            if name == "log" and len(node.args) == 2:
                return rf"\log_{{{argument}}}\left({render(node.args[1])}\right)"
            if name in TRIG_FUNCTIONS or name in ("arcsin", "arccos", "arctan", "exp", "ln", "log"):
                return rf"\{name}\left({argument}\right)"
            return rf"\operatorname{{{name}}}\left({argument}\right)"
        else:
            assert isinstance(node, ast.BinOp)
            if isinstance(node.op, ast.Div):
                precedence = 2
                content = rf"\frac{{{render(node.left)}}}{{{render(node.right)}}}"
            elif isinstance(node.op, ast.Pow):
                precedence = 4
                exponent = render(node.right)
                if (
                    isinstance(node.left, ast.Call) and node.left.func.id in TRIG_FUNCTIONS
                    and isinstance(node.right, ast.Constant) and isinstance(node.right.value, int)
                ):
                    name = node.left.func.id
                    argument = render(node.left.args[0])
                    content = rf"\{name}^{{{exponent}}}\left({argument}\right)"
                else:
                    base = render(node.left, precedence + 1)
                    content = rf"{base}^{{{exponent}}}"
            else:
                sign, precedence = {
                    ast.Add: ("+", 1), ast.Sub: ("-", 1), ast.Mult: (r"\cdot ", 2),
                }[type(node.op)]
                factor = node.right
                if isinstance(factor, ast.BinOp) and isinstance(factor.op, ast.Pow):
                    factor = factor.left
                if (
                    isinstance(node.op, ast.Mult)
                    and isinstance(node.left, ast.Constant)
                    and isinstance(factor, ast.Name) and factor.id == "x"
                ):
                    sign = ""
                content = render(node.left, precedence) + sign + render(node.right, precedence + 1)
        return rf"\left({content}\right)" if precedence < minimum else content

    return render(function._tree)
