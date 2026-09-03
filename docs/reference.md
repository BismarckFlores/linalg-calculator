# Code reference

What every module exposes, so you can work with a piece without reading it.
Signatures are taken from the source; the docstrings hold the detail this file
leaves out.

## The shape of it

Each layer only knows about the ones above it. Nothing points back down.

```
scalar        exact numbers
   │
matrix        a rectangle of them, and row operations that return new matrices
   │
steps         a record: the starting matrix, and one Step per operation
   │
worksheet     matrix + record, where an operation happens and is written down
   │
elimination   drives a worksheet down to the echelon form, reduced or not
   │
systems       classifies what came out, and clears the unknowns
   │                                      verification   checks it independently
   ├──────────────────────────────────────────┘
presentation  turns all of the above into Spanish
prompts       reads a system from the keyboard
   │
program1      orders the seven sections
```

`verification` hangs off to the side deliberately: it imports `matrix` and
`scalar` only, so it cannot accidentally check the elimination against itself.

## What flows through it

```
keyboard ──prompts.ask_system()──> Matrix [A | b]
                                      │
                                      └──systems.solve()──> Solution
                                                              ├─ .log          → presentation.render_steps
                                                              ├─ .result       → presentation.render_equations
                                                              ├─ .kind         → presentation.describe
                                                              ├─ .values       → presentation.render_values
                                                              ├─ .substitutions→ presentation.render_substitutions
                                                              └─ .coefficients, .constants, .values
                                                                        └─verification.verify()─> Verification
                                                                                                     → presentation.render_verification
```

One call to `solve` produces everything the seven sections need. Nothing is
computed twice.

---

## `core/scalar.py`

The number every matrix entry is stored as.

| Name | Meaning |
| --- | --- |
| `Scalar` | `Fraction`. What an entry always is once inside a matrix. |
| `NumberLike` | `int \| float \| Fraction \| str`. What is accepted at the door. |
| `to_scalar(value) -> Scalar` | Normalizes anything readable. Accepts `"2,5"` and `"1/3"`. Raises `ValueError` on text that is not a number, `TypeError` on a bool. |
| `format_scalar(value) -> str` | `3`, `-4`, `1/3`. |
| `format_factor(value) -> str` | The same, parenthesized when negative or fractional: `(-1)`, `(1/3)`, but `5`. For step labels. |

## `core/matrix.py`

A rectangle of exact numbers. Indices count from 1 in `elem`, `row`, `column`
and every row operation; `Matrix.data` underneath is a plain 0-based list of
lists.

Construction raises `ValueError` if the rows are not all the same length.

**Reading**

| Method | Returns |
| --- | --- |
| `elem(i, j)` | The entry `a_ij`. |
| `row(i)`, `column(j)` | That row or column as a list. |
| `diagonal()` | The main diagonal, as far as it reaches. |
| `size()` | `(rows, cols)`. Also available as `.rows` and `.cols`. |
| `is_square()`, `is_zero_row(i)` | Predicates. |

**Shape**

| Method | Returns |
| --- | --- |
| `transpose()` | Rows become columns. |
| `augment(other)` | `[A \| B]`. Raises if the row counts differ. |
| `take_columns(first, last)` | A slice of columns, both ends included. |

**Elementary row operations** — each returns a *new* matrix and records
nothing. Use `Worksheet` when the step has to be kept.

| Method | Operation |
| --- | --- |
| `swap_rows(i, j)` | `f_i <-> f_j` |
| `scale_row(i, k)` | `f_i -> k*f_i`. Raises if `k` is zero. |
| `add_scaled_row(i, j, k)` | `f_i -> f_i + k*f_j`. Raises if `i == j`. |

**Arithmetic** — through the operators: `A + B`, `A - B`, `A * B`, `k * A`,
`A * k`, `-A`, `A == B`. Mismatched shapes raise `ValueError` naming both. The
scalar factor may be text, so `A * "1/2"` works.

**Building** — `Matrix.zero(rows, cols)`, `Matrix.identity(n)`,
`Matrix.column_vector(values)`.

