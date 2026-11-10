# Bisection

Run `python -m gui` and open **Métodos Numéricos > Método de Bisección**.
The assignment is to solve an equation by bisection, with efficiency, code
presentation, an oral defence and aesthetics assessed. The page uses the
existing application, cards, fonts, light/dark palette and result-clearing
behaviour. It adds no dependencies.

## Inputs and stopping rules

The page starts with the function field, **Cargar ejemplo** and **Graficar función**.
Examples are available before any graph is drawn. Choosing one fills its
function and bisection parameters and immediately draws its preview, revealing
the controls without calculating a root. Graphing
requires no bisection endpoints and initially displays x in [-10, 10]. Only
after the graph is created are the bisection controls shown below it. Editing
the function closes its expanded graph and hides both graph and controls
until it is graphed again. Invalid expressions remain in the first stage.
Changing bisection parameters preserves the preview but invalidates the answer
and its markers. Graphing is visual inspection, not an analytic continuity
certificate; the proposed continuity-analysis action was withdrawn.

Enter the left side of `f(x) = 0`, the initial interval `[a, b]`, tolerance E
and an iteration limit from 1 to 1000 (default 100). Multiplication can be
implicit: `5x^3`, `(1/2)x`, `2(x+1)`, `(x+1)(x-1)` and `2sin(x)` are accepted.
Explicit `*` remains valid. Both `^` and `**` mean exponentiation. Supported elementary
functions are `sin`, `cos`, `tan`, `exp`, `ln`, `log` (natural logarithm),
`log10`, `sqrt` and `abs`, each with one argument; constants are `pi` and `e`.
Function literals use a decimal point. The existing scalar reader accepts
fractions and decimal commas in a, b and E.

Function calls require parentheses, such as `sin(x)`. Complete names stay
intact: write `pi x` or `pi*x`, rather than `pix`. Scientific notation such as
`1e-3x` means `0.001*x`. Implicit products have the same precedence as `*`:
`1/2x` means `(1/2)*x`; use `1/(2x)` for a product in the denominator.

The three supplied sources use different measures. They are selectable rather
than silently treated as interchangeable:

| Choice | Test | Interpretation |
| --- | --- | --- |
| Ancho del intervalo (default) | `b - a < E` | The rule stated in slide 3 of MÉTODOS NUMERICOS. Units of x. |
| Residuo | `abs(f(c)) < E` | The `error` column in Bisección.xlsx. Units of f(x). |
| Error relativo (%) | `abs((c - previous_c) / c) * 100 < E` | Approximate change between estimates. E = 1 means 1%, not 0.01%. |

Every comparison is strict. An evaluation of zero also stops. Relative error
is unavailable in the first iteration, at c = 0 or when the percentage cannot
be represented; it is displayed as a dash and cannot satisfy that criterion.
An iteration limit or an interval that can no longer be split before meeting
the chosen tolerance is reported as an unsuccessful stop, not convergence.
A zero relative change caused by an unsplittable interval cannot satisfy the
relative criterion. No intermediate results are rounded.

The method needs continuity over the entire interval and opposite endpoint
signs, unless an endpoint already evaluates to zero. Same-sign endpoints are
rejected; they do not establish that the equation has no roots. A finite
sample cannot establish continuity. A function such as `1/x` can change signs
without having a root. Undefined evaluations encountered during bisection are
errors; undefined plot samples leave gaps.

## What the page shows

The answer card reports the approximation, stop reason, final bracket,
geometric bound in x, substitution into the original function, residual and
relative change. The bound is `max(c-a, b-c)`, approximately `(b-a)/2`; it
assumes the bracket contains a root. It is not the residual, and the relative
change is not the true relative error against a known root. A computed zero
means zero in floating-point evaluation, not a proof of an exact symbolic root.

The shared `StepWalker` starts with the initial interval, then explains each
midpoint, endpoint evaluations and sign decision. Its counter includes the
initial setup, like the matrix reader includes its initial matrix. The same
grey caption, clickable dots, previous/next links and all-steps view are used
on both pages. It reads the saved trace. The table uses that trace, with 15 rows
per page. The **Decimal / Automático** selector controls presentation. Decimal
uses the shared **Decimales** stepper for 0 to 17 places; 5 is the default,
matching the final Excel row. Automatic restores the original 10-significant-digit
format: `0.6` stays `0.6`, while a small residual may appear as `6.538248167e-05`.
The decimal-place controls are hidden in automatic mode. These settings only
format the table, persist across calculations and do not change the saved
trace, stop criterion or answer. Small values may display as zero in decimal
mode; increase the places or switch to automatic notation to inspect them.
Wide tables use the existing horizontal strip. Its scrollbar appears directly
under the data whenever the current columns exceed the available width, and
is refreshed after format, decimal-place or page changes. The heading, format
controls and pagination remain fixed while the columns move. Editing or pasting into any
calculation input invalidates the result.

