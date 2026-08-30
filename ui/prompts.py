"""
Reading a system from the keyboard, one number at a time.

The assignment asks for the size first and then the coefficients one by one, so
that is what this does: m, n, and then every a_ij and b_i named as it is asked
for. A wrong answer is not fatal — the same question comes back until it gets a
number it can use.

This is the only module that calls `input`, and everything it says is in
Spanish. It returns the augmented matrix [A | b] and nothing else; what to do
with it is somebody else's decision.
"""

from core.matrix import Matrix
from core.scalar import Scalar, to_scalar

SIZE_LIMIT = 10

NUMBER_HELP = "Se admiten enteros, decimales (2.5 o 2,5) y fracciones (1/3)."

def ask_int(question: str, minimum: int = 1, maximum: int = SIZE_LIMIT) -> int:
    """Ask for a whole number inside a range, insisting until one arrives."""
    while True:
        answer = input(f"{question} ").strip()
        if not answer:
            print("  No escribiste nada.")
            continue
        try:
            number = int(answer)
        except ValueError:
            print(f"  '{answer}' no es un número entero. Escribe un entero.")
            continue
        if not minimum <= number <= maximum:
            print(f"  Tiene que estar entre {minimum} y {maximum}.")
            continue
        return number

def ask_scalar(question: str) -> Scalar:
    """Ask for one number, accepting integers, decimals and fractions."""
    while True:
        answer = input(f"{question} ").strip()
        if not answer:
            print("  No escribiste nada.")
            continue
        try:
            return to_scalar(answer)
        except (TypeError, ValueError):
            print(f"  '{answer}' no es un número. Prueba con 3, -2.5 o 1/3.")

def ask_yes_no(question: str) -> bool:
    """Ask something that only takes yes or no."""
    while True:
        answer = input(f"{question} ").strip().lower()
        if answer in ("s", "si", "sí"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Responde s o n.")

def ask_system() -> Matrix:
    """
    Ask for the size and then every coefficient, and build [A | b] out of them.

    The questions go equation by equation, ending each one with its constant
    term, because that is the order in which the system is written down: a whole
    equation, then the next.
    """
    print("Datos del sistema de ecuaciones lineales A x = b")
    print()
    equations = ask_int("Número de ecuaciones (m):")
    unknowns = ask_int("Número de variables (n):")

    print()
    print(f"Ahora los {equations * (unknowns + 1)} coeficientes, ecuación por ecuación.")
    print(NUMBER_HELP)

    rows: list[list[Scalar]] = []
    for i in range(1, equations + 1):
        print(f"\nEcuación {i}:")
        row = [ask_scalar(f"  a_{i}{j} =") for j in range(1, unknowns + 1)]
        row.append(ask_scalar(f"  b_{i}  ="))
        rows.append(row)

    return Matrix(rows)