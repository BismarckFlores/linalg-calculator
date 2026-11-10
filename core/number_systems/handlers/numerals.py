"""Normalización común de enteros en otras bases y números romanos."""


def normalize_numeral(text: str) -> str:
    """Conserva los símbolos, sin espacios y en mayúsculas."""
    return "".join(text.split()).upper()