The graph draws f(x), the initial endpoints a and b, and the final estimate c.
Use **Acercar**, **Alejar**, **Restablecer** and left-button dragging. There is
also mouse-wheel zoom (including Linux wheel events), consumed locally so the
page does not scroll at the same time. **Maximizar** opens a transient window
over the application with the same current view and a graph that fills the
available space. It retains zoom, wheel and pan; Close or Escape dismisses it.
Only one expanded window is opened per graph, and it closes when that graph
is replaced or invalidated. There is
no hover display, point picker, crosshair, cursor-coordinate readout or data
inspection toolbar. Axis tick labels are fixed scale labels. Zoom and pan
only change the view; they do not change the bisection result.

## Course examples and source discrepancies

For `x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10` on `[0.6, 1]`, E = 0.0001:

| Criterion | Iterations | Approximation | Residual |
| --- | --- | --- | --- |
| Interval width | 13 | 0.763916015625 | 0.00027542280657 |
| Residual (Excel example) | 15 | 0.76392822265625 | 0.000065382481667 |

These answers differ because the stopping rules differ. The first has a bound
in x of approximately 0.000048828125. The Excel example reproduces the 15 saved
midpoints and its final residual. Other examples are `x^2 - 2` on `[1, 2]` and
`x^10 - 1` on `[0, 1.3]`.

The sources reviewed were MÉTODOS NUMERICOS.pptx (especially slides 3, 6, 8
and 14), Errores.pptx, Bisección.xlsx (Hoja1), guia-busqueda-raices.pdf,
Búsqueda_Numérica_de_Raíces.pdf, Anatomía_de_la_Incertidumbre_Computacional.pdf
and the three supplied group photographs. The two illustrated PDFs have no
extractable page text and were rendered for visual reading. The photographs
guide the information shown, while the application retains its own styling.

The worked tables are not all internally consistent. In particular, the first
table in guia-busqueda-raices.pdf has function values that do not evaluate its
printed polynomial. Slide 6 also mixes its displayed relative-error values
and final approximation. The implementation evaluates the typed expression;
it does not copy those inconsistent numbers. The spreadsheet formulas and
saved values provide the regression example. Requirements for other methods,
such as checking a derivative in Newton's method, are not bisection features.

## Code and oral defence

| File | Responsibility |
| --- | --- |
| `core/real_function.py` | Reads and evaluates `RealFunction` and samples it for the plot. |
| `core/root_bracket.py` | Validates inputs and intervals, checks stopping rules and records `BracketStep` and `BracketResult`. |
| `core/bisection.py` and `core/regula_falsi.py` | Define each method's estimate and default tolerance. |
| `gui/root_plot.py` | Draws `RootPlot` with Tkinter Canvas and implements view navigation. |
| `gui/pages/root_bracket.py` | `RootBracketPage` arranges the graph, controls, result, step reader and table. |
| `gui/pages/bisection.py` and `gui/pages/regula_falsi.py` | Configure the shared page with each method's solver, examples and labels. |
| `gui/app.py` | Registers the page and keeps the expanded sidebar usable in small windows. |
| `build.py` | Combines the modules in dependency order to generate the independent assignment files. |
| `tests/test_bisection.py` | Course results, bracket invariants and numerical/parser boundary cases. |

The core algorithm is a loop:

1. Validate the parameters, evaluate the endpoints and check their signs.
2. Compute `c = a + (b-a)/2`, algebraically the midpoint formula. This avoids
   overflowing `a+b` for large same-sign endpoints.
3. Evaluate f(c), record the interval and its measures, and test the stop rules.
4. Keep `[a,c]` if f(a) and f(c) have opposite signs; otherwise keep `[c,b]`.
5. Reuse the surviving endpoint values and repeat.

Comparing sign booleans avoids overflow or underflow in `f(a)*f(c)`. Endpoint
values are reused: after the initial evaluations each iteration needs one new
evaluation. For p expression nodes and n iterations, calculation time is
O(n p), with O(n) space for the pedagogical trace. Each additional midpoint
halves the bracket. After n midpoint evaluations its width is
`initial_width / 2**(n-1)`, before that row's next cut.

`core/notation.py` first makes implicit products explicit, using the same
normalization helper as the linear-equation reader. It preserves function calls,
whole identifiers and scientific literals. Each reader retains its own grammar:
linear systems still reject powers and products of unknowns. The parser then
walks a restricted Python AST and interprets only allowed arithmetic,
names and single-argument functions. It never calls `eval` or executes the
input as Python. Expression size and exponent limits bound evaluation work.
Domain errors, non-finite results and detected underflow are reported.

