"""
The window: a third front end over the same engine.

`deliverables/program1.py` drives `core/` from a terminal, the built file does
the same on its own, and this package draws it. None of the three holds a line
of arithmetic: they all call `core/` and hand what comes back to
`ui/presentation.py` for the wording.

Nothing here is ever built into the file handed in. The course wants one
self-contained script with no dependencies, and this package needs
CustomTkinter, so `build.py` does not know it exists.
"""
