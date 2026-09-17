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
| **Vectores** | `u + v`, `u − v` and `k · u` in Rⁿ, as columns side by side and component by component, and whether b is a linear combination of v₁, …, vₖ, solved as the system it is. Nobody says what n is: it is however many components were typed. |
| **Operaciones Matriciales** | `A + B`, `A − B`, `A × B`, `k · A`, `Aᵀ`. Each matrix is resized with its own steppers, and B follows A wherever the shapes have to agree. |
| **Eliminación Gaussiana** | Solves `A x = b`: the step by step, the classification, the clearing and the verification. The system goes in as coefficients or as written equations, and Gauss or Gauss-Jordan is chosen inside the page. |
| **Formas Escalonadas** | Takes a matrix as it stands and answers the definition: is it in echelon form, is it in the reduced one. Then it reduces it, step by step, and marks the pivot positions the reduced form puts on show. Switched to `Es una matriz aumentada [ A \| b ]`, it also reads the pivots as a system. |
| **Sistemas Numéricos** | Converts a whole number from decimal to binary, octal, hexadecimal or any base from 2 to 36 by repeated division, and back to decimal by the linear combination of powers it stands for. Each direction is checked with the other. |

The order follows the course. Vectors come first, then the matrix pages — the
arithmetic before the elimination because the elimination is written in terms
of it, and reading the form of a matrix after both, as the check somebody
reaches for once one of them is done. The numeral systems have nothing to do
with matrices, so they sit apart, at the end.

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

One grid cannot say whether its last column is b, and a 3x5 augmented matrix
typed cell by cell reads as five unknowns instead of four. The switch under the
grid says it: the bar is drawn in every matrix of the page, the pivot columns
counted are only those of A, and the page reads the pivots as the existence
theorem does — a system has a solution exactly when the column of b holds no
pivot, and only one when every column of A holds one. Typed as equations the
matrix is augmented anyway, so the switch only exists for the grid.

The two verdicts are all that card shows by default. The five numbered
properties, and the entry that breaks the ones that fail, are behind `Ver por
qué`: they are what somebody wants when the answer is no, and clutter when it is
not. A page that reduces a matrix has three cards of output already.

### What comes out

Press **Calcular** and the cards below the input answer the seven requirements
of Programa 1, in the order the assignment numbers them:

| Requirement | Where it is |
| --- | --- |
| 1. Entrada de datos | The input card, and **Ecuación matricial A x = b** under it: A, the column of unknowns and b, in brackets side by side — the system as the single matrix equation it is. |
| 2. Matriz aumentada inicial | The first step of **Paso a paso** — `[ A \| b ]` before anything was done to it. |
| 3. Eliminación por filas | **Paso a paso**: every elementary operation, one at a time, with the matrix it produced. `Anterior` / `Siguiente` walk it, the dots jump straight to one, and `Ver todos los pasos` lays the whole walk out to be scrolled instead. The labels are the ones `core/steps.py` records, in typographic notation: `f₃ → f₃ + 4 · f₁`. |
| 4. Sistema equivalente | **Sistema equivalente**: the matrix the walk ended on, read back as equations. |
| 5. Clasificación | **Resultado**: `rango(A)`, `rango(A\|b)`, the number of unknowns, which columns hold a pivot and which are free, and the classification in the words the assignment demands. |
| 6. Solución | **Resultado** carries the values; **Despeje por sustitución hacia atrás** carries the clearing, four lines per unknown, exactly as the terminal prints it. |
| 7. Comprobación | **Comprobación en el sistema original**: first the product `A · x`, worked with the same matrix multiplication as **Operaciones Matriciales**, coming out as b; then the values put back into the equations that were typed, never into the echelon ones. |

The last two cards only make sense for a system with one solution, so they only
appear for one. An indeterminate system shows which variables are free, an
inconsistent one names the row that reads `0 = k`, and both say in as many words
that there is nothing to substitute — requirement 7 has an answer even when
there is no answer to check.

Somebody following the method wants one operation at a time; somebody checking
an answer wants to scroll past the lot. Neither is the right default for the
other, so the step by step does both and the choice is one click. Both pages
that walk an elimination get it, because both get it from the same widget.

