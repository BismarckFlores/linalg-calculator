# Matrix inverse

The inverse page takes a square matrix of any positive order. Enter one row per
line and separate entries with spaces. Integers, decimal numbers and fractions
are accepted; the calculation keeps exact rational values. There is no fixed
dimension limit in this input. Available memory and the number of elimination
steps still limit how large a calculation can be in practice.

Gauss–Jordan reduces `[A | Iₙ]`. If the left block becomes `Iₙ`, the right
block is `A⁻¹`. The result is checked against the original input with both
`A A⁻¹ = Iₙ` and `A⁻¹ A = Iₙ`. If A is not square, has an unreadable entry, or
has fewer than n pivots, the page reports the reason in Spanish.

The **Ax = b** application takes the same A and a column b of n entries. Its
method is `x = A⁻¹b`, followed by an independent check that `Ax = b` using the
original A. This method applies only when A is invertible; a singular system
must be classified by elimination instead.

## Theorems and their conditions

- **Definition.** A square matrix A of order n is invertible if a square C of
  the same order satisfies both `AC = Iₙ` and `CA = Iₙ`. That C is `A⁻¹`.
- **Order two.** For `A = [[a,b],[c,d]]`, if `ad − bc ≠ 0`, then
  `A⁻¹ = (1/(ad − bc)) [[d,−b],[−c,a]]`. If `ad − bc = 0`, A is singular.
  This formula is specific to 2×2 matrices; the calculator uses Gauss–Jordan
  for every order.
- **Solving a system.** If A is invertible and has order n, then for every
  `b ∈ ℝⁿ`, `Ax = b` has exactly one solution, `x = A⁻¹b`.
- **Inverse of an inverse.** If A is invertible, then A⁻¹ is invertible and
  `(A⁻¹)⁻¹ = A`.
- **Product.** If A and B are invertible square matrices of the same order,
  then AB is invertible and `(AB)⁻¹ = B⁻¹A⁻¹`.
- **Transpose.** If A is invertible, then Aᵀ is invertible and
  `(Aᵀ)⁻¹ = (A⁻¹)ᵀ`.

For a square n×n matrix, the **invertible matrix theorem** says all of the
following statements are equivalent. They are either all true or all false:

| Letter | Equivalent statement |
| --- | --- |
| a | A is invertible. |
| b | A is row equivalent to `Iₙ`. |
| c | A has n pivot positions. |
| d | `Ax = 0` has only the trivial solution. |
| e | The columns of A are linearly independent. |
| f | `x ↦ Ax` is one-to-one. |
| g | `Ax = b` has a solution for every `b ∈ ℝⁿ`. |
| h | The columns of A span `ℝⁿ`. |
| i | `x ↦ Ax` maps `ℝⁿ` onto `ℝⁿ`. |
| j | Some n×n C satisfies `CA = Iₙ`. |
| k | Some n×n D satisfies `AD = Iₙ`. |
| l | Aᵀ is invertible. |

The square-matrix condition is essential. For a rectangular matrix, pivots and
solutions still matter, but these twelve statements are not an inverse theorem.

## Exercises from the course slides

1. **Compute an inverse.** For `A = [[3,4],[5,6]]`, `ad − bc = −2`, so
   `A⁻¹ = [[−3,2],[5/2,−3/2]]`. Check both products against `I₂`.
2. **Practice 2.2.** Enter `[[1,−2,−1],[−1,5,6],[5,−4,5]]`. It has rank 2,
   so no inverse exists. The left block of `[A | I₃]` cannot become `I₃`.
3. **Apply the inverse to a system.** With `A = [[3,4],[5,6]]` and
   `b = [3,7]ᵀ`, calculate `x = A⁻¹b = [5,−3]ᵀ` and verify `Ax = b`.
   A second preset uses `A = [[1,0,−2],[3,1,−2],[−5,−1,9]]` and
   `b = [3,7,−16]ᵀ`; it gives `x = [1,2,−1]ᵀ`.
4. **Use the invertible matrix theorem.** The matrix
   `[[2,3,4],[2,3,4],[2,3,4]]` has repeated rows, so it has fewer than three
   pivots. It is singular, its columns are dependent, and some `Ax = b` have no
   solution. For contrast, `[[1,0,−2],[3,1,−2],[−5,−1,9]]` has three pivots.

The source presentation is `Materiales de estudio/Inversa de una Matriz.pptx`.
Its formulas are used as mathematical reference; the calculator requirements
come from the user request.
