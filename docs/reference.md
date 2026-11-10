# Referencia del código

Las firmas y los nombres corresponden a los módulos del repositorio. Las
cadenas de documentación de cada función explican los detalles de su contrato.

## Capas y flujo de datos

`core/` contiene los algoritmos. `ui/presentation.py` convierte resultados
en texto y `desktop/` conecta el motor con las entradas, gráficas y tarjetas.

```text
MatrixInput / read_equations ──> [A | b], incógnitas y nombres
                         │
                         └──> systems.solve() ──> Solution
                                                  ├── log → StepView
                                                  ├── result → sistema equivalente
                                                  ├── kind → clasificación
                                                  ├── substitutions → despeje
                                                  └── values → verify(A, b, x)

RealFunction ──> FunctionPlot
       └──> bisect() o regula_falsi() ──> BracketResult ──> tabla y recorrido
```

`scalar` y `matrix` son la base de la aritmética. `Worksheet` combina una
matriz y un `StepLog` para que `elimination` pueda registrar operaciones.
`systems` usa esa reducción. `verification` depende solo de la matriz y
los escalares para comprobar el sistema original. `echelon` y
`parametric` consultan la reducción para identificar pivotes y escribir
familias. `vectors` delega las combinaciones lineales en `solve`.
`bases` y `roman` tienen su propia aritmética de numerales.

## Métodos numéricos

La [guía de raíces](bisection.md) explica las condiciones y ejemplos.

| Módulo | Nombre | Contrato |
| --- | --- | --- |
| `core/real_function.py` | `RealFunction(text)` | Lee una función en x con un AST restringido. Se puede llamar con un valor de x. Eleva `RootInputError` ante una expresión o evaluación inválida. |
| `core/real_function.py` | `sample_function(function, a, b, count=401)` | Devuelve muestras. Los puntos indefinidos se representan como `(x, None)`. |
| `core/root_bracket.py` | `read_root_number(value)` | Usa `to_scalar` y convierte a un `float` finito. |
| `core/root_bracket.py` | `RootCriterion` | `WIDTH`, `RESIDUAL` y `RELATIVE` (porcentaje). |
| `core/root_bracket.py` | `RootStop` | `ZERO`, `TOLERANCE`, `LIMIT` y `STAGNATION`. |
| `core/root_bracket.py` | `solve_bracket(function, a, b, tolerance, criterion, max_iterations, estimate)` | Recibe una función de estimación. Comprueba los extremos, conserva el cambio de signo y guarda la traza. |
| `core/bisection.py` | `bisect(function, a, b, tolerance="0.0001", *, criterion=WIDTH, max_iterations=100)` | Usa el punto medio y devuelve un `BracketResult`. |
| `core/regula_falsi.py` | `regula_falsi(function, a, b, tolerance="0.01", *, criterion=RELATIVE, max_iterations=100)` | Usa la intersección de la secante y devuelve un `BracketResult`. |

`BracketStep` guarda `index`, `a`, `b`, `c`, `fa`, `fb`, `fc` y
`relative_error`. Expone el ancho, cota, residuo y decisión de signo.
`BracketResult` guarda la función, extremos iniciales y finales,
tolerancia, criterio, iteraciones, motivo de parada, aproximación y valor.
También expone `converged` y `bound`. Ambos registros son inmutables.
`core/bisection.py` conserva los nombres anteriores `Bisection*`,
`bisection_number` y `sample_bisection` como alias.

## `core/scalar.py`

| Nombre | Significado |
| --- | --- |
| `Scalar` | `Fraction`, el tipo de las entradas matriciales. |
| `NumberLike` | `int \| float \| Fraction \| str`. |
| `to_scalar(value) -> Scalar` | Acepta, por ejemplo, `"2,5"` y `"1/3"`. Lanza `ValueError` para texto inválido y `TypeError` para booleanos. |
| `format_scalar(value) -> str` | Formato como `3`, `-4` o `1/3`. |
| `format_factor(value) -> str` | Agrega paréntesis cuando es negativo o fraccionario, como `(-1)` o `(1/3)`. |

## `core/matrix.py`

`Matrix` representa un rectángulo de escalares exactos. Los índices de
filas y columnas de su API empiezan en 1. `data` es una lista de listas
con índices desde 0. La construcción rechaza filas de distinto tamaño.

