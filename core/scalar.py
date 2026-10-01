"""
El numero en que se guarda cada entrada de una matriz: un racional exacto.

Usar Fraction en vez de float es lo que permite que un paso se imprima como
f_2 -> (1/3)*f_2 y una solucion como x = 1/3, y nunca como 0.3333333333333333.
El redondeo no entra nunca en el calculo, asi que la eliminacion es exacta de
principio a fin y los resultados se pueden comparar con los hechos a mano.
"""

from fractions import Fraction

# Lo que es una entrada una vez dentro de una matriz: siempre una fraccion exacta.
Scalar = Fraction

# Lo que to_scalar sabe leer: un numero, o texto como "3", "-2.5", "1/3".
NumberLike = int | float | Fraction | str

def to_scalar(value: NumberLike) -> Scalar:
    """Convierte un numero o un texto en el tipo exacto Scalar."""
    if isinstance(value, Fraction):
        return value

    if isinstance(value, bool):
        # bool hereda de int, y un True como entrada de una matriz siempre es un error.
        raise TypeError("A boolean is not a valid matrix entry.")

    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        # Pasando por str() para que 0.1 sea 1/10 y no una aproximacion binaria.
        return Fraction(str(value))
    if isinstance(value, str):
        text = value.strip().replace(",", ".")
        if not text:
            raise ValueError("Empty value.")
        try:
            return Fraction(text)
        except ZeroDivisionError:
            raise ValueError(f"'{value}' divides by zero.") from None
        except ValueError:
            raise ValueError(f"'{value}' is not a valid number.") from None
    raise TypeError(f"Cannot read {value!r} as a number.")

def format_scalar(value: NumberLike) -> str:
    """Escribe un numero como se escribe en el pizarron: 3, -4, 1/3."""
    value = to_scalar(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"

def format_factor(value: NumberLike) -> str:
    """
    Escribe el numero que multiplica a una fila dentro de la etiqueta de un paso.

    Los negativos y las fracciones llevan parentesis para que la etiqueta se
    lea bien: f_3 -> (-1)*f_3 y f_2 -> (1/3)*f_2, pero f_1 -> 5*f_1.
    """
    value = to_scalar(value)
    text = format_scalar(value)
    if value < 0 or value.denominator != 1:
        return f"({text})"
    return text
