"""Adaptadores entre MathLive y los lectores existentes del motor."""

import ast
import re

from core.equations import parse_equation
from core.real_function import RealFunction
from core.scalar import format_scalar, to_scalar
from core.vectors import parse_vector


_SLASH_FRACTION = re.compile(r"(?<![\w.])(\d+)\s*/\s*(\d+)(?![\d.])")
_EXPORTED_FRACTION = re.compile(r"\(([+-]?\d+)\)\s*/\s*\(([+-]?\d+)\)")
_SUBSCRIPTS = "₀₁₂₃₄₅₆₇₈₉"


def _notation(text: str) -> str:
    text = text.replace("−", "-").replace("·", r"\cdot ").replace("≈", r"\approx ")
    text = re.sub(rf"[{_SUBSCRIPTS}]+", lambda m: "_{" + m[0].translate(
        str.maketrans(_SUBSCRIPTS, "0123456789")
    ) + "}", text.replace("_", r"\_"))
    return _SLASH_FRACTION.sub(lambda m: rf"\frac{{{m[1]}}}{{{m[2]}}}", text)


def matrix_rows(text: str) -> list[list[str]]:
    rows = [
        [cell.strip() for cell in line.split(";")] if ";" in line else line.split()
        for line in text.splitlines() if line.strip()
    ]
    if len(rows) != 2 or any(len(row) != 2 for row in rows):
        raise ValueError("Escribe una matriz de 2 × 2, con dos valores en cada fila.")
    return rows


def to_latex(text: str, kind: str, *, paste: bool = False) -> str:
    """Compone la notación del campo sin sustituir los lectores del motor."""
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
            return _number_latex(text)
        rows = matrix_rows(text)
        cells = ["&".join(_number_latex(cell) for cell in row) for row in rows]
        return r"\begin{pmatrix}" + r"\\".join(cells) + r"\end{pmatrix}"
    if kind == "vector":
        return ",\\ ".join(_notation(format_scalar(number)) for number in parse_vector(text))
    if kind == "integer":
        return str(int(text))
    if kind == "number":
        return _number_latex(text)
    return _result_latex(text)


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
    return normalized.lower().replace("e", r"\mathrm{e}")


def from_ascii(text: str, kind: str) -> str:
    if kind == "function":
        return text.replace("a b s (", "abs(").replace("l o g10 (", "log10(")

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


def _result_latex(text: str) -> str:
    def words(line: str) -> str:
        escaped = re.sub(r"([%&$#_{}])", r"\\\1", line)
        return rf"\text{{{escaped}}}"

    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            lines.append(r"\vphantom{X}")
        elif ("=" in line or "≈" in line) and not line.startswith("La fila "):
            caption, separator, expression = line.partition(":")
            prefix = words(caption + ": ") if separator else ""
            expression = expression if separator else caption
            expression, _, note = expression.strip().partition("   ")
            lines.append(prefix + _notation(expression) + (r"\quad" + words(note.strip()) if note else ""))
        else:
            lines.append(words(line))
    return r"\begin{array}{l}" + r"\\".join(lines) + r"\end{array}"


def formula_latex(text: str) -> str:
    """Convierte una expresión ya validada en LaTeX para el modo visual."""
    if not text.strip():
        return ""
    function = RealFunction(text)

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
            if name in ("sin", "cos", "tan", "exp", "ln", "log"):
                return rf"\{name}\left({argument}\right)"
            return rf"\operatorname{{{name}}}\left({argument}\right)"
        else:
            assert isinstance(node, ast.BinOp)
            if isinstance(node.op, ast.Div):
                precedence = 2
                content = rf"\frac{{{render(node.left)}}}{{{render(node.right)}}}"
            elif isinstance(node.op, ast.Pow):
                precedence = 4
                base = render(node.left, precedence + 1)
                content = rf"{base}^{{{render(node.right)}}}"
            else:
                sign, precedence = {
                    ast.Add: ("+", 1), ast.Sub: ("-", 1), ast.Mult: (r"\cdot ", 2),
                }[type(node.op)]
                content = render(node.left, precedence) + sign + render(node.right, precedence + 1)
        return rf"\left({content}\right)" if precedence < minimum else content

    return render(function._tree)
