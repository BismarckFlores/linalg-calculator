# Cómo funciona

Este ejemplo recorre un sistema desde la entrada hasta la verificación.
Puedes seguirlo en **Eliminación Gaussiana → Ecuaciones**.

```text
 x - 2y +  z =  0
     2y - 8z =  8
-4x + 5y + 9z = -9
```

## 1. Convertir el sistema en una matriz

Cada columna representa una incógnita. Los términos independientes se
colocan al final, después de la barra.

```text
  [  1  -2   1 |  0 ]
  [  0   2  -8 |  8 ]
  [ -4   5   9 | -9 ]
```

La matriz aumentada `[A | b]` es un objeto `Matrix`. La interfaz dibuja la
barra al conocer el número de incógnitas. Cada entrada es un `Fraction`,
así que el valor de un coeficiente como `1/3` se conserva exactamente.

## 2. Reducir por filas

Las siguientes operaciones conservan el conjunto de soluciones.

- Intercambiar dos filas, `f_i <-> f_j`.
- Multiplicar una fila por un número distinto de cero, `f_i -> k*f_i`.
- Sumar un múltiplo de una fila a otra, `f_i -> f_i + k*f_j`.

`core/elimination.py` busca un pivote, lo lleva a uno y crea ceros debajo.
Después pasa a la siguiente columna con pivote.

```text
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

`Worksheet` aplica y registra cada operación. `StepLog.snapshot(k)` devuelve
la matriz después de `k` pasos. El paso a paso consulta ese estado al
avanzar o retroceder. La última matriz está en **forma escalonada** y el
primer coeficiente distinto de cero de cada fila es un pivote.

## 3. Leer el sistema equivalente

```text
  f_1:  x - 2y + z = 0
  f_2:      y - 4z = 4
  f_3:           z = 3
```

Las soluciones son las mismas que en el sistema inicial. Ahora la última
ecuación da directamente el valor de `z`.

## 4. Clasificar el sistema

`core/systems.py` aplica Rouché–Frobenius. `rango(A|b)` cuenta todos los
pivotes y `rango(A)` cuenta los de las columnas de incógnitas.

| Condición | Clasificación |
| --- | --- |
| `rango(A) < rango(A\|b)` | Sistema inconsistente, sin solución. |
| `rango(A) = rango(A\|b) < incógnitas` | Sistema consistente indeterminado, infinitas soluciones. |
| `rango(A) = rango(A\|b) = incógnitas` | Sistema consistente determinado, solución única. |

Un pivote en la última columna produce una ecuación `0 = k` con `k ≠ 0`.
En el ejemplo ambos rangos valen 3, igual que el número de incógnitas.

## 5. Despejar de abajo hacia arriba

`core/systems.py` guarda cada sustitución. Se empieza por la última
incógnita y se usan los valores encontrados al subir de fila.

```text
  f_3:  z = 3

  f_2:  y - 4z = 4
        y - 4(3) = 4
        y = 4 + 4(3)
        y = 16

  f_1:  x - 2y + z = 0
        x - 2(16) + 3 = 0
        x = 2(16) - 3
        x = 29
```

El despeje muestra la ecuación, la sustitución, el traslado de la constante
y el resultado. Si dos líneas coinciden, aparece una sola.

## 6. Comprobar con el sistema original

`core/verification.py` sustituye los valores en A y b originales. La
comparación es exacta gracias a que las operaciones usaron fracciones.

```text
  Ecuación 1:  1(29) - 2(16) + 1(3) = 0
               0 = 0   correcto
  Ecuación 2:  0(29) + 2(16) - 8(3) = 8
               8 = 8   correcto
  Ecuación 3:  -4(29) + 5(16) + 9(3) = -9
               -9 = -9   correcto

Todas las ecuaciones se cumplen: la solución es correcta.
```

## Los otros dos casos

**Infinitas soluciones.** Las ecuaciones `x + y + z = 3` y
`2x + 2y + 2z = 6` expresan la misma restricción. La segunda fila se reduce
a ceros. Ambos rangos son 1 y hay tres incógnitas. Las columnas de `y` y `z`
son libres. Puedes elegirlas y obtener `x = 3 - y - z`.

**Sin solución.** Las ecuaciones `x + y = 5` y `x + y = 8` se contradicen.
La reducción normaliza la última fila a `0 = 1`. Se obtiene `rango(A) = 1`
y `rango(A|b) = 2`. La app indica la fila que causa la contradicción.

## Dónde vive cada parte

| Responsabilidad | Módulo |
| --- | --- |
| Números exactos | `core/scalar.py` |
| Matriz y operaciones por filas | `core/matrix.py` |
| Registro de operaciones | `core/steps.py` y `core/worksheet.py` |
| Eliminación | `core/elimination.py` |
| Clasificación y despeje | `core/systems.py` |
| Comprobación | `core/verification.py` |
| Lectura de ecuaciones | `core/equations.py` |
| Forma escalonada y pivotes | `core/echelon.py` |
| Familia de soluciones | `core/parametric.py` |
| Conversión entre bases | `core/bases.py` |
| Vectores y combinaciones lineales | `core/vectors.py` |
| Formato de los resultados | `ui/presentation.py` |
| Controles y tarjetas | `desktop/` |

El motor devuelve datos y la interfaz se encarga de mostrarlos. Consulta la
[guía de la ventana](gui.md) y las [decisiones de diseño](design.md).
