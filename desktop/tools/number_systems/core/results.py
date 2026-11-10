"""Formato de la lectura por piezas de un número romano."""

from core.number_systems.roman import Numeral


def roman_pieces(number: Numeral) -> str:
    return f"{number.text} = {' + '.join(piece.text for piece in number.pieces)} = {number.value}"