Every fraction in the window is written the way one is written by hand, one
number over another with a rule between them — in the matrices, in the labels of
the steps, in the values of the solution, and inside the blocks of working: the
equivalent system, the clearing, the check and the general solution. A column of
`22/15` and `-17/15` is much harder to read slashed onto one line, and the
window has the room the terminal does not. The file handed in still prints the
plain form, because a transcript has one line per line.

The brackets that only a line of text needed are dropped where the stacked
fraction makes them unnecessary: `(1/2)y` is bracketed so that `1/2y` cannot be
read as one over two-y, and stacked it says where it ends by itself. They stay
wherever something is leaning on them — `3(-17/12)` would otherwise become
`3-17/12`.

A minus sign belongs to the whole fraction, so it stands to the left of the
stack and on the rule: `-1/4` is one number over another and then negated, which
is what it looks like that way and not when the sign is stacked with the
numerator.

A product is written by putting the two things next to each other, the way it
is written by hand: `2y`, not `2*y`; `1(29)`, not `1*(29)`. That is
`ui/presentation.py`, so the terminal and the file handed in read the same way.
The sign of a negative term comes out in front of it — `3x - 4(12)` rather than
`3x + (-4)(12)` — and closes up against the number when it opens the sum:
`-4(29) + 5(16)`.

Those blocks were lined up by counting characters, which stops being true the
moment a fraction takes two lines instead of one, so `MathBlock` lays them out
again in a grid. It is told which of the two alignments the text meant: a system
of equations is written with its left sides pushed right so the equals signs
fall under each other, and a clearing is written with its lines starting at the
same place. Both were true before, and both still are.

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

### Vectors

The dimension is never asked for. The assignment makes a point of it — n is not
known in advance — so a vector is typed as its components, `1, -2, 3` or
`(1 -2 3)`, and n is however many there turn out to be. Components are split on
commas, semicolons or spaces, which is why a decimal takes a point: `2,5` is two
components, and the `n = 2` badge on the result says so.

**u + v**, **u − v** and **k · u** show the operation twice. **Resultado** writes
it as columns side by side, `[u] + [v] = [u + v]`, with the result also in a
line, `u + v = (5, -2, 5/2)`. **Componente a componente** writes one line per
component, `u₃ + v₃ = 3 - 1/2 = 5/2`, with the sign of the second number folded
into the operation the way it is by hand: `3 + (-1/2)` is written `3 - 1/2`, and
`2 - (-3)` is written `2 + 3`. A scalar multiplies with the component in
brackets, `-3(-2)`, and a fractional scalar in brackets of its own,
`(1/2)(-4)`. Two vectors of different dimension are refused before anything is
added, naming both sizes.

**Combinación lineal** takes b and the vectors v₁, …, vₖ, one per line, and
answers in four cards:

| Card | What it shows |
| --- | --- |
| Planteamiento | The question as the vector equation `c₁[v₁] + c₂[v₂] = [b]`, wrapped every four vectors, and the same thing written out component by component as a system in c₁, …, cₖ. |
| Paso a paso | That system's augmented matrix, `[ v₁ v₂ \| b ]`, reduced with the same step walker as the elimination page. |
| Resultado | The ranks and the answer in colour: green for one way of combining them, orange for infinitely many, red for none. With one, the scalars and `b = 3v₁ + 2v₂`. With infinitely many, the general solution and an example with every free scalar at 0. With none, the row that reads `0 = k`. |
| Comprobación | The scalars put back: each vector scaled, the products added up column by column to b, and the same check component by component. With infinitely many it checks the example. |

It is the definition, solved the way the course solves everything: b is a
combination exactly when `[ v₁ … vₖ | b ]` is consistent, so `core/vectors.py`
asks `solve` and adds nothing of its own to the elimination.

### Numeral systems

The assignment asks for two directions, and the page has a pill for each.

**Decimal → otra base** takes a whole number and a base, and divides. Every
division is written as the equation it is, `43 = 2 · 21 + 1`, beside its
remainder and the digit that remainder becomes, so a remainder of 14 in base 16
is visibly an `E`. The digits are then read from the bottom up into the result.