**Printing** — `str(m)` is the blackboard form, aligned on the widest entry;
`repr(m)` is valid Python that rebuilds it. A list of matrices printed directly
shows the reprs.

## `core/steps.py`

The record of what was done.

| Name | Meaning |
| --- | --- |
| `label_swap(i, j)` | `"f_1 <-> f_2"` |
| `label_scale(i, k)` | `"f_2 -> (1/3)*f_2"` |
| `label_add_scaled(i, j, k)` | `"f_2 -> f_2 + 3*f_1"`, dropping the factor when it is 1 or -1. |

**`Step`** — frozen. Fields `before`, `label`, `after`, `note`. `render()`
draws it as `before --[ label ]-> after`.

**`StepLog`** — built on a starting matrix.

| Member | Meaning |
| --- | --- |
| `snapshot(k)` | The matrix after `k` operations; `snapshot(0)` is the initial one. The whole of a 'previous / next' control. |
| `result` | Where the chain ends. |
| `record(before, label, after)` | Appends. Normally called by `Worksheet`, not directly. |
| `annotate(text)` | Attaches a note to the step just recorded. |
| `is_empty()`, `len(log)`, `log[i]`, iteration | The steps themselves. |
| `summary()`, `render()`, `str(log)` | Developer views, in English. |

## `core/worksheet.py`

A matrix being worked on, plus its record. `sheet.matrix` is where the work
stands; `sheet.log` is how it got there.

| Method | Operation |
| --- | --- |
| `swap(i, j)` | `f_i <-> f_j`, skipped when `i == j`. |
| `scale(i, k)` | `f_i -> k*f_i`, skipped when `k` is 1. |
| `add_scaled(i, j, k)` | `f_i -> f_i + k*f_j`, skipped when `k` is 0. |

"Skipped" means the matrix is unchanged and nothing is written down: an
operation that does nothing would be noise in the step by step.

## `core/elimination.py`

| Name | Meaning |
| --- | --- |
| `to_ref(matrix, title="") -> Elimination` | Reduces to row echelon form, recording every operation. |
| `rank(matrix) -> int` | How many pivots that form has. |

**`Elimination`** — frozen. Fields `original`, `result`, `log`, `pivots`
(a tuple of `(row, col)`, 1-based, ordered by row) and `reduced`, which says
which of the two forms `result` is in.

| `to_rref(matrix, title="") -> Elimination` | Keeps going to the reduced form: Gauss-Jordan. |
| Member | Meaning |
| --- | --- |
`to_rref` is `to_ref` plus a second pass, not a second algorithm: the walk down
finds the pivots and normalizes them, the walk back up clears the entries above
each one, rightmost pivot first. Going back up never moves a pivot.

| `rank` | Number of pivots. |
| `pivot_columns()` | The columns holding one. |
| `free_columns()` | The columns without one. |
| `zero_rows()` | Rows that ended up entirely zero. |

After `to_ref`, every pivot is exactly 1 and everything below it is 0.

## `core/systems.py`

| Name | Meaning |
| --- | --- |
After `to_rref`, everything above it is 0 as well, so a pivot is the only
non-zero entry in its column.
| `solve(augmented) -> Solution` | The whole thing. Raises `ValueError` if the matrix has fewer than one equation or two columns. |
| `SystemKind` | `UNIQUE`, `INFINITE`, `INCONSISTENT`. |

**`BackSubstitution`** — frozen. One unknown cleared: `column`, `row`,
`constant`, `terms` (the `(coefficient, column)` pairs that had to be replaced),
`value`.

**`Solution`** — frozen. Everything the seven sections read.

| Member | Meaning |
| --- | --- |
| `kind` | Which of the three. |
| `unknowns` | How many variables the system has. |
| `values` | The value of each unknown, in order. **Empty unless `kind` is `UNIQUE`.** |
| `free_columns` | The variables with no pivot. Empty unless `kind` is `INFINITE`. |
| `substitutions` | The clearing, last unknown first. Empty unless `kind` is `UNIQUE`. |
| `homogeneous` | Whether every constant is zero. |
| `log` | The step by step of the elimination. |
| `augmented`, `result` | `[A \| b]` as given, and the echelon form. |
| `coefficients`, `constants` | `A` and `b` pulled back apart, for verifying. |
| `rank`, `coefficient_rank` | `rank(A\|b)` and `rank(A)`. Comparing them is the classification. |
| `reduction` | The `Elimination` underneath, if the pivots are needed. |

