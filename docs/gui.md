# The window

A desktop front end over the same engine, built with CustomTkinter. It does not
replace `python -m deliverables.program1`; it is a third caller of `core/`,
beside the terminal program and the single file handed in to the course.

```bash
pip install -r requirements-gui.txt
python -m gui
```

Run it as a module, from the repository root, for the same reason the terminal
version is run as `python -m deliverables.program1`: `import core` only resolves
when the root is the directory Python started from.

## What is on it

The sidebar lists what works, and nothing else:

| Row | What it does |
| --- | --- |
| **Operaciones Matriciales** | `A + B`, `A − B`, `A × B`, `k · A`, `Aᵀ`. Each matrix is resized with its own steppers, and B follows A wherever the shapes have to agree. |
| **Eliminación Gaussiana** | Solves `A x = b`: the step by step, the classification, the clearing and the verification. The system goes in as coefficients or as written equations, and Gauss or Gauss-Jordan is chosen inside the page. |
| **Formas Escalonadas** | Takes a matrix as it stands and answers the definition: is it in echelon form, is it in the reduced one. Then it reduces it, step by step, and marks the pivot positions the reduced form puts on show. |

The two that solve something come first, and the arithmetic before the
elimination because the elimination is written in terms of it. Reading the form
of a matrix is a check somebody reaches for after one of those, so it sits at
the end.

The order is one tuple, `MODULES` in `gui/app.py`, and nothing else depends on
it: the rows are drawn by walking it, and the first row is the page that opens.

Gauss and Gauss-Jordan share one row because they share the walk — one stops at
the staircase and the other keeps going — so the choice is a setting of one
method, not a second program. Two rows opening what is almost the same page is
a duplicated menu, not a feature.

A program that has not been written has no row. A menu of things that do
nothing is a plan, and the plan lives in this repository, not in the window.

### Two ways to hand over a matrix

The pill at the top of the input card is the same choice `ui/prompts.py` offers
in the terminal, and it reads what was typed with the same two modules. Both
pages have it, and both get it from the same widget: `gui/entry.py`.

**Coeficientes** is a grid for A and a column for b, resized with their own
steppers. b follows A: one equation is one row of A and one entry of b, and they
cannot drift apart.

**Ecuaciones** is a box where the system is written the way it is on paper, one
equation per line:

```
a - 2b + c = 0
2b - 8c = 8
-4a + 5b + 9c = -9
```

`core/equations.py` reads them. Nobody says how many unknowns there are — they
are whatever the equations turn out to mention, and the list of them is read
back under the box (`Incógnitas encontradas (3): a, b, c`) before anything is
done with it. That echo is the point: `2x + 3x = 5` written where `2x + 3y = 5`
was meant shows up there, immediately, instead of as a system that classifies
wrong for no visible reason. The window earns it — the line only appears once
the equations have actually parsed, and disappears the moment one is edited.

Whatever the unknowns were called is what comes out. A system typed in `a`, `b`
and `c` is cleared, verified and printed in `a`, `b` and `c`; that name list is
what `ui/presentation.py` has taken as its `names` argument all along. The grid
route names nothing, so it falls back to `x`, `y`, `z`, `w`.

Everything the terminal parser accepts, this box accepts, because it is the
same parser: `2*x`, `2.5x`, `2,5x`, `(1/3)x`, unknowns on the right, constants
on the left, the same unknown twice, and `x2` sorting before `x10`. The table in
[usage.md](usage.md) is the full list.

What cannot be read is said in Spanish, naming the line — `A la ecuación 2 le
falta el '='`, `En la ecuación 1 no entiendo la parte '&'`. The terminal does
not need the number, because it has just asked for that one equation; the window
does, because all of them are on screen at once.

The two verdicts are all that card shows by default. The five numbered
properties, and the entry that breaks the ones that fail, are behind `Ver por
qué`: they are what somebody wants when the answer is no, and clutter when it is
not. A page that reduces a matrix has three cards of output already.

