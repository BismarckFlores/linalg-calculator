"""
Leer un sistema por teclado.

Dos maneras de entrarlo, porque el mismo sistema se puede escribir de dos
formas. O las ecuaciones se escriben como en el papel, 2x + 3y - z = 5, y de
ahi se sacan los coeficientes; o primero se da el tamano y despues se pide cada
a_ij y cada b_i por su nombre, uno a uno.

Una respuesta equivocada nunca corta nada: la misma pregunta vuelve hasta que
llega algo que sirva. Este es el unico modulo que llama a input, y todo lo que
dice esta en castellano. Devuelve la matriz aumentada [A | b] y los nombres de
las incognitas, y nada mas; que hacer con ellos lo decide otro.
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
    """Pide un numero entero dentro de un rango, insistiendo hasta conseguirlo."""
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
    """Pide un numero, aceptando enteros, decimales y fracciones."""
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
    """Pregunta algo que solo admite si o no."""
    while True:
        answer = input(f"{question} ").strip().lower()
        if answer in ("s", "si", "sí"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Responde s o n.")

def pause(message: str = "  [Enter] para continuar...") -> None:
    """
    Espera a que se pulse Enter, para poder leer una seccion antes de que
    llegue la siguiente.

    Solo si hay alguien mirando. Con la entrada redirigida no hay quien pulse
    nada, asi que el programa corre de largo en vez de quedarse esperando una
    tecla que nunca va a llegar.
    """
    if not sys.stdin.isatty():
        return
    input(message)

def ask_system() -> tuple[Matrix, list[str]]:
    """
    Pregunta como se va a escribir el sistema, y lo lee de esa manera.

    Devuelve [A | b] y los nombres de las incognitas en el orden de las
    columnas. Los nombres vienen vacios cuando los coeficientes se dieron uno
    a uno, porque entonces nadie llego a decir como se llaman las incognitas.
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
    Lee el sistema como ecuaciones, una por linea, hasta que una linea en
    blanco lo da por terminado.

    Las incognitas son las que resulten mencionar las ecuaciones, asi que
    nadie tiene que decir de antemano cuantas hay. Lo que se entendio se
    devuelve por pantalla antes de hacer nada con ello: una errata en una
    ecuacion se pilla mucho mejor viendo la lista de incognitas que viendo un
    resultado equivocado tres secciones mas adelante.
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
    Pide el tamano y despues cada coeficiente, y construye [A | b] con ellos.

    Las preguntas van ecuacion por ecuacion, terminando cada una con su
    termino independiente, porque es el orden en que se escribe un sistema:
    una ecuacion entera, y luego la siguiente.
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
    Va tomando ecuaciones hasta una linea en blanco, explicando en castellano
    lo que falle.

    El analizador lanza una excepcion por cada tipo de error y no le dice nada
    a nadie; la frase que lee una persona se decide aqui, como todas las demas
    frases del programa.
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
