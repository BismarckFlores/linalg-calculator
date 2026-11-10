# Guía de uso

Abre la calculadora desde la raíz del repositorio con Python 3.12 o posterior.

```bash
python -m pip install -r requirements-gui.txt
python main.py
```

**Inicio** presenta las herramientas por tema. Abre una tarjeta o elige una
herramienta en el menú lateral.

## Resolver un sistema lineal

En **Sistemas Lineales → Eliminación Gaussiana**, elige Gauss o Gauss–Jordan y
selecciona **Coeficientes** o **Ecuaciones**.

### Ecuaciones

Escribe una ecuación por línea. Puedes probar este sistema:

```text
x - 2y + z = 0
2y - 8z = 8
-4x + 5y + 9z = -9
```

La app deduce los nombres de las incógnitas, los ordena por columna y usa esos
mismos nombres en el resultado. Si hay un error de lectura, indica la línea
que debes corregir.

| Escritura | Interpretación |
| --- | --- |
| `2x + 3y - z = 5` | Los espacios son opcionales. |
| `x + y = 2` | Un coeficiente omitido vale 1. |
| `2*x + 3*y = 1` | Puedes escribir el producto explícitamente. |
| `2.5x`, `2,5x`, `1/3x`, `(1/3)x` | Se admiten decimales y fracciones. |
| `2x = 3y + 1` | Las incógnitas pasan a la izquierda. |
| `2x + 3 = 5` | Las constantes pasan a la derecha. |
| `x + x = 4` | Se suman los términos de una misma incógnita. |
| `x1`, `x_2`, `X` | Se admiten letras, dígitos y `_`. Las mayúsculas se tratan como minúsculas. |

`1/3x` se lee como `(1/3)x`. Las potencias y los productos entre incógnitas se
admiten en el lector de funciones reales de Métodos Numéricos, mientras que
la entrada de sistemas lineales exige términos lineales.

### Coeficientes

Ajusta el número de ecuaciones y de incógnitas con los controles de tamaño.
Escribe los coeficientes en A y los términos independientes en b. La celda
`aᵢⱼ` es el coeficiente de la incógnita j en la ecuación i. La celda `bᵢ`
es el término independiente de esa ecuación. Las incógnitas se nombran
`x`, `y`, `z`, `w` y luego `x5`, `x6`, etc.

La aplicación conserva los valores exactos. Por ejemplo, `1/3` sigue siendo
un tercio durante toda la reducción. Al resolver puedes revisar la matriz
inicial, las operaciones por filas, el sistema equivalente, los rangos y la
solución. Para una solución única también puedes ver la comprobación en el
sistema original. La [guía de la ventana](gui.md) describe las tarjetas y el
[ejemplo resuelto](how-it-works.md) explica el cálculo.

## Resolver una ecuación no lineal

Abre **Métodos Numéricos → Método de Bisección** o **Regula Falsi**. Escribe
`f(x)` y pulsa **Graficar función**. También puedes cargar un ejemplo desde
esa pantalla. Los controles del intervalo se muestran debajo de la gráfica.

Introduce `a`, `b`, la tolerancia y el límite de iteraciones. Comprueba que
la función sea continua en el intervalo y cambie de signo entre sus extremos.
Selecciona el criterio y pulsa **Calcular raíz**. La app muestra el motivo
de parada, la sustitución en la función, el paso a paso y la tabla. Consulta
[los métodos numéricos](bisection.md) para ver la sintaxis y los ejemplos.

## Comprobar y entregar

```bash
python check.py
python -m unittest discover -s tests -v
```

`check.py` muestra las comprobaciones del motor y se detiene ante un resultado
distinto del esperado. Las pruebas unitarias incluyen los casos numéricos y,
con CustomTkinter y una pantalla Tk, la navegación de la app.

Entrega el repositorio. Para reproducir una actividad, indica en qué
herramienta del menú se encuentra y con qué datos se puede probar.