### What comes out

Press **Calcular** and the cards below the input answer the seven requirements
of Programa 1, in the order the assignment numbers them:

| Requirement | Where it is |
| --- | --- |
| 1. Entrada de datos | The input card. |
| 2. Matriz aumentada inicial | The first step of **Paso a paso** — `[ A \| b ]` before anything was done to it. |
| 3. Eliminación por filas | **Paso a paso**: every elementary operation, one at a time, with the matrix it produced. `Anterior` / `Siguiente` walk it and the dots jump straight to one. The labels are the ones `core/steps.py` records, in typographic notation: `f₃ → f₃ + 4 · f₁`. |
| 4. Sistema equivalente | **Sistema equivalente**: the matrix the walk ended on, read back as equations. |
| 5. Clasificación | **Resultado**: `rango(A)`, `rango(A\|b)`, the number of unknowns, which columns hold a pivot and which are free, and the classification in the words the assignment demands. |
| 6. Solución | **Resultado** carries the values; **Despeje por sustitución hacia atrás** carries the clearing, four lines per unknown, exactly as the terminal prints it. |
| 7. Comprobación | **Comprobación en el sistema original**: the values put back into the equations that were typed, never into the echelon ones. |

The last two cards only make sense for a system with one solution, so they only
appear for one. An indeterminate system shows which variables are free, an
inconsistent one names the row that reads `0 = k`, and both say in as many words
that there is nothing to substitute — requirement 7 has an answer even when
there is no answer to check.

Changing any number removes every card below the input. A result that was
computed from other numbers is not a result any more.

### What Gauss-Jordan shows instead

Everything above, minus the clearing, which the method does not need: in the
reduced form every pivot is alone in its column, so **Sistema equivalente**
already reads `x = 29`, `y = 16`, `z = 3` and there is nothing left to
substitute backwards. The card is not hidden silently — the result says the
values are read straight off the last column.

The classification and the values are the same either way. They come from
counting pivots and from an exact arithmetic, so the road taken cannot change
them; what changes is where the walk stops, which is what the step by step and
the equivalent system show.

When the system has infinitely many solutions, a **Solución general** card
writes the family out: every basic variable — the one holding a pivot — in terms
of the free ones, `x = -2 + z` and `y = 8 - 2*z` with `z es libre`. It is read
from the reduced form even when the method chosen was Gauss, because that is
where a pivot is alone in its column and the row is already the answer. The
family is the same either way, so reducing a second time behind the scenes
smuggles nothing in.

The pivot columns are named either way too — `columnas pivote: 1, 2` and
`columnas libres: 3` — because identifying them is what the second assignment
asks for, and because the free columns are exactly the free variables under
another name. Only the columns of A are counted: a pivot can also land on the
constants column, and that one is not a column of the system but the reason an
inconsistent system is inconsistent, which the classification already says.

### What it does not do yet

- Determinant, inverse and everything from Programa 3 onwards do not exist at
  all — not in the engine and, therefore, not in the sidebar either.

## How it is put together

```
gui/
├── theme.py       colours, fonts, the light/dark switch
├── widgets.py     the shapes CustomTkinter does not have
├── entry.py       the two ways a matrix is handed over, in one card
├── app.py         the window, the sidebar, and which page is open
├── __main__.py    python -m gui
└── pages/
    ├── operations.py   matrix arithmetic
    ├── echelon.py      the five properties, the reduction, the pivots
    └── gauss.py        A x = b, both methods
```

Two things both pages need live outside them, because the second page needing
one is what proves it was never page-specific: `SystemInput` in `entry.py` is
the input card with its pill, its grids and its text box, and `StepWalker` in
`widgets.py` is the step by step with its dots and its two links. Each was
written inside the elimination page first and moved out when the echelon page
asked for the same thing.

A page lands here when it works. There is no placeholder page, and adding one
would be the same mistake as a `Method` enum with a single member: weight that
has to be read and kept correct for no return.

