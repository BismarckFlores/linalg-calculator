"""
The number every matrix entry is stored as: an exact rational.

Using `Fraction` instead of `float` is what lets a step print as
`f_2 -> (1/3)*f_2` and a solution as `x= 1/3`, never as `0.3333333333333333`.
Rounding never enters the calculation, so the elimination is exact from end to
end and the results can be checked against the ones done by hand.
"""

from fractions import Fraction

# What an entry is once it is inside a matrix: always an exact Fraction.
Scalar = Fraction

# What `to_scalar` knows how to read: a number, or text like "3", "-2.5", "1/3".
NumberLike = int | float | Fraction | str

def to_scalar(value: NumberLike) -> Scalar:
    """Normalize a number or a piece of text into the exact Scalar type."""
    if isinstance(value, Fraction):
        return value

    if isinstance(value, bool):
        # bool is a subclass of int, and True as a matrix entry is always a bug.
        raise TypeError("A boolean is not a valid matrix entry.")

    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        # Through str() so 0.1 becomes 1/10 and not a binary approximation.
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
    """Write a scalar the way it goes on the blackboard: 3, -4, 1/3."""
    value = to_scalar(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"

def format_factor(value: NumberLike) -> str:
    """
    Write a scalar that multiplies a row inside a step label.

    Negatives and fractions get parentheses so the label stays readable:
    `f_3 -> (-1)*f_3` and `f_2 -> (1/3)*f_2`, but `f_1 -> 5*f_1`.
    """
    value = to_scalar(value)
    text = format_scalar(value)
    if value < 0 or value.denominator != 1:
        return f"({text})"
    return text