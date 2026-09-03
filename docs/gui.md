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

The sidebar lists what works, and nothing else. Two rows:

| Row | What it does |
| --- | --- |
| **Operaciones Matriciales** | `A + B`, `A − B`, `A × B`, `k · A`, `Aᵀ`. Each matrix is resized with its own steppers, and B follows A wherever the shapes have to agree. |
| **Eliminación Gaussiana** | Solves `A x = b`: the step by step, the classification, the clearing and the verification. Gauss or Gauss-Jordan is chosen inside the page. |

The arithmetic tab comes first deliberately. Everything else in the course is
written in terms of those five operations.

Gauss and Gauss-Jordan share one row because they share the walk — one stops at
the staircase and the other keeps going — so the choice is a setting of one
method, not a second program. Two rows opening what is almost the same page is
a duplicated menu, not a feature.

A program that has not been written has no row. A menu of things that do
nothing is a plan, and the plan lives in this repository, not in the window.

### Solving a system

Type A and b, press **Calcular**, and the cards below the input answer the seven
requirements of Programa 1, in the order the assignment numbers them:

| Requirement | Where it is |
| --- | --- |
| 1. Entrada de datos | The input card. |
| 2. Matriz aumentada inicial | The first step of **Paso a paso** — `[ A \| b ]` before anything was done to it. |
| 3. Eliminación por filas | **Paso a paso**: every elementary operation, one at a time, with the matrix it produced. `Anterior` / `Siguiente` walk it and the dots jump straight to one. The labels are the ones `core/steps.py` records, in typographic notation: `f₃ → f₃ + 4 · f₁`. |
| 4. Sistema equivalente | **Sistema equivalente**: the matrix the walk ended on, read back as equations. |
| 5. Clasificación | **Resultado**: `rango(A)`, `rango(A\|b)`, the number of unknowns, and the classification in the words the assignment demands. |
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

### What it does not do yet

- The equations cannot be typed as `2x + 3y - z = 5`. `core/equations.py` reads
  them and the terminal offers it; the window does not, yet.
- An indeterminate system reports its free variables and stops there. Writing
  the family out in terms of parameters needs `core/parametric.py`, which does
  not exist in any front end.
- Determinant, inverse and everything from Programa 3 onwards do not exist at
  all — not in the engine and, therefore, not in the sidebar either.

## How it is put together

```
gui/
├── theme.py       colours, fonts, the light/dark switch
├── widgets.py     the shapes CustomTkinter does not have
├── app.py         the window, the sidebar, and which page is open
├── __main__.py    python -m gui
└── pages/
    ├── operations.py   matrix arithmetic
    └── gauss.py        A x = b, both methods
```

A page lands here when it works. There is no placeholder page, and adding one
would be the same mistake as a `Method` enum with a single member: weight that
has to be read and kept correct for no return.

Three rules hold the package together, and they are the same three that hold the
rest of the repository together.

**No arithmetic in `gui/`.** Every number on screen came out of `core/`. The
pages read matrices out of their cells, call `solve`, `to_rref`, `verify` or a
`Matrix` operator, and arrange what comes back. If a calculation ever appears in
this package it is in the wrong place.

**No wording in `gui/` that another front end also needs.** The classification,
the values, the clearing and the verification are written by
`ui/presentation.py`, exactly as the terminal writes them. What the window does
own is its own chrome — `Calcular`, `Filas`, `Matriz A` — the same way
`ui/prompts.py` owns the wording of its menu.

**`gui/` is never built into the file handed in.** `build.py` does not know the
package exists. The course wants one self-contained script with no dependencies;
CustomTkinter is a dependency, so the window stays out of it. That is also why
`requirements-gui.txt` is named the way it is: nothing else in the repository
requires anything.

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