| Método | Resultado |
| --- | --- |
| `elem(i, j)` | Entrada `a_ij`. |
| `row(i)`, `column(j)` | Fila o columna como lista. |
| `diagonal()` | Diagonal principal hasta donde alcance. |
| `size()` | Par `(rows, cols)`. También hay atributos `rows` y `cols`. |
| `is_square()`, `is_zero_row(i)` | Comprueban forma cuadrada o fila nula. |
| `require_square()` | Exige matriz cuadrada. Lanza `NotSquare` con `rows` y `cols`. |
| `transpose()` | Intercambia filas y columnas. |
| `augment(other)` | `[A \| B]`. Exige el mismo número de filas. |
| `take_columns(first, last)` | Selecciona columnas, incluyendo ambos extremos. |
| `minor(i, j)` | Elimina la fila i y la columna j. |
| `swap_rows(i, j)` | Intercambia dos filas. |
| `scale_row(i, k)` | Multiplica por k. Rechaza k = 0. |
| `add_scaled_row(i, j, k)` | Suma k veces la fila j a la i. Rechaza i = j. |

Las operaciones por filas devuelven una matriz nueva. Usa `Worksheet`
para conservar la operación en el registro. `SingularMatrix` contiene la
columna del pivote faltante, o `None`.

Los operadores son `A + B`, `A - B`, `A * B`, `k * A`, `A * k`, `-A`
y `A == B`. Las formas incompatibles dan `ValueError`. Un escalar puede
escribirse como texto, por ejemplo `A * "1/2"`. Los constructores
auxiliares son `Matrix.zero(rows, cols)`, `Matrix.identity(n)` y
`Matrix.column_vector(values)`. `str(m)` alinea las entradas y `repr(m)`
representa la construcción de la matriz.

## `core/steps.py`

| Función | Ejemplo de etiqueta |
| --- | --- |
| `label_swap(i, j)` | `f_1 <-> f_2` |
| `label_scale(i, k)` | `f_2 -> (1/3)*f_2` |
| `label_add_scaled(i, j, k)` | `f_2 -> f_2 + 3*f_1`. Omite la magnitud del factor si vale 1 o −1. |

`Step` es inmutable y guarda `before`, `label`, `after` y `note`.
`render()` muestra ambos estados junto a la etiqueta.

| Miembro de `StepLog` | Significado |
| --- | --- |
| `snapshot(k)` | Matriz después de k operaciones. El estado 0 es la inicial. |
| `result` | Último estado. |
| `record(before, label, after)` | Agrega una operación. Habitualmente se llama desde `Worksheet`. |
| `annotate(text)` | Añade una nota al último paso. |
| `is_empty()`, `len(log)`, `log[i]`, iteración | Consultan el contenido del registro. |
| `summary()`, `render()`, `str(log)` | Vistas de depuración. |

## `core/worksheet.py`

`sheet.matrix` es el estado actual y `sheet.log` es el recorrido.

| Método | Operación |
| --- | --- |
| `swap(i, j)` | Intercambia filas. Omite el paso si i = j. |
| `scale(i, k)` | Multiplica por k. Omite el paso si k = 1. |
| `add_scaled(i, j, k)` | Suma k veces la fila j a la i. Omite el paso si k = 0. |

## `core/elimination.py`

| Función | Resultado |
| --- | --- |
| `to_ref(matrix, title="") -> Elimination` | Reduce a forma escalonada con registro. |
| `to_rref(matrix, title="") -> Elimination` | Añade el recorrido ascendente que hace ceros encima de cada pivote. |
| `rank(matrix) -> int` | Cuenta los pivotes. |

`Elimination` es inmutable. Contiene `original`, `result`, `log`,
`pivots` y `reduced`. Los pivotes son pares `(fila, columna)` con índices
desde 1 y ordenados por fila. Las consultas son `rank`,
`pivot_columns()`, `free_columns()` y `zero_rows()`. Los pivotes de la
forma escalonada producida por el algoritmo valen 1 y tienen ceros debajo.
En la forma reducida también tienen ceros arriba.

## `core/inverse.py`

| Función | Contrato |
| --- | --- |
| `invert(matrix) -> InverseResult` | Reduce `[A \| Iₙ]`. Lanza un error para una A no cuadrada y `SingularMatrix` si el bloque izquierdo no llega a `Iₙ`. |
| `solve_with_inverse(matrix, constants) -> InverseSystem` | Requiere A invertible y b de n×1. Calcula `A⁻¹b` y comprueba el sistema original. |

`InverseResult` conserva A, la inversa, el registro y ambos productos.
`InverseSystem` agrega b, x y la comprobación `Ax`.

## `core/systems.py`

`solve(augmented) -> Solution` recibe una matriz aumentada con al menos
una ecuación y dos columnas. `SystemKind` distingue `UNIQUE`,
`INFINITE` e `INCONSISTENT`.

