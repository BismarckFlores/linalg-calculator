"""Notación científica para texto visible en Qt y MathLive."""

import re


_EXPONENT = re.compile(r"(?<![\w.])(\d+(?:\.\d*)?|\.\d+)[eE]([+-]?\d+)(?![\w.])")
_SUPERSCRIPT = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def scientific_notation(text: str) -> str:
    """Convierte literales como 2.5e-06 a 2.5 × 10⁻⁶."""
    def replace(match: re.Match[str]) -> str:
        exponent = match[2]
        digits = exponent.lstrip("+-").lstrip("0") or "0"
        sign = "-" if exponent.startswith("-") and digits != "0" else ""
        return f"{match[1]} × 10{(sign + digits).translate(_SUPERSCRIPT)}"

    return _EXPONENT.sub(replace, text)


_DISPLAY_EXPONENT = re.compile(r"(?<=[\d.]) × 10(⁻?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)")
_PLAIN_EXPONENT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


def parse_scientific_display(text: str) -> str:
    """Restaura el literal que esperan los lectores de entradas."""
    return _DISPLAY_EXPONENT.sub(lambda match: "e" + match[1].translate(_PLAIN_EXPONENT), text)
