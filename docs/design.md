# Design notes

Why the engine is split the way it is. The API lives in the docstrings; this
file holds the decisions that took thinking.

Add a section here when a module lands, not before.

## The record does not live inside the matrix

Three pieces, one job each:

| Piece | What it is |
| --- | --- |
| `Matrix` | A value. Row operations return a new matrix and say nothing about themselves. |
| `StepLog` | A record. The starting matrix and one `Step` per operation. |
| `Worksheet` | The blackboard: a matrix being worked on and the record of what was done to it. |

Keeping them apart means a matrix used for plain arithmetic carries no
bookkeeping, a matrix being reduced is not a different kind of object, and an
algorithm controls what gets written down instead of writing it down as a side
effect of operating. The reduction then reads like the blackboard it imitates:

```python
sheet = Worksheet(ab, "Gaussian elimination")
sheet.swap(1, 2)
sheet.scale(1, Fraction(1, 3))
sheet.add_scaled(2, 1, -4)
```

`sheet.log.snapshot(k)` returns the k-th link of the chain, which is literally
all a 'next' button needs.

## Operations that do nothing are not recorded

`Worksheet` silently drops `swap(i, i)`, `scale(i, 1)` and `add_scaled(i, j, 0)`.
They leave the matrix untouched, and in a step by step they are noise: someone
reading the trace would see a step where nothing happened.

`Matrix.scale_row(i, 0)` and `Matrix.add_scaled_row(i, i, k)` raise instead.
They are not elementary operations and they are not reversible, so asking for one
is a bug in the algorithm, not an operation that happens to be redundant.

## The matrix validates its own shape

`Matrix([[1, 2], [3]])` fails at construction. A ragged matrix that is accepted
does not fail where it was built; it fails much later, inside some unrelated
`elem`, with an `IndexError` that explains nothing.

## Exact numbers, all the way down

Every entry is a `Fraction`. Rounding never enters the calculation, so a third
prints as `1/3` and not as `0.3333333333333333`, the elimination is exact from
end to end, and a result can be checked against the same exercise done by hand.
The cost is that a decimal typed in becomes a fraction on the way out — `0.18`
comes back as `9/50` — which is the right trade for a course where the answers
are fractions.

## Only what has been asked for

The engine reduces to the echelon form, carries the elimination on to the
reduced form, and clears the unknowns by back substitution. It has no way to
pick between methods, though: a caller names the reduction it wants by calling
it, and no `Method` enum sits in between, because nothing has needed one yet.

That is the rule for this repository generally: a capability lands when an
assignment asks for it, not when it looks like it might be useful later. A
`Method` enum with a single member is weight that has to be read, tested and
kept correct for no return.

`to_rref` is the exception that proves it: the reduced form landed the day
Programa 2 asked for it, not the day `to_ref` made it look easy. It costs
almost nothing precisely because it was not designed for in advance — it is the
same walk with a second pass, so there was no abstraction waiting for it.

## Classification comes from the pivots, not from the answer

The system is classified before any value is computed, by counting pivots:

    rank(A) < rank(A|b)                 no solution
    rank(A) = rank(A|b) < unknowns      infinitely many
    rank(A) = rank(A|b) = unknowns      exactly one

`rank(A|b)` is how many pivots the reduction found; `rank(A)` is how many of them
landed on an unknown rather than on the constants column. A pivot on the
constants column *is* the row that reads `0 = k`, so the inconsistent case falls
out of the same count instead of needing a scan of its own.

Values are only computed in the unique case. The infinite case reports which
columns are free and stops there; writing the family out in terms of parameters
is a separate job.

## Verification does not trust the elimination

`verify` takes A, b and a list of values, and knows nothing about how those
values were found — not the method, not the log, not even that a `Solution`
exists. If it took the reduced form as its input it would be checking the
elimination against itself, and would agree with any bug that was consistent.

It compares both sides exactly, with no tolerance. That is affordable only
because nothing was ever rounded, and it is why every entry is a `Fraction`.

## The window is a front end, not a second program

`gui/` sits beside `core/` and `ui/`, imports both, and is imported by neither.
It draws matrices, reads them back, and calls `solve`, `to_rref`, `verify` and
the `Matrix` operators for everything else. Not one number on screen is computed
inside the package.

That is what the layering was for, and it is the first time it has been tested:
a window landed without a line of `core/` changing, and it says exactly what the
terminal says because both ask `ui/presentation.py` for the words.

It is deliberately outside `build.py`. The course wants one self-contained
script with no dependencies, and CustomTkinter is a dependency — so the file
handed in cannot contain the window, and the repository does not pretend
otherwise. `requirements-gui.txt` is named for the same reason: it is the
requirements of one package, not of the project.

`ui/` was not the place for it either. `ui/prompts.py` calls `input`, which
makes that package the terminal's; `ui/presentation.py` only builds strings,
which is why both front ends can share it.

## The handed-in file is built, never written

The course wants one self-contained `.py`. A project split into modules is what
is worth writing. `build.py` resolves that by assembling the file: it reads the
modules in dependency order, drops the imports between them (everything lands in
one namespace anyway), merges the standard-library imports into one block, and
puts a Spanish heading in front of each block explaining what it does.

The generated file is never edited — a change goes into the module and the file
is built again.

## The translation is keyed by text, and missing one stops the build

The handed-in file has to read in Spanish, comments and docstrings included,
while the repository stays in English. Keeping two copies of every module would
guarantee they drift, so instead `translations.py` holds the Spanish for each
docstring and comment, keyed by the exact English text, and `build.py` swaps one
for the other as it assembles.

Keying by text is what makes it safe. Edit an English docstring and its Spanish
is stale — the build then fails naming it, rather than quietly shipping the old
wording. Add a function and the build fails until its docstring is translated.
There is no path that ends with English in the file handed in.

Comments are found with `tokenize`, not by looking for a `#`, because a `#`
inside a string is not a comment. Docstrings are replaced from the bottom of the
file upwards, so changing the length of one cannot move the line numbers of the
ones not yet reached.

What stays in English is the text of the exceptions the engine raises. Those
describe programming mistakes and are addressed to whoever is writing the code;
a person using the program never sees one, because the interface catches what
they can get wrong and says it in Spanish first.

`build.py` compiles what it produced before writing it out, so a build that
succeeds cannot have shipped a syntax error.

## The engine raises in English

`core/` speaks no Spanish, not even when it fails. Its messages describe a
programming error ("Cannot multiply: A has 2 columns and B has 1 rows") and are
addressed to whoever is writing the code. When the mistake belongs to the person
using the program, the interface catches it and says so in Spanish before
calling the engine. That is why the interface checks dimensions the engine also
checks: two different audiences, not duplication.

## The parser raises one exception per kind of mistake

A typed equation is the first place where the mistake is genuinely the reader's,
so the wording matters and none of it can live in `core/`. `core/equations.py`
raises instead: `MissingEquals` when there is no `=` to split on, and
`UnreadableTerm` carrying the exact fragment that stopped it. Both descend from
`EquationError`, so `ui/prompts.py` can name the two it has a sentence for and
still catch anything added later without going silent.

The fragment is what makes the difference. "No pude leer esa ecuación" sends
somebody hunting through a line they already believe is correct; "No entiendo la
parte '&'" points at the character. That is worth an attribute on an exception.

The unknowns are read out of the equations rather than declared first. It is not
only shorter to type: the list that comes back is a proof of what was
understood. `Incógnitas encontradas (3): x, y, z` catches `2x + 3x = 5` written
where `2x + 3y = 5` was meant, at the moment it was typed, instead of three
sections later as a system that classifies wrong for no visible reason.