`BackSubstitution` guarda `column`, `row`, `constant`, los `terms` como
pares de coeficiente y columna, y `value`.

| Campo de `Solution` | Significado |
| --- | --- |
| `kind`, `unknowns` | Clasificación y número de incógnitas. |
| `values` | Valores en orden de columna para solución única. |
| `free_columns` | Columnas sin pivote para infinitas soluciones. |
| `substitutions` | Despejes desde la última incógnita para solución única. |
| `homogeneous` | Indica si todas las constantes son cero. |
| `log` | Registro de la eliminación. |
| `augmented`, `result` | Matrices inicial y final. |
| `coefficients`, `constants` | A y b separados para comprobar. |
| `rank`, `coefficient_rank` | Rangos de `[A \| b]` y A. |
| `reduction` | Objeto `Elimination` con la información de pivotes. |

## `core/notation.py`

`explicit_products(text, functions=(), *, scientific=True)` agrega productos
entre factores adyacentes y conserva nombres completos y llamadas conocidas.
`scientific=False` mantiene la interpretación lineal de nombres como
`e3x` después de un coeficiente. Cada lector valida su gramática.

## `core/equations.py`

| Función | Contrato |
| --- | --- |
| `parse_equation(text) -> Equation` | Mueve incógnitas a la izquierda y constantes a la derecha. |
| `unknown_names(equations) -> list[str]` | Nombres en orden natural, de modo que x2 aparece antes de x10. |
| `to_augmented(equations, names) -> Matrix` | Organiza `[A \| b]` en ese orden y completa coeficientes ausentes con cero. |

`Equation` guarda `terms`, `constant` y el `text` original.
`MissingEquals` indica que la línea requiere exactamente un signo igual.
`UnreadableTerm.text` guarda el fragmento ilegible. Ambos errores
derivan de `EquationError` y la interfaz agrega el número de línea.

## `core/determinant.py`

| Función | Contrato |
| --- | --- |
| `by_cofactors(matrix, depth=FULL) -> Cofactors` | Expansión recursiva por la línea con más ceros. `depth` limita los niveles guardados. |
| `by_lu(matrix) -> ByLU` | Producto de la diagonal de U ajustado por el signo de la permutación. |
| `determinant(matrix) -> Scalar` | Fórmula directa hasta 2×2 y LU para órdenes mayores. |
| `costs(order) -> Costs` | Estima multiplicaciones y recomienda un método. |
| `best_line(matrix)` | Devuelve `ROW` o `COLUMN` con el índice de la línea con más ceros. |
| `COFACTOR_LIMIT`, `LU_FROM` | Límite de cofactores en la interfaz y orden desde el cual se recomienda LU, 8 y 4 respectivamente. |

Se exige una matriz cuadrada. `Cofactors` conserva `matrix`, `along`,
`index`, `terms`, `rule`, `value` y si se expandió (`expanded`).
Cada `Summand` guarda la entrada, signo, menor, cofactor y contribución.
`Rule` representa `ad − bc`. `ByLU` contiene la factorización y el valor.
`Costs` contiene `order`, `cofactor`, `lu`, `advised` y `times`.

## `core/lu.py`

| Función | Contrato |
| --- | --- |
| `factorize(matrix, partial=False, strict=False) -> Factorization` | Factoriza `PA = LU`. `partial` elige el pivote de mayor valor absoluto. `strict` eleva `SingularMatrix` ante un pivote faltante. |
| `solve_with_lu(matrix, constants, partial=False) -> LUSystem` | Resuelve `Ly = Pb` y `Ux = y`. Comprueba `Ax = b`. Lanza `SingularMatrix` si U tiene un cero en la diagonal. |

`Factorization` guarda `matrix`, `lower`, `upper`, `permutation`,
`swaps`, `rank` y `log`. Las propiedades derivadas son `permuted`,
`singular`, `diagonal`, `row_order`, `permuted_matrix`, `product` y
`holds`. L es triangular inferior unitaria y U es triangular superior.
Se comprueba `PA = LU` con igualdad exacta.

`LUSystem` incluye la factorización, `constants`, `permuted` (Pb), las
sustituciones, `intermediate` (y), `solution` (x) y `check` (Ax). Una
`Substitution` guarda `unknown`, `known` como ternas de coeficiente, valor
e índice, `constant`, `divisor` y `value`. En L el divisor es 1. En U es
el pivote. Se usa el primer pivote distinto de cero salvo al activar
pivoteo parcial.

## `core/echelon.py`

