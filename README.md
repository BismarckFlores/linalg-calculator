# linalg-calculator

Calculadora de Álgebra Lineal — Universidad Americana (UAM), Álgebra Lineal
(MTM0120).

A linear algebra engine written in plain Python. It grows one assignment at a
time, and the files handed in to the course are generated from it rather than
written by hand.

## Layout

```
linalg-calculator/
├── core/                 # the engine: mathematics, not a word of interface
│   ├── scalar.py         # the exact number (Fraction) and how it is written
│   ├── matrix.py         # the matrix and the operations that need no explaining
│   ├── steps.py          # the step by step (Step, StepLog)
│   ├── worksheet.py      # matrix + record: the blackboard operations happen on
│   ├── elimination.py    # row elimination, to the echelon form and the reduced one
│   ├── systems.py        # classification and solution of a linear system
│   └── verification.py   # putting a solution back into the original system
├── ui/                   # everything a person reads, in Spanish
│   ├── presentation.py   # engine objects → the words that go on screen
│   └── prompts.py        # reading a system from the keyboard, one number at a time
├── deliverables/         # the scripts handed in to the course
│   ├── program1.py       # Programa 1: systems by row elimination
│   └── out/              # generated single files, not versioned
├── build.py              # assembles the single file that gets handed in
├── translations.py       # Spanish for every docstring and comment it carries
└── docs/
    ├── usage.md          # how to run everything, and what it asks for
    ├── how-it-works.md   # one system solved end to end, module by module
    ├── reference.md      # what each module exposes, and how they connect
    └── design.md         # why the pieces are split where they are
```

```bash
python -m deliverables.program1     # run Programa 1
python build.py                     # write deliverables/out/Programa 1_GrupoN.py
python check.py                     # smoke test the engine
```

This section grows as modules land. Nothing is listed here before it exists.

**Start with [docs/usage.md](docs/usage.md)** to run it, and
[docs/how-it-works.md](docs/how-it-works.md) to understand what it does.
[docs/reference.md](docs/reference.md) is what to open before changing
something: it lists what every module exposes without you having to read it.

## Rules

**Code is written in English; the deliverables are written in Spanish.** Every
identifier, comment, docstring and document in this repository is in English,
including the exception messages the engine raises. The files handed in to the
course are the exception: they go to a class taught in Spanish, so their block
comments and everything they print are in Spanish.

**`core/` does not talk.** No `print`, no message addressed to a person. It
returns data and raises exceptions aimed at whoever is writing the code. The
wording a user reads is decided in the interface layer, which is why every front
end says exactly the same thing.

**Standard library only.** No NumPy, no SciPy, no linear algebra helpers from
`math`: the assignments require the algorithms to be built from lists,
conditionals, loops and functions. `fractions`, `dataclasses`, `enum` and
`tkinter` are standard and are allowed.

**Deliverables are generated, not written.** Each file handed in is a single
self-contained script produced out of the modules in this repository. The
repository is the source of truth; the handed-in file is a build artefact, and
`build.py` translates its docstrings and comments into Spanish on the way out.

## The engine so far

`Matrix` is a value: a rectangle of exact rationals, indexed from 1 through
`elem`, `row` and the row operations, the way they are written on paper. Its
elementary row operations return a new matrix and say nothing about themselves.

`StepLog` is a record: the matrix you started from and one `Step` per operation.
`snapshot(k)` returns the k-th matrix of the chain, and that single method is the
whole 'previous / next' of any interface.

`Worksheet` is the two together — the blackboard, where an operation both
happens and gets written down:

```python
sheet = Worksheet(a)
sheet.swap(1, 2)
sheet.scale(1, Fraction(1, 3))
sheet.add_scaled(2, 1, -4)
sheet.matrix        # where the work stands now
sheet.log           # every operation that got it there
```

`to_ref` runs on one of those, so a reduction and its step by step are two
readings of the same walk. It returns an `Elimination`, which carries the
result, the log and the position of every pivot — and from the pivots come the
rank, the pivot columns and the free ones.

`solve` reads an augmented matrix `[A | b]` and classifies the system by
comparing ranks: `rank(A) < rank(A|b)` has no solution, `rank(A) = rank(A|b) <
unknowns` has infinitely many, and equality with the number of unknowns has
exactly one. In that last case it clears the unknowns by back substitution, from
the last to the first, and keeps every one of those steps: seeing the echelon
matrix and then the clearing is the point of the method.

`verify` is the independent check: hand it A, b and the values found and it
evaluates every equation of the original system, comparing both sides exactly.
It trusts nothing the elimination did, which is the only way the check is worth
anything.

## The wording

`ui/presentation.py` turns those objects into the text a person reads, and it is
the only file in the project that writes Spanish. It builds strings and returns
them — no `print`, no widgets — so whatever displays them decides where they go
while the words stay the same everywhere.

It also owns the two pieces of formatting that need to know what a matrix
*means*: the bar between A and b in `[ 1  -2   1 | 0 ]`, which `Matrix.__str__`
cannot draw because only a system knows its last column is different, and the
names of the unknowns (`x`, `y`, `z`, `w`, then `x5` and up).

`ui/prompts.py` is the other half: the only module in the project that calls
`input`. It asks for the size and then for every coefficient by name — `a_11`,
`a_12`, `b_1` — and a wrong answer just asks again, so nothing a person types
can end the program. It hands back the augmented matrix and decides nothing
else. End of input (Ctrl+D) is left to travel up to whoever started the
program, which is the only place that knows whether stopping is an error.
