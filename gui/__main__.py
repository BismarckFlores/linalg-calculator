"""
La puerta de entrada: python -m gui, desde la raiz del repositorio.

Se ejecuta como modulo y no como archivo por lo mismo que la version de terminal
se ejecuta con python -m deliverables.program1: import core solo funciona cuando
la raiz del repositorio es el directorio desde el que arranco Python.
"""

from .app import main

if __name__ == "__main__":
    main()