Three rules hold the package together, and they are the same three that hold the
rest of the repository together.

**No arithmetic in `gui/`.** Every number on screen came out of `core/`. The
pages read matrices out of their cells, call `solve`, `to_rref`, `verify` or a
`Matrix` operator, and arrange what comes back. If a calculation ever appears in
this package it is in the wrong place.

**No wording in `gui/` that another front end also needs.** The five properties
of the echelon forms are the exception that proves it: only this window says
them, so `gui/pages/echelon.py` owns those sentences the way `ui/prompts.py`
owns its menu. The day the terminal needs them they move to
`ui/presentation.py`, which is where the classification went.
 The classification,
the values, the clearing and the verification are written by
`ui/presentation.py`, exactly as the terminal writes them. What the window does
own is its own chrome — `Calcular`, `Filas`, `Matriz A` — the same way
`ui/prompts.py` owns the wording of its menu.

**The window is handed in as one file, like everything else.** `build.py`
assembles `deliverables/out/Programa 2_Grupo5.py` out of `core/`,
`ui/presentation.py` and this package, with every docstring and comment in
Spanish, and its first lines tell whoever opens it to make a `.venv` and
`pip install customtkinter` — the only thing any deliverable of this repository
has ever needed installed, and only to draw. `requirements-gui.txt` says the
same thing for anyone working in the repository: nothing else here requires
anything.

The terminal program is still built too, as `Programa 1_Grupo5.py`, and it is
still standard library from end to end.

`ui/` is not the window's home, either. `ui/prompts.py` calls `input`, which
makes that package the terminal's. `ui/presentation.py` is shared by both
because it only builds strings.

### The layers inside it

`theme.py` holds every colour as a `(light, dark)` pair, which is what
CustomTkinter reads directly — the theme switch is one call and no widget is
rebuilt. Fonts cannot exist before a window does, so `load_fonts()` runs once the
application has started.

`widgets.py` has the pieces the toolkit does not: a card, a stepper, a matrix
you type into, a matrix drawn read-only, the brackets around both. It knows what
a matrix looks like and nothing about what one means.

`pages/` is one module per page. A page owns its widgets and its state and is
built the first time it is opened, so switching away and back finds what was
typed still there.

## Things that cost an afternoon

Written down because none of them are guessable.

**A `CTkFrame` one pixel wide draws nothing at all.** Not a thin line — nothing.
The bar between A and b, and the divider in the sidebar, are two pixels for that
reason and no other.

**A bar drawn per row sets the height of every row.** A `CTkFrame` defaults to
200x200, and gridding one into each row with `sticky="ns"` asks every row to be
200 pixels tall. The bar is one frame with `rowspan`.

**A header wider than the matrix stretches the matrix.** With the header spanning
the columns of the same grid, the extra width lands in the cell column and the
brackets stand away from the numbers. The header is packed above a separate body
frame instead.

**The brackets are drawn by hand,** on a canvas, which is the one thing here that
does not follow the theme by itself: a canvas holds a colour, not a pair of
them. `theme.on_change` exists for exactly that, and `Bracket` unsubscribes when
it is destroyed.

**`f_2` written `f₂` is one character shorter,** which is invisible until it
lands in a block `ui/presentation.py` has already lined up by counting
characters. The window puts the missing space back after the colon.

## The design

It follows a mockup made in Figma, close enough that the two are recognisably
the same program: the blue `#0071e3`, the rounded cards, the pill of choices,
the sidebar.

What was not taken from it is the mathematics. That mockup carries its own
implementation in TypeScript, with its own fraction type, and it is not as
careful as the engine here — `1/0` comes back as `1` from it rather than as an
error, and `2x` as `0`. The window calls `core/`, which is exact all the way
down and has `check.py` behind it.

What was dropped from it is the menu of programs that do not exist, and the
second elimination row: the mockup routes to a Gauss-Jordan page it never lists,
which is the same duplication seen from the other side.
