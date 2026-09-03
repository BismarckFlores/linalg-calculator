"""
Reading a system from the keyboard.

Two ways in, because the same system can be written down two ways. Either the
equations go in as they are written on paper, `2x + 3y - z = 5`, and the
coefficients are read out of them; or the size comes first and then every a_ij
and b_i is named and asked for one at a time.

A wrong answer is never fatal: the same question comes back until it gets
something it can use. This is the only module that calls `input`, and everything
it says is in Spanish. It returns the augmented matrix [A | b] and the names of
the unknowns, and nothing else; what to do with them is somebody else's
decision.
"""

import sys

from core.equations import (
    Equation,
    EquationError,
    MissingEquals,
    UnreadableTerm,
    parse_equation,
    to_augmented,
    unknown_names,
)
from core.matrix import Matrix
from core.scalar import Scalar, to_scalar

SIZE_LIMIT = 10

NUMBER_HELP = "Se admiten enteros, decimales (2.5 o 2,5) y fracciones (1/3)."

EQUATION_HELP = "Por ejemplo:  2x + 3y - z = 5   o   2x = 3y + 1"

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

def pause(message: str = "  [Enter] para continuar...") -> None:
    """
    Wait for Enter, so one section can be read before the next one arrives.

    Only when a person is watching. With the input redirected there is nobody
    to press anything, so the program runs straight through instead of stopping
    on a prompt that will never be answered.
    """
    if not sys.stdin.isatty():
        return
    input(message)

def ask_system() -> tuple[Matrix, list[str]]:
    """
    Ask how the system is going to be written down, and read it that way.

    Comes back with [A | b] and the names of the unknowns in column order. The
    names are empty when the coefficients were given one by one, because then
    nobody ever said what the unknowns are called.
    """
    print("Datos del sistema de ecuaciones lineales A x = b")
    print()
    print("  1) Escribir las ecuaciones tal como se leen")
    print("  2) Dar los coeficientes uno por uno")
    print()

    if ask_int("¿Cómo prefieres entrarlo? (1/2):", 1, 2) == 1:
        return ask_equations()
    return ask_coefficients(), []

def ask_equations() -> tuple[Matrix, list[str]]:
    """
    Read the system as equations, one per line, until a blank line ends it.

    The unknowns are whatever the equations turn out to mention, so nobody has
    to say up front how many there are. What was understood is read back before
    anything is done with it: a typo in an equation is much easier to catch as a
    list of unknowns than as a wrong answer three sections later.
    """
    while True:
        print()
        print("Escribe una ecuación por línea. Una línea en blanco termina.")
        print(EQUATION_HELP)
        print(NUMBER_HELP)
        print()

        equations = _read_equations()
        names = unknown_names(equations)

        if not names:
            print("\n  Ninguna de las ecuaciones tiene incógnitas. Empecemos de nuevo.")
            continue
        if len(names) > SIZE_LIMIT:
            print(f"\n  Son {len(names)} incógnitas y el máximo es {SIZE_LIMIT}.")
            continue

        print()
        print(f"Incógnitas encontradas ({len(names)}): {', '.join(names)}")
        return to_augmented(equations, names), names

def ask_coefficients() -> Matrix:
    """
    Ask for the size and then every coefficient, and build [A | b] out of them.

    The questions go equation by equation, ending each one with its constant
    term, because that is the order in which the system is written down: a whole
    equation, then the next.
    """
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

def _read_equations() -> list[Equation]:
    """
    Take equations until a blank line, explaining in Spanish whatever fails.

    The parser raises one exception per kind of mistake and says nothing to
    anybody; the sentence a person reads is decided here, like every other
    sentence in the program.
    """
    equations: list[Equation] = []

    while len(equations) < SIZE_LIMIT:
        text = input(f"  Ecuación {len(equations) + 1}: ").strip()

        if not text:
            if equations:
                return equations
            print("  Escribe al menos una ecuación.")
            continue

        try:
            equations.append(parse_equation(text))
        except MissingEquals:
            print("  Falta el '='. Una ecuación se escribe como  2x + 3y = 5")
        except UnreadableTerm as error:
            print(f"  No entiendo la parte '{error.text}'. Revísala.")
        except EquationError:
            print("  No pude leer esa ecuación. Escríbela otra vez.")

    print(f"  Llegaste al máximo de {SIZE_LIMIT} ecuaciones.")
    return equations
