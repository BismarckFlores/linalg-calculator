# How it works

One system solved from beginning to end, with the module doing the work named
at each stage. Everything below is real output, not a sketch of it.

The system:

```
 x - 2y +  z =  0
     2y - 8z =  8
-4x + 5y + 9z = -9
```

## 1. It becomes a matrix

Writing the coefficients down and dropping the names of the unknowns loses
nothing: the position of a number already says which variable it belongs to.
The constants go in a last column, separated by a bar.

```
  [  1  -2   1 |  0 ]
  [  0   2  -8 |  8 ]
  [ -4   5   9 | -9 ]
```

That is `[A | b]`, the augmented matrix, and it is a single `Matrix` — the bar
is drawn by `ui/presentation.py`, which knows the last column means something
different. `core/matrix.py` just holds a rectangle of numbers.

Every entry is a `Fraction`, from `core/scalar.py`. Nothing is ever rounded, so
a coefficient of `1/3` stays `1/3` and the answer can be checked against the
same exercise done by hand.

## 2. Rows are combined until a staircase appears

Three operations do not change which values solve the system:

- swapping two equations, `f_i <-> f_j`
- multiplying an equation by a number that is not zero, `f_i -> k*f_i`
- adding a multiple of one equation to another, `f_i -> f_i + k*f_j`

`core/elimination.py` applies them in a fixed order: find a pivot in the first
column, scale it to 1, and use it to make zeros below. Then the same in the
next column, one row further down.

```
Paso 1:  f_3 -> f_3 + 4*f_1
  [  1  -2   1 |  0 ]
  [  0   2  -8 |  8 ]
  [  0  -3  13 | -9 ]

Paso 2:  f_2 -> (1/2)*f_2
  [  1  -2   1 |  0 ]
  [  0   1  -4 |  4 ]
  [  0  -3  13 | -9 ]

Paso 3:  f_3 -> f_3 + 3*f_2
  [  1  -2   1 | 0 ]
  [  0   1  -4 | 4 ]
  [  0   0   1 | 3 ]
```

Three operations, three matrices. Nobody had to remember to write them down:
the elimination runs on a `Worksheet` (`core/worksheet.py`), where an operation
happening and an operation being recorded are the same act. The record is a
`StepLog` (`core/steps.py`), and `snapshot(k)` gives the matrix after `k`
operations — which is all a 'previous / next' button ever needs.

The last matrix is in **row echelon form**: each row starts with more zeros
than the one above, and the first non-zero entry of a row — its **pivot** — is
1.

## 3. The staircase is read back as equations

```
  f_1:  x - 2*y + z = 0
  f_2:      y - 4*z = 4
  f_3:            z = 3
```

Same solutions as the system at the top, but now the last equation has one
unknown, the one above it has two, and so on. That shape is the whole point of
the elimination.

## 4. Counting pivots classifies the system

Two numbers decide everything, and neither needs the solution:

- **rank(A|b)** — how many pivots the elimination found. Here, 3.
- **rank(A)** — how many of those pivots landed on a variable rather than on
  the constants column. Here, also 3.

Rouché–Frobenius, in `core/systems.py`:

| Condition | Kind |
| --- | --- |
| `rank(A) < rank(A\|b)` | Sistema Inconsistente: no solution |
| `rank(A) = rank(A\|b) < unknowns` | Sistema Consistente Indeterminado: infinitely many |
| `rank(A) = rank(A\|b) = unknowns` | Sistema Consistente Determinado: exactly one |

A pivot landing on the constants column *is* a row reading `0 = k` with `k`
not zero — an equation nothing can satisfy. That is why the inconsistent case
falls out of counting rather than needing a search of its own.

Here `3 = 3 = 3`: one solution.

## 5. The unknowns are cleared from the bottom up

The last equation gives a value straight away. Substituting it into the one
above gives the next, and so on. `core/systems.py` keeps every line of it:

```
  f_3:  z = 3

  f_2:  y - 4*z = 4
        y - 4*3 = 4
        y = 4 + 4*3
        y = 16

  f_1:  x - 2*y + z = 0
        x - 2*16 + 3 = 0
        x = 0 + 2*16 - 3
        x = 29
```

Four lines per unknown: the equation, the values put in, the constant cleared,
the result. It is the same work done on paper, written the same way.

## 6. The answer is put back where it came from

Solving is one thing; showing the answer holds is another. `core/verification.py`
takes the values and evaluates every equation of the **original** system —
never the echelon one:

```
  Ecuación 1:  1*(29) + (-2)*(16) + 1*(3) = 0
               0 = 0   correcto
  Ecuación 2:  0*(29) + 2*(16) + (-8)*(3) = 8
               8 = 8   correcto
  Ecuación 3:  (-4)*(29) + 5*(16) + 9*(3) = -9
               -9 = -9   correcto

Todas las ecuaciones se cumplen: la solución es correcta.
```

Checking against the reduced matrix would be checking the elimination against
itself, and would agree with any bug that was consistent. Checking against what
was typed in does not. The comparison is exact, with no tolerance, which is
affordable only because nothing was ever rounded.

## The other two endings

**Infinitely many.** `x + y + z = 3` together with `2x + 2y + 2z = 6` is the
same equation twice. The elimination flattens the second row to zeros:

```
rango(A) = 1
rango(A|b) = 1
número de incógnitas = 3

Sistema Consistente Indeterminado: Presenta Infinitas Soluciones.

El sistema tiene 3 incógnitas y 1 pivote, así que quedan 2 variables libres: y, z
```

One pivot for three unknowns. The two without a pivot are free: fix them at any
values and the first equation gives the third. There is nothing to verify,
because there is no single answer to put back.

**None.** `x + y = 5` together with `x + y = 8` cannot both hold:

```
  f_1:  x + y = 5
  f_2:      0 = 1

rango(A) = 1
rango(A|b) = 2

Sistema Inconsistente: Sin Solución.

La fila f_2 quedó como  0 = 1, que ningún valor de las
incógnitas puede cumplir.
```

The second rank is larger than the first: a pivot fell on the constants column.
The program names the row rather than saying one exists somewhere.

## Where each piece lives

| Stage | Module |
| --- | --- |
| Exact numbers | `core/scalar.py` |
| The matrix and its row operations | `core/matrix.py` |
| Recording the steps | `core/steps.py`, `core/worksheet.py` |
| The elimination | `core/elimination.py` |
| Classifying and clearing | `core/systems.py` |
| Putting the answer back | `core/verification.py` |
| Reading a written equation | `core/equations.py` |
| Every word on screen | `ui/presentation.py` |
| Reading the keyboard | `ui/prompts.py` |
| Ordering the seven sections | `deliverables/program1.py` |

Not one of the `core/` modules prints anything or contains a word of Spanish.
They return data; the interface decides how to say it. That is why the same
engine could drive a window without a line of it changing, and why the wording
of the classification exists in exactly one place.

`docs/design.md` covers why the pieces are split where they are.
