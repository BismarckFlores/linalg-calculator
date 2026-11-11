# Decisiones de diseño

El proyecto separa el cálculo, la presentación de resultados y la interfaz.
`core/` contiene los algoritmos, `ui/presentation.py` prepara los textos
matemáticos y `desktop/` administra los controles. La entrega se ejecuta desde
el repositorio con `python main.py`.

`core/scalar.py` y `core/notation.py` sirven a todo el motor. Cada área
reúne sus algoritmos en un paquete. Dentro de cada paquete, `handlers/`
contiene la lógica que comparten sus herramientas. Álgebra lineal reutiliza
matrices, ecuaciones y trazas. Los sistemas numéricos comparten la
normalización de numerales, y los métodos numéricos comparten el lector de
funciones y la búsqueda por intervalo.

## Matriz, registro y hoja de trabajo

| Pieza | Responsabilidad |
| --- | --- |
| `Matrix` | Guarda un valor matricial. Las operaciones por filas devuelven otra matriz. |
| `StepLog` | Guarda la matriz inicial y un `Step` por operación. |
| `Worksheet` | Aplica la operación sobre la matriz de trabajo y registra el resultado. |

Una suma ordinaria de matrices puede usar `Matrix` directamente. Durante la
eliminación, la hoja registra la operación en el mismo punto en que la
aplica.

```python
sheet = Worksheet(ab, "Eliminación gaussiana")
sheet.swap(1, 2)
sheet.scale(1, Fraction(1, 3))
sheet.add_scaled(2, 1, -4)
```

`sheet.log.snapshot(k)` devuelve el estado después de k operaciones. Eso
permite que el recorrido avance y retroceda sin volver a calcular.

`Worksheet` omite `swap(i, i)`, `scale(i, 1)` y `add_scaled(i, j, 0)`
porque dejan la matriz igual. `Matrix.scale_row(i, 0)` y
`Matrix.add_scaled_row(i, i, k)` lanzan un error porque no representan
operaciones elementales válidas. La construcción de una matriz también
valida su forma. Por ejemplo, `Matrix([[1, 2], [3]])` falla al construirse.

## Aritmética exacta y búsqueda numérica

Las entradas matriciales son `Fraction`. Escribir `0.18` produce `9/50` y
un tercio sigue siendo exacto. Esto permite comprobar la solución con
igualdades exactas.

La búsqueda de raíces usa `float` para evaluar funciones elementales.
`core/numerical_methods/handlers/real_function.py` interpreta la expresión, `core/numerical_methods/handlers/root_bracket.py`
conserva el intervalo, aplica la parada y registra las iteraciones.
Bisección aporta el punto medio y Regula Falsi aporta el cruce de la
secante. El resultado distingue tolerancia, cero, estancamiento y límite.
Consulta las [condiciones y ejemplos](bisection.md).

`core/notation.py` agrega signos de multiplicación omitidos. Cada lector
aplica después su propia gramática. Búsqueda de raíces acepta `5x^3` y
`2(x+1)`. Los sistemas aceptan `2x` y `(1/2)x` como términos lineales.
La normalización conserva los nombres completos y las llamadas a funciones.
El evaluador de funciones usa un AST restringido. Reutilizar el valor del
extremo que permanece permite evaluar una sola vez por iteración.

## Clasificación y comprobación

`to_ref` reduce hasta la forma escalonada. `to_rref` continúa hacia arriba
para crear ceros sobre los pivotes. Quien llama elige la reducción según
el cálculo. La forma reducida se incorporó cuando la actividad de
Gauss–Jordan la necesitó.

La clasificación cuenta pivotes antes de resolver. Si `rango(A) < rango(A|b)`
hay contradicción. Si los rangos coinciden y son menores que el número de
incógnitas, hay variables libres. Si también coinciden con el número de
incógnitas, se hace la sustitución hacia atrás. Un pivote en la última
columna produce una ecuación `0 = k` con k distinto de cero. La familia
paramétrica se calcula por separado para el caso indeterminado.

`verify` recibe A, b y los valores. Evalúa las ecuaciones originales,
independientemente del método que dio la solución. Comparar solo con la
matriz reducida podría ocultar un error de la propia eliminación.

## Inversa, LU y determinante

La inversa reduce `[A | Iₙ]` con Gauss–Jordan y comprueba el bloque
izquierdo completo. Contar los pivotes de toda la matriz aumentada sería
insuficiente porque el bloque de identidad también aporta pivotes.
Cuando el bloque izquierdo llega a `Iₙ`, el derecho es `A⁻¹`. Se comprueban
ambos productos con la A original. La misma página permite resolver
`Ax = b` mediante `x = A⁻¹b`.

Las páginas de inversa y LU comparten `MatrixTaskFields` para leer una
matriz sola o un sistema. La inversa admite hasta 1000 filas y columnas.
Las demás entradas conservan sus límites propios.