Bisection uses `float`, since this assignment is about numerical approximation
and supports transcendental functions. Matrix algorithms keep their exact
`Fraction` arithmetic. `math` evaluates elementary functions only; the
bisection algorithm itself uses conditionals and a loop, with no numerical
solver library. The plot samples 401 points for each horizontal view, reuses
them for repainting and never supplies the solver's answer.

## Regula Falsi

Open **Métodos Numéricos > Regula Falsi**. Enter f(x) and select **Graficar
función**. Then enter the endpoints and tolerance below the graph. The page
shares the function reader, examples control, graph and zoom, result cards,
step reader, and scrollable table with Bisection. Selecting a preset fills the
inputs and graphs the function before the first iteration.

On each iteration `regula_falsi` chooses c (the guide's xᵣ), the intersection
with the x-axis of the line through `(a, f(a))` and `(b, f(b))`:

```text
c = b − f(b)(a − b)/(f(a) − f(b))
```

The implementation computes the equivalent distance from the endpoint nearer
the intersection, with a ratio of absolute values to avoid overflow when
subtracting large ordinates with opposite signs. `solve_bracket` shares the
validation, sign comparisons, endpoint updates and trace with `bisect`.
Only one new function evaluation is needed per iteration after the endpoints.

The default precision is relative change below **0.01%**. The residual
`|f(c)|` is the other selectable criterion. One endpoint may remain fixed for
many iterations, so there is no halving rule and the bound shown is
`max(c-a, b-c)`. The app reports a rounded estimate that lands on an endpoint
as stagnation if tolerance was not reached. The final substitution and residual
help assess the answer even when relative change is small. As with bisection,
existence of a root in the sign-changing interval requires continuity.

The preset **Ejercicio de la guía** uses `x^3 - 4.23603x^2 - 2.73620x - 13.09037`
on `[4.95, 5.5]` from section 1.2 of `guia-busqueda-raices.pdf`. The printed
table does not match the polynomial. Direct evaluation gives `f(4.95) =
-9.140510075` and `f(5.5) = 10.0956225`. The first estimate is `5.2113457004`
and the fourth is `5.2360505080`, which matches the iterates in the illustrated
`Búsqueda_Numérica_de_Raíces.pdf` (pp. 5–7). The fourth step has relative change
about `0.002862%` and residual about `0.0004642`. The implementation uses the
classical update with the actual endpoint values. The illustrated handout
also discusses the modified method and the slow `x^10 - 1` example, which is
available for comparison with bisection.

Build the independent submission with `python build.py` and run
`python "deliverables/out/Programa Regula Falsi_Grupo5.py"`.

## Graph integration choice

Tkinter Canvas was selected because it is already available and permits the
required zoom/pan without a value-query feature or another dependency.
[Tkinter documentation](https://docs.python.org/3/library/tkinter.html).
Matplotlib could instead be embedded in Tk and restricted to custom zoom/pan
controls, with its coordinate display and picking disabled. It would add a
dependency and more integration work for this assignment.
[Matplotlib's Tk embedding example](https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_tk_sgskip.html).

## Verification and delivery

From the repository root:

```bash
python -m unittest discover -s tests -v
python check.py
python build.py
python "deliverables/out/Programa Biseccion_Grupo5.py"
```

The automated cases compare the course example and bracket containment, test
the percentage convention, endpoint/midpoint roots, undefined relative error,
same-sign intervals, invalid input, limits, stagnation, overflow, underflow and
the expression whitelist. GUI checks cover examples, pagination, step controls,
input invalidation, light/dark appearance, window resizing, zoom, dragging,
reset and the absence of a hover-value binding. The generated file must also
open and calculate successfully without repository imports.

## UI reuse

| UI need | Shared implementation |
| --- | --- |
| Page, result lifecycle, cards and headings | `ResultsPage`, `Card`, `PageHeader`, `SectionTitle` and `_draw_walk`. |
| Step navigation and all-steps view | `StepWalker`, with captions and a numerical-state drawing callback. Matrix callers retain their `StepLog` route. |
| Secondary actions | `LinkButton`, using the reader's text-button style, also used for zoom/reset, help and table pagination. |
| Criterion, example and table-format selection | Existing `SegmentedControl`, matching method/operation selection elsewhere. |
| Table decimal places | Existing `Stepper`, bounded from 0 to 17; initial value 5. |
| Working and numerical values | Existing `MathBlock` and `MathLine`. |
| Primary action, errors and horizontal overflow | `PrimaryButton`, `ErrorBanner` and `Wide`. |

The function/scalar fields use themed `CTkEntry` controls as on the other
pages; matrix grids would be inappropriate for these inputs. The iteration
columns have their own data layout because there is no shared general-purpose
table widget. The graph is the new drawing component: other pages have no
function plot. It reuses the palette, fonts, cards and shared action buttons.