## `core/verification.py`

| Name | Meaning |
| --- | --- |
| `verify(coefficients, constants, values) -> Verification` | Evaluates `A x = b` row by row. Raises `ValueError` if `b` is not one column, if the row counts differ, or if the number of values does not match the unknowns. |

**`RowCheck`** — frozen. One equation: `row`, `terms` as
`(coefficient, value, column)`, `left`, `right`, and `holds`.

**`Verification`** — frozen. `checks`, `holds` (all of them), `failures()`.

Knows nothing about `systems` or `elimination` on purpose.

## `ui/presentation.py`

The only module that writes Spanish. Every function returns a string and prints
nothing.

| Function | Produces |
| --- | --- |
| `unknown_name(col)` | `x`, `y`, `z`, `w`, then `x5` and up. |
| `render_augmented(matrix, unknowns)` | `[  1  -2   1 \|  0 ]`, with the bar. |
| `render_steps(log, unknowns)` | Every operation, numbered, with the matrix after it. |
| `describe(solution)` | The classification, in the assignment's exact words. |
| `render_values(solution)` | The values, or the free variables, or the contradictory row — whichever applies to the kind. |
| `render_equations(solution)` | The echelon form read back as equations. |
| `render_substitutions(solution)` | The clearing, four lines per unknown. |
| `render_verification(verification)` | Each equation substituted, and the verdict. |

`CLASSIFICATIONS` is the dict holding the three required sentences. Change the
wording there and it changes everywhere.

## `ui/prompts.py`

The only module that calls `input`. A bad answer re-asks; nothing a person
types can end the program. End of input travels up to the caller.

| Function | Asks for |
| --- | --- |
| `ask_int(question, minimum=1, maximum=10)` | A whole number in range. |
| `ask_scalar(question)` | One number: integer, decimal or fraction. |
| `ask_yes_no(question)` | `s` or `n`. |
| `ask_system()` | `m`, `n`, and every coefficient by name. Returns `[A \| b]`. |
| `pause(message)` | Enter — but only when `stdin` is a terminal. |

`SIZE_LIMIT = 10` caps `m` and `n`.

## `deliverables/program1.py`

The script. Calculates nothing and words nothing beyond its headings.

| Function | Does |
| --- | --- |
| `banner(text, wait=True)` | A section heading, pausing first unless told not to. |
| `solve_one_system()` | The seven sections, once. |
| `main()` | The header, the loop, and a clean exit on Ctrl+C or Ctrl+D. |

## Outside the packages

| File | Does |
| --- | --- |
| `check.py` | Runs the engine end to end and prints one line per claim. Run it after touching `core/`. |
| `build.py` | Assembles the handed-in file. `BLOCKS` lists the modules in order with their Spanish headings; `GROUP_NUMBER` and `PROGRAM_NUMBER` name the output. |
| `translations.py` | `DOCSTRINGS` and `COMMENTS`, keyed by the exact English text. A missing entry stops the build. |

## Conventions worth knowing before changing anything

**Indices count from 1** everywhere a mathematician would count from 1: `elem`,
`row`, `column`, the row operations, `pivots`, `free_columns`, `RowCheck.row`.
`Matrix.data` is the exception and is 0-based, because it is a plain list.

**Values are frozen.** Every dataclass is `frozen=True` and `Matrix` operations
return new matrices. Nothing mutates under you.

**`core/` never speaks.** No `print`, no Spanish, not even in its exceptions —
those describe programming mistakes and are addressed to whoever is writing the
code. What a person can get wrong is caught in `ui/` and said in Spanish there.

**Empty is meaningful.** `Solution.values` is empty for anything but a unique
solution, and `free_columns` is empty for anything but an indeterminate one.
Check `kind` before reading either.
