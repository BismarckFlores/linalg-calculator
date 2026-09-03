"""
The way in: `python -m gui`, from the root of the repository.

Run as a module and not as a file, for the same reason the terminal version is
run as `python -m deliverables.program1`: `import core` only resolves when the
root of the repository is the directory Python started from.
"""

from .app import main

if __name__ == "__main__":
    main()
