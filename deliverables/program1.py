"""
Programa 1: resolver sistemas lineales por eliminacion de filas.

El guion que pide el enunciado. Solo ordena trabajo hecho en otra parte: prompts
lee, systems resuelve, verification comprueba y presentation escribe. Aqui no se
calcula nada, y no se decide ninguna palabra mas alla de los titulos de las
secciones.

Las secciones van numeradas segun los requisitos que responden, para que la
salida se pueda leer al lado del enunciado punto por punto.
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
    Un titulo de seccion, para localizar facilmente cada requisito en la salida.

    Antes espera a que se pulse Enter, para poder leer la seccion que acaba
    de terminar antes de que la siguiente la empuje fuera de la pantalla. El
    primer titulo no espera, porque no hay nada encima que leer.
    """
    if wait:
        pause()
    print()
    print(RULE)
    print(text)
    print(RULE)

def solve_one_system() -> None:
    """Lee un sistema, lo reduce, lo clasifica, lo resuelve y comprueba la respuesta."""
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
    """Ejecuta el programa, y ofrece resolver otro sistema antes de salir."""
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
        # Ctrl+D o Ctrl+C: se sale sin traza de error, la ejecucion se corto.
        print()

    print("\nFin del programa.")

if __name__ == "__main__":
    main()