`core/linear_algebra/lu.py` se encarga de P, L, U, los pivotes, los casos singulares y
las sustituciones. `core/linear_algebra/determinant.py` utiliza la factorización para
multiplicar la diagonal de U y ajustar el signo. También puede expandir
cofactores directamente. Los pivotes se comparan con cero exacto.

## Combinaciones lineales

Para determinar si b es combinación de v₁, …, vₖ, se buscan escalares
c₁, …, cₖ que cumplan `c₁v₁ + … + cₖvₖ = b`. `core/linear_algebra/vectors.py` forma
`[v₁ … vₖ | b]` y llama a `solve`. La dimensión sale de las componentes
y se comprueba que los vectores sean compatibles. El resultado comparte
los rangos, la reducción, la solución general y la comprobación del
solucionador de sistemas.

## Componentes de la interfaz

`desktop/core/` comparte los formularios, controles y el puente de MathLive.
Las páginas de `desktop/tools/` componen esos controles y conectan el motor.
`ToolPage` comparte formulario, errores y resultado.
`MatrixInput` comparte la entrada de coeficientes y `read_equations`
conserva los nombres de incógnitas. `StepView` navega las trazas de
álgebra y raíces. `ResultTable` comparte la presentación tabular de
conversiones e iteraciones.

El visor de resultados de MathLive agrupa fórmulas y explicaciones por
sección. `StepView` usa el mismo encabezado numerado en el recorrido
individual y en la vista completa. El banner, el acceso de Inicio y el
menú lateral comparten el SVG de identificación de cada herramienta.

`RootBracketPage` organiza la gráfica antes de los controles y configura
cada método mediante su fórmula, criterios y ejemplos. El motor toma las
muestras que `FunctionPlot` dibuja con Qt. La gráfica conserva zoom,
arrastre, restablecimiento y vista ampliada.

`NewtonRaphsonPage` usa `FunctionPlot` en modo de selección de x.
Un clic actualiza x₀ y su marca en ambas vistas. El arrastre sigue
moviendo la vista. La página conecta el motor de Newton con `StepView`
y la tabla paginada `IterationTable`, que comparte con Bisección y Regula
Falsi. La página invalida los resultados al editar los parámetros.

`calculus_page` reutiliza `ToolPage` y presenta tres operaciones con el
mismo editor de funciones. Muestra el punto opcional en Derivada y el
par de límites en Integral definida. `core/calculus.py` conserva el
cálculo fuera de Qt. Los resultados llevan fórmulas LaTeX para MathLive
y texto para la vista de respaldo.

`MathInput` carga el editor local y conecta Qt con MathLive mediante
QWebChannel. Los adaptadores traducen el formato visual a texto para el
motor. Los campos de respaldo conservan la última entrada del usuario.

## Integrar una herramienta nueva

- **Navegación.** Registra una clave única, categoría, nombre en español,
  descripción breve y fábrica de la página en `desktop/tools/registry.py`.
  El registro alimenta Inicio y la barra lateral.
- **Identidad visual.** Agrega `desktop/assets/navigation/<clave>.svg` para
  el menú lateral y un SVG propio en `desktop/assets/banners/`. Asocia el
  banner al glifo de la herramienta en `PAGE_ILLUSTRATIONS`. Usa
  `page_header` para el título y la descripción. Inicio reutiliza ese banner
  en su tarjeta.
- **Entrada y limpieza.** Usa `ToolPage` o reutiliza `input_actions` si la
  página tiene un flujo propio. Incluye **Limpiar** y **Ctrl+Mayús+Supr**,
  conserva las dimensiones de las matrices al ponerlas en cero e invalida
  el resultado al editar. Usa MathLive con su respaldo de texto si la
  herramienta necesita fórmulas.
- **Salida.** Muestra el resultado y los errores en español. Si el motor
  entrega una traza, una tabla o una gráfica, reutiliza los componentes
  compartidos que correspondan.
- **Documentación y pruebas.** Agrega la herramienta a la [guía de interfaz](gui.md).
  Comprueba la apertura desde Inicio y la barra lateral, el ancho mínimo,
  ambos temas, un ejemplo válido, una entrada inválida, la edición y la
  limpieza. Ejecuta `python check.py` y `python -m unittest discover -s tests -v`.

## Texto y lectura de datos

Los identificadores siguen la convención en inglés, como `to_rref`,
`SingularMatrix` y `render_equations`. Los comentarios y mensajes se
escriben en español. El motor devuelve datos y lanza excepciones en español.
La interfaz indica qué campo o ecuación requiere corrección.

`core/linear_algebra/handlers/equations.py` distingue `MissingEquals` de `UnreadableTerm`, ambos
derivados de `EquationError`. `UnreadableTerm` conserva el fragmento que
falló. La entrada común de álgebra agrega el número de línea al aviso. La lista de
incógnitas detectadas ayuda a reconocer, por ejemplo, un `2x + 3x = 5`
cuando se quería escribir `2x + 3y = 5`.

`render_despeje` comparte el formato de sustitución entre eliminación y LU.
Recibe números y nombres. La página de LU recorre su propio registro de
sustituciones y le entrega esos datos.