| Función o dato | Significado |
| --- | --- |
| `leading_column(matrix, row)` | Columna de la entrada principal o `None` para fila nula. |
| `leading_entries(matrix)` | Pares `(fila, columna)` en orden de fila. |
| `analyse(matrix) -> Form` | Comprueba las cinco propiedades. |
| `pivot_positions(matrix)` | Reduce y encuentra las posiciones pivote de la forma reducida. |
| `pivot_columns(matrix)`, `free_columns(matrix)` | Columnas con pivote y sin pivote. |
| `ECHELON`, `REDUCED` | Propiedades (1, 2, 3) y propiedades adicionales (4, 5). |

`Condition` registra el número, si se cumple y dónde falla. La
propiedad 1 corresponde a la fila, así que su columna se marca con 0.
`Form` conserva `matrix`, `conditions` y `leading`. `condition(n)`
consulta una propiedad de 1 a 5. `is_echelon` exige las primeras tres
y `is_reduced` exige las cinco. La matriz nula satisface todas.

## `core/parametric.py`

`general_solution(reduction, unknowns) -> General` lee la familia de
una reducción en forma escalonada reducida. Lanza `ValueError` si
recibe una reducción sin terminar. Se clasifica primero el sistema,
porque un pivote en la columna de constantes indica contradicción.

`Basic` guarda `column`, `constant` y pares `(coeficiente, columna libre)`
para expresar la variable como constante más términos libres. `General`
agrupa `basic` y `free` en orden de columna.

## `core/bases.py`

| Función o dato | Contrato |
| --- | --- |
| `to_base(value, base) -> ToBase` | Divide el valor absoluto y restituye el signo. Valida la base. |
| `from_base(text, base) -> FromBase` | Evalúa la combinación de potencias. Ignora espacios y mayúsculas. Admite un signo inicial. |
| `digit_value(character, base)` | Valor de una cifra en la base. |
| `DIGITS` | Símbolos 0–9 y A–Z para valores 0–35. |
| `LOWEST_BASE`, `HIGHEST_BASE` | 2 y 36. |

`ToBase` guarda `value`, `base`, `divisions`, `numeral` y `negative`.
Cada `Division` cumple `dividend = base * quotient + remainder`. Las
divisiones van en el orden de cálculo y las cifras se leen al revés.

`FromBase` guarda `numeral`, `base`, `terms`, `value`, `negative` y
`magnitude`. Cada `Term` tiene `digit`, `value`, `position` desde cero a
la derecha, `power` y `amount`. `-0` se normaliza a cero.
`EmptyNumeral` incluye un signo sin cifras. `BadDigit` contiene el
`digit` inválido y la `base`. Ambos derivan de `NumeralError`.

## `core/roman.py`

| Función o dato | Contrato |
| --- | --- |
| `to_value(text) -> int` | Lee la escritura canónica. `XIV` vale 14. |
| `to_roman(value) -> str` | Toma repetidamente la pieza más grande que cabe. Lanza `OutOfRange` fuera de 1–3999. |
| `read(text) -> Numeral` | Devuelve texto, valor y piezas. |
| `sum_of(a, b)`, `difference_of(a, b)` | Lee ambos operandos y convierte el resultado. |
| `product_of(a, b)` | Guarda además la suma repetida. |
| `PIECES`, `SYMBOLS`, `LARGEST` | Las trece piezas, los siete símbolos y 3999. |

`Numeral` guarda `text`, `value` y `pieces`. Cada `Piece` tiene texto,
valor y `subtractive` para los pares de resta. `Operation` guarda
`left`, `right`, `sign`, `value`, `numeral` y `terms`.
`writable` indica si el resultado tiene representación romana.
`NotCanonical` lleva el numeral y su forma canónica. `BadOrder` lleva
el numeral con orden inválido y `BadLetter` su letra inválida.
Los errores derivan de `RomanError`.

## `core/vectors.py`

| Función o dato | Contrato |
| --- | --- |
| `Vector` | Tupla de escalares exactos. Su longitud determina la dimensión. |
| `parse_vector(text) -> Vector` | Admite `(1, -2, 1/3)`, `1 -2 1/3` y `[1; -2; (1/3)]`. Usa punto decimal. |
| `add(u, v)`, `subtract(u, v)` | Operan por componente. Exigen dimensiones iguales. |
| `scale(k, u)` | Multiplica las componentes por k. |
| `linear_sum(weights, vectors)` | Suma `c₁v₁ + … + cₖvₖ`. |
| `combination_matrix(vectors, target) -> Matrix` | Forma `[v₁ … vₖ \| b]`. |
| `combine(vectors, target) -> Combination` | Forma el sistema y lo resuelve. |

