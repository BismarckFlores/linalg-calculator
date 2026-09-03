"""
Programa 1: solving linear systems by row elimination.

The script the assignment asks for. It only sequences work done elsewhere:
`prompts` reads, `systems` solves, `verification` checks and `presentation`
writes. Nothing here calculates anything, and nothing here decides any wording
beyond the section headings.

The sections are numbered after the requirements they answer, so the output can
be read next to the assignment sheet point by point.
"""

from core.systems import SystemKind, solve
from core.verification import verify
from ui.presentation import (
    describe,
    render_augmented,
    render_equations,
    render_steps,
    render_substitutions,
    render_values,
    render_verification,
)
from ui.prompts import ask_system, ask_yes_no, pause

TITLE = (
    "PROGRAMA 1 - Solución de Sistemas de Ecuaciones Lineales\n"
    "                 por Eliminación por Filas"
)
RULE = "=" * 70

def banner(text: str, wait: bool = True) -> None:
    """
    A section heading, so each requirement is easy to find in the output.

    It waits for Enter first, so the section just finished can be read before
    the next one pushes it off the screen. The first heading of a system has
    nothing above it to read, so it does not wait.
    """
    if wait:
        pause()
    print()
    print(RULE)
    print(text)
    print(RULE)

def solve_one_system() -> None:
    """Read a system, reduce it, classify it, solve it and check the answer."""
    banner("1. ENTRADA DE DATOS", wait=False)
    augmented, names = ask_system()
    solution = solve(augmented)
    unknowns = solution.unknowns

    banner("2. MATRIZ AUMENTADA INICIAL")
    print(render_augmented(augmented, unknowns))

    banner("3. ELIMINACIÓN POR FILAS")
    print(render_steps(solution.log, unknowns))

    banner("4. SISTEMA EQUIVALENTE")
    print("La matriz escalonada, leída otra vez como ecuaciones:")
    print()
    print(render_equations(solution, names))

    banner("5. CLASIFICACIÓN DEL SISTEMA")
    print(f"rango(A) = {solution.coefficient_rank}")
    print(f"rango(A|b) = {solution.rank}")
    print(f"número de incógnitas = {solution.unknowns}")
    print()
    print(describe(solution))

    banner("6. SOLUCIÓN")
    if solution.substitutions:
        print("Despeje, de la última incógnita a la primera:")
        print(render_substitutions(solution, names))
        print()
    print(render_values(solution, names))

    banner("7. COMPROBACIÓN")
    if solution.kind is SystemKind.UNIQUE:
        print("Se sustituyen los valores hallados en el sistema original:")
        print()
        print(render_verification(
            verify(solution.coefficients, solution.constants, solution.values)
        ))
    else:
        print("No hay una solución única que sustituir, así que no hay nada")
        print("que comprobar en el sistema original.")

def main() -> None:
    """Run the program, and offer to solve another system before leaving."""
    print(RULE)
    print(TITLE)
    print(RULE)

    try:
        while True:
            solve_one_system()
            print()
            if not ask_yes_no("¿Resolver otro sistema? (s/n):"):
                break
    except (EOFError, KeyboardInterrupt):
        # Ctrl+D or Ctrl+C: leave without a traceback, the run was cut short.
        print()

    print("\nFin del programa.")

if __name__ == "__main__":
    main()