# Using it

Everything runs from the repository root, with no installation and no
dependencies. Python 3.12 or newer.

```bash
python -m deliverables.program1     # solve systems, interactively
python check.py                     # confirm the engine still works
python build.py                     # write the file that gets handed in
```

## Solving a system

`python -m deliverables.program1` offers two ways to hand it a system, and then
walks the whole solution in seven sections.

```
  1) Escribir las ecuaciones tal como se leen
  2) Dar los coeficientes uno por uno
```

### Typing the equations

The first way takes the system as it is written on paper, one equation per
line, ending on a blank line:

```
  Ecuación 1: x - 2y + z = 0
  Ecuación 2: 2y - 8z = 8
  Ecuación 3: -4x + 5y + 9z = -9
  Ecuación 4:

Incógnitas encontradas (3): x, y, z
```

Nobody says how many unknowns there are: they are whatever the equations turn
out to mention, sorted into column order, and read back so a typo shows up as
a wrong matrix rather than as a wrong answer three sections later. The names
are the ones that were typed, so a system written in `a` and `b` is solved and
printed in `a` and `b`.

What the parser accepts:

| Written | Read as |
| --- | --- |
| `2x + 3y - z = 5` | the plain case, spaces optional |
| `x + y = 2` | a missing coefficient is 1 |
| `2*x + 3*y = 1` | `*` is allowed between number and unknown |
| `2.5x`, `2,5x`, `1/3x`, `(1/3)x` | integers, decimals and fractions |
| `2x = 3y + 1` | unknowns on the right move left |
| `2x + 3 = 5` | constants on the left move right |
| `x + x = 4` | the same unknown twice adds up |
| `x1`, `x_2`, `X` | names are letters, digits and `_`, and case is ignored |

`1/3x` is read as `(1/3)x`, never as `1/(3x)`.

### Giving the coefficients one at a time

The second way asks for the size first and then every number by name, which is
the order the assignment sheet asks for:

```
Número de ecuaciones (m): 3
Número de variables (n): 3

Ahora los 12 coeficientes, ecuación por ecuación.
Se admiten enteros, decimales (2.5 o 2,5) y fracciones (1/3).

Ecuación 1:
  a_11 = 1
  a_12 = -2
  a_13 = 1
  b_1  = 0
```

`a_ij` is the coefficient in equation `i` of variable `j`; `b_i` is what
equation `i` equals. Nothing here names the unknowns, so they come out as the
blackboard default: `x`, `y`, `z`, `w`, then `x5` upwards.

Either way the numbers are kept exactly as written — a third stays a third all
the way to the answer.

### When something cannot be read

Nothing a person types ends the program. The same question comes back, saying
what it could not make sense of:

```
  a_11 = uno
  'uno' no es un número. Prueba con 3, -2.5 o 1/3.

  Ecuación 1: 2x + 3y
  Falta el '='. Una ecuación se escribe como  2x + 3y = 5

  Ecuación 1: 2x + & = 3
  No entiendo la parte '&'. Revísala.
```

The size is capped at 10 equations and 10 unknowns. That is not a limit of the
method; it is there so a typo of `100` does not turn into ten thousand
questions in the middle of a demonstration.

### The seven sections

Each one answers a requirement of the assignment, in the same order.

| Section | What it shows |
| --- | --- |
| 1. Entrada de datos | The questions above |
| 2. Matriz aumentada inicial | `[A \| b]` as it was typed |
| 3. Eliminación por filas | Every elementary operation, with the matrix after it |
| 4. Sistema equivalente | The echelon matrix read back as equations |
| 5. Clasificación del sistema | The two ranks, and which of the three kinds it is |
| 6. Solución | The clearing and the values, or the free variables |
| 7. Comprobación | The values substituted into the original system |

Between sections the program waits for Enter, so nothing scrolls away before it
has been read. That only happens when a person is watching: with the input
redirected — a pipe, a file, a test — it runs straight through.

At the end it offers another system, which is how three cases fit in one
session and one screenshot each.

### Stopping

`n` at the closing question leaves normally. Ctrl+C or Ctrl+D leaves at any
point, without a traceback.

## Checking the engine

`python check.py` runs the engine end to end and prints one line per claim:

```
  ok   A + B: [  6   8 ] / [ 10  12 ]
  ok   pivots: ((1, 1), (2, 2), (3, 3))
  ok   unique: SystemKind.UNIQUE
  ok   3x = 1: (1/3)

Everything above says ok: the engine is wired correctly.
```

It stops at the first line that is wrong, printing what it got and what it
expected. Run it after touching anything in `core/`.

## Building the file to hand in

`python build.py` assembles the modules into one self-contained script under
`deliverables/out/`, translating every docstring and comment into Spanish on
the way:

```
Escrito: deliverables/out/Programa 1_Grupo5.py
  1465 lineas, 11 bloques, sin dependencias
  Todo el texto del archivo esta en castellano.
```

Two settings at the top of `build.py` control the result:

```python
GROUP_NUMBER = "5"      # becomes the file name and the header
PROGRAM_NUMBER = 1
```

The output directory is ignored by git. The generated file is a build artefact,
not source: **never edit it**. A change belongs in the module it came from,
followed by another build.

### When the build refuses

```
No se puede construir: falta traducir esto en translations.py

  Rows become columns.
```

A docstring or comment has no Spanish. Add it to `translations.py`, keyed by
the exact English text, and build again. This happens on purpose whenever a
function is added or an English docstring is edited — it is the mechanism that
keeps English out of the file handed in.

## Handing it in

1. Set `GROUP_NUMBER` in `build.py`.
2. `python build.py`.
3. Run the generated file and screenshot three cases: one with a unique
   solution, one with infinitely many, one with none. The systems in
   `docs/how-it-works.md` produce one of each.
4. Put the screenshots and the official cover page in the submission document.
   The cover is a separate document, which is why `build.py` does not know the
   names of the members or the teacher.