`Combination` conserva `vectors`, `target`, `solution` y `general`.
`is_combination` indica consistencia. `weights` es la solución única o,
si hay infinitas, la que fija los escalares libres a cero. Si el sistema
es inconsistente, es `None`. `EmptyVector` indica ausencia de componentes.
`UnreadableComponent.text` guarda el texto inválido y `DimensionMismatch`
contiene ambas dimensiones. Derivan de `VectorError`.

## `core/verification.py`

`verify(coefficients, constants, values) -> Verification` evalúa `Ax = b`
fila por fila. Exige una columna de constantes, igual número de filas y
tantos valores como incógnitas. `RowCheck` guarda `row`, `terms` como
ternas de coeficiente, valor y columna, `left`, `right` y `holds`.
`Verification` reúne `checks`, `holds` y `failures()`.

## `ui/presentation.py`

Prepara el texto matemático que usan las páginas. Los nombres vienen de
la entrada de ecuaciones o se completan con x, y, z, w, x5 y siguientes.

| Función | Qué produce |
| --- | --- |
| `subscript(number)`, `superscript(number)` | Dígitos en subíndice o superíndice. |
| `unknown_name(col, names=())` | Nombre introducido o el predeterminado para esa columna. |
| `render_despeje(head, name, divisor, known, constant, value)` | Ecuación, sustitución, constante despejada y resultado. Incluye división cuando el divisor difiere de 1. |
| `pretty_label(label)` | Notación tipográfica, como `f₂ → f₂ + 3 · f₁`. |
| `describe(solution)` | Clasificación a partir de `CLASSIFICATIONS`. |
| `render_values(solution, names=())` | Valores, variables libres o fila contradictoria. |
| `render_equations(solution, names=())` | Forma escalonada escrita como ecuaciones. |
| `render_system(matrix, unknowns, names=())` | Sistema representado por cualquier matriz aumentada. |
| `render_general(family, names=())` | Una línea por variable básica, como `x = 1 - 4z`. |
| `render_linear_sum(weights, names)` | Combinación de vectores sin términos de coeficiente cero. |
| `typographic_rows(block)` | Convierte `f_2:` en `f₂:` y mantiene la alineación. |
| `render_substitutions(solution, names=())` | Pasos del despeje, omitiendo líneas repetidas. |
| `render_verification(verification)` | Sustitución y veredicto por ecuación. |

Los productos se presentan como `2y`, `1(29)` y `(1/3)x`. Los
paréntesis separan el valor sustituido de su coeficiente.

## `desktop/`

Abre la ventana con `python main.py`. La [guía de la interfaz](gui.md)
describe qué muestra cada herramienta.

| Módulo | Responsabilidad |
| --- | --- |
| `desktop/window.py` | Catálogo, menú, páginas bajo demanda y tema. |
| `desktop/forms.py` | Entrada de matrices, lectura de ecuaciones, formularios, resultados y recorrido de pasos. |
| `desktop/widgets.py` | Estilos Qt, tarjetas, botones y tablas. |
| `desktop/math_input.py` | MathLive en Qt WebEngine, canal de edición y respaldo de texto. |
| `desktop/math_notation.py` | Adaptadores entre texto, MathLive y los lectores del motor. |
| `desktop/matrix_tools.py` | Gauss, formas escalonadas, operaciones, inversa, LU y determinante. |
| `desktop/number_tools.py` | Vectores, conversiones y aritmética romana. |
| `desktop/roots.py` | Flujo compartido y configuración de Bisección y Regula Falsi. |
| `desktop/plot.py` | Dibujo Qt, zoom, arrastre y gráfica ampliada. |
| `ui/theme_tokens.py` | Paleta claro y oscuro, radios y tipografía. |

`ToolPage` invalida la respuesta al editar. `Result` reúne el texto,
el procedimiento y los datos tabulares. `StepView` muestra la traza
calculada y `ResultTable` presenta los valores con formato de pantalla.

## Pruebas y convenciones

- `check.py` ejecuta comprobaciones del motor.
- `python -m unittest discover -s tests -v` ejecuta las pruebas unitarias.
  Las de interfaz requieren PySide6 y una sesión gráfica.
- Los índices de las operaciones matriciales empiezan en 1. Las listas
  de Python como `Matrix.data` empiezan en 0.
- Las matrices producen valores nuevos al operar. Los registros de
  resultados usan dataclasses inmutables.
- `core/` devuelve datos o lanza excepciones. La interfaz muestra los
  avisos de entrada y la explicación del resultado.
