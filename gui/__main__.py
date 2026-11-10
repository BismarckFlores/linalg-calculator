"""
La puerta de entrada: python -m gui, desde la raiz del repositorio.

La ejecucion como modulo permite resolver los imports de gui, core y ui.
"""

from .app import main

if __name__ == "__main__":
    main()
