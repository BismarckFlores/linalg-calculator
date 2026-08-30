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

The engine reduces to the echelon form and clears the unknowns by back
substitution. It does not carry the elimination on to the reduced form, and it
has no way to pick between methods, because nothing has needed one yet.

That is the rule for this repository generally: a capability lands when an
assignment asks for it, not when it looks like it might be useful later. A
`Method` enum with a single member, or a second reduction nobody calls, is
weight that has to be read, tested and kept correct for no return.

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

## The engine raises in English

`core/` speaks no Spanish, not even when it fails. Its messages describe a
programming error ("Cannot multiply: A has 2 columns and B has 1 rows") and are
addressed to whoever is writing the code. When the mistake belongs to the person
using the program, the interface catches it and says so in Spanish before
calling the engine. That is why the interface checks dimensions the engine also
checks: two different audiences, not duplication.
