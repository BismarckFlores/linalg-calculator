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
│   ├── elimination.py    # row echelon form and reduced row echelon form
│   ├── systems.py        # classification and solution of a linear system
│   └── verification.py   # putting a solution back into the original system
└── docs/                 # design notes
```

This section grows as modules land. Nothing is listed here before it exists.

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
repository is the source of truth; the handed-in file is a build artefact.

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

`to_ref` and `to_rref` run on one of those, so a reduction and its step by step
are two readings of the same walk. Both return an `Elimination`, which carries
the result, the log and the position of every pivot — and from the pivots come
the rank, the pivot columns and the free ones.

`solve` reads an augmented matrix `[A | b]` and classifies the system by
comparing ranks: `rank(A) < rank(A|b)` has no solution, `rank(A) = rank(A|b) <
unknowns` has infinitely many, and equality with the number of unknowns has
exactly one. With `Method.GAUSS` it finishes by back substitution and keeps every
step of it; with `Method.GAUSS_JORDAN` it reads the values straight off the last
column. The two always agree.

`verify` is the independent check: hand it A, b and the values found and it
evaluates every equation of the original system, comparing both sides exactly.
It trusts nothing the elimination did, which is the only way the check is worth
anything.
