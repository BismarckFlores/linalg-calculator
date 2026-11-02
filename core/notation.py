"""La multiplicacion que se omite al escribir matematica, compartida por los lectores."""

import io
import tokenize
from collections.abc import Collection


def explicit_products(
    text: str, functions: Collection[str] = (), *, scientific: bool = True,
) -> str:
    """Hace explicitos productos como 5x, 2(x+1) y (x+1)(x-1), sin evaluar.

    Conserva las llamadas conocidas y los nombres completos: x1 no es x*1.
    Cada lector valida despues su propia gramatica. El lineal no usa notacion
    cientifica: 1e3x alli es el coeficiente 1 de la incognita e3x.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError):
        # Un texto incompleto debe recibir el error del lector que lo esperaba.
        return text
    if not scientific and any(
        token.type == tokenize.NUMBER and "e" in token.string.lower() for token in tokens
    ):
        return text

    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    insertions: list[int] = []
    previous = None
    for token in tokens:
        if token.type in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                          tokenize.DEDENT, tokenize.COMMENT, tokenize.ENDMARKER):
            continue
        if previous is not None:
            ends_factor = previous.type in (tokenize.NUMBER, tokenize.NAME) or previous.string == ")"
            starts_factor = token.type == tokenize.NAME or token.string == "("
            # Un numero tras un parentesis tambien es un factor: (x+1)2.
            starts_factor |= previous.string == ")" and token.type == tokenize.NUMBER
            call = previous.type == tokenize.NAME and previous.string in functions and token.string == "("
            if ends_factor and starts_factor and not call:
                insertions.append(offsets[token.start[0] - 1] + token.start[1])
        previous = token

    parts: list[str] = []
    start = 0
    for position in insertions:
        parts.extend((text[start:position], "*"))
        start = position
    parts.append(text[start:])
    return "".join(parts)