The base is picked on a pill: binary, octal and hexadecimal by name, because
those are the ones the course asks for, and **Otra base**, which opens a
`b =` field beside the pill for any base from 2 to 36. Past 9 the digits are
letters, `A` for 10 up to `Z` for 35 — the alphabet running out is why 36 is
the top. The field is read with the same `from_base` the page is about, so not
even the base goes through `int`; anything that is not a whole number in range
is refused before converting. The note under the divisions names the letters
the chosen base uses, and says nothing about letters when it uses none.

**Otra base → decimal** takes a numeral and the base it is written in — the
same pill, custom field included — and
writes out the linear combination it stands for — the requirement the
assignment names — in three stages worked down to one number:

```
2B₁₆ = 2·16¹ + 11·16⁰
     = 2·16 + 11·1
     = 32 + 11
     = 43
```

with a letter's value named beside it, and the same thing again as a table of
positions, powers and contributions. A long binary numeral breaks its sum into
lines of six terms.

The first direction checks itself with the second: the result is read back as a
combination right under the divisions, and has to come to the number the
divisions started from. The divisions are not trusted with their own answer.

Neither direction borrows from Python: no `int(text, base)`, no `bin`, `oct` or
`hex`. The procedure is the point, so the procedure is what runs, in
`core/bases.py`. Whole numbers are converted, up to 32 digits; a decimal point,
a sign anywhere but the front, or a digit the base does not have is named back
in Spanish with the digits that base does use (`En base 20 se usan las cifras
del 0 al 9 y las letras de la A a la J.`). Spaces are ignored, so a binary
number can be typed in groups of four.

Negative numbers are converted the way they are by hand, in every base: the
sign stays apart from the digits. Towards a base, the divisions are those of
the absolute value — a note says `|-43| = 43` — and the digits read back come
out as `-( 1 0 1 0 1 1 )  →  -101011₂`. Back to decimal, each stage of the
combination is wrapped in the sign, so it is seen to apply to the whole sum and
not to its first term:

```
-2B₁₆ = -(2·16¹ + 11·16⁰)
      = -(2·16 + 11·1)
      = -(32 + 11)
      = -43
```

and the table of positions adds up the digits, `Suma = 43`, then applies the
sign, `Con el signo: -43`. A leading `+` is accepted and changes nothing, and
`-0` is `0`. The sign never counts towards the 32 digits, because it is not one.
Two's complement — `-43` as `11010101` in 8 bits — is a different notation, tied
to binary and to a fixed width, and is not what this page does.

The assignment reads "binario, octal o decimal a su equivalente número
decimal"; converting decimal to decimal says nothing, so the page offers
hexadecimal there, the base the other direction converts into, along with any
other base through the custom field.

The example in the number box is always 43, written in whichever base is
showing — `101011`, `53`, `2B`, or `133` for base 5 — and follows the custom
field as it is typed, until somebody types a number of their own.

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
    ├── vectors.py      Rⁿ: operations and linear combinations
    ├── operations.py   matrix arithmetic
    ├── gauss.py        A x = b, both methods
    ├── echelon.py      the five properties, the reduction, the pivots
    └── bases.py        whole numbers between base 10 and bases 2 to 36
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

**The wheel arrives at the window, not at the page under the pointer.**
CustomTkinter binds it application-wide and then walks up from the widget the
pointer is over, which means anything outside the scrolling area — the sidebar,
a text box — swallows the notch. It also moves thirty pixels at a time on Linux,
so a long page took forty notches. `Application._wire_wheel` replaces that
binding with one that answers from anywhere and moves three lines, and steps
aside only for a text box with scrolling of its own to do.

**Two modules that each define the same global are fine until they are one
file.** `gui/pages/gauss.py` and `gui/pages/bases.py` both had a `SUBTITLES`.
In the repository that is two names in two namespaces; assembled, the second
replaced the first and the elimination page would have raised `KeyError` the
moment it opened. `build.py` now refuses to assemble a program where two blocks
define the same name, and says which two. It caught the next one on its own:
the custom base brought an `EXAMPLE` that `gui/pages/echelon.py` already had.

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
