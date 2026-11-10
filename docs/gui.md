# Interfaz de escritorio

La calculadora usa CustomTkinter. Desde la raíz del repositorio:

```bash
pip install -r requirements-gui.txt
python main.py
```

## Inicio y navegación

**Inicio** muestra las once herramientas con su descripción y un botón
**Abrir**. Las tarjetas se agrupan igual que el menú lateral. Se muestran
en una columna cuando el espacio es estrecho y en dos a partir de 720
píxeles disponibles. Cada pantalla se crea al abrirla por primera vez y
conserva lo que escribiste al cambiar de herramienta.

| Grupo | Herramienta | Qué hace |
| --- | --- | --- |
| Sistemas Lineales | Eliminación Gaussiana | Resuelve `Ax = b` por Gauss o Gauss–Jordan y muestra la clasificación, las operaciones y la comprobación. |
| Sistemas Lineales | Formas Escalonadas | Analiza la forma de una matriz, la reduce y localiza sus pivotes. |
| Matrices | Operaciones Matriciales | Suma, resta, producto, multiplicación por escalar y transpuesta. |
| Matrices | Matriz Inversa | Calcula `A⁻¹` y resuelve `Ax = b` con ella. |
| Matrices | Factorización LU | Descompone `PA = LU` y resuelve sistemas por sustitución. |
| Matrices | Determinante | Calcula por cofactores o por LU y compara los métodos. |
| Vectores | Operaciones Vectoriales | Suma, resta, producto por escalar y combinación lineal. |
| Sistemas Numéricos | Conversiones | Convierte entre decimal, bases de 2 a 36 y números romanos. |
| Sistemas Numéricos | Aritmética Romana | Suma, resta y multiplica numerales romanos. |
| Métodos Numéricos | Método de Bisección | Aproxima una raíz con el punto medio de un intervalo. |
| Métodos Numéricos | Regula Falsi | Aproxima una raíz con el cruce de una secante. |

`GROUPS` en `gui/app.py` define el orden y la descripción que usan Inicio y
el menú. La entrada `HOME` abre el catálogo. Los títulos de grupo son
etiquetas. La rueda mueve el menú lateral si sus filas no caben, y la fila
activa se mantiene visible al seleccionar una página o redimensionar.

## Entrada de matrices y sistemas

**Coeficientes** muestra una cuadrícula para A y, cuando corresponde, una
columna para b. Los controles ajustan filas y columnas. b sigue el número de
filas de A. **Ecuaciones** lee una ecuación por línea y conserva los nombres
de incógnitas encontrados. Los valores se guardan como fracciones exactas.
La [guía de uso](usage.md#ecuaciones) enumera la sintaxis.

`gui/entry.py` comparte la entrada entre las páginas. Cuando se analiza una
matriz sin b, el selector **Es una matriz aumentada [ A | b ]** permite
indicar si la última columna contiene términos independientes. En modo
Ecuaciones la separación ya se deduce de la entrada. Si hay un error,
el aviso indica la línea o celda.

### Eliminación Gaussiana y Gauss–Jordan

| Parte del ejercicio | Tarjeta |
| --- | --- |
| Datos | **Ecuación matricial A x = b** presenta A, las incógnitas y b. |
| Matriz aumentada inicial | Primer estado de **Paso a paso**. |
| Operaciones por filas | **Paso a paso** presenta las operaciones y sus matrices. |
| Sistema equivalente | La matriz final de la reducción escrita como ecuaciones. |
| Clasificación | **Resultado** muestra los dos rangos, las incógnitas y columnas pivote o libres. |
| Solución | Valores, familia paramétrica o fila contradictoria. |
| Verificación | **Comprobación en el sistema original** muestra `A · x` y la sustitución ecuación por ecuación para una solución única. |

Con Gauss y solución única aparece el despeje por sustitución hacia atrás.
Con Gauss–Jordan los pivotes quedan solos en su columna y los valores se
leen directamente. Para infinitas soluciones, **Solución general** expresa
cada variable básica en términos de las libres, por ejemplo `x = -2 + z`
y `y = 8 - 2z`. Esa familia se obtiene de la forma reducida aunque se
haya seleccionado Gauss. Solo se cuentan como columnas pivote del sistema
las columnas de A. Un pivote en b explica una fila contradictoria.

Los botones **Anterior**, **Siguiente**, los puntos y **Ver todos los pasos**
navegan la traza guardada. Las fracciones se apilan en matrices, operaciones
y bloques de trabajo. El signo de una fracción negativa queda a la altura
de la barra. Se conservan paréntesis cuando hacen falta, como en `3(-17/12)`.
Los productos se muestran como `2y` o `1(29)`. Un resultado ancho permite
desplazamiento horizontal y deja fijo el encabezado.

### Formas escalonadas, operaciones e inversa

**Formas Escalonadas** informa qué propiedades satisface la matriz original
y cuáles fallan. El recorrido muestra su reducción y el resultado señala
los pivotes. Las formas y sus condiciones se detallan en la
[referencia de echelon](reference.md#coreechelonpy).

**Operaciones Matriciales** ajusta la entrada a la operación. Para sumar
o restar se necesitan tamaños iguales. Para multiplicar, las columnas de A
deben coincidir con las filas de B. La transpuesta intercambia filas y
columnas.

**Matriz Inversa** reduce `[A | I]` y comprueba los dos productos con la
matriz original. **Resolver A x = b** calcula `x = A⁻¹b`. Los modos
conservan sus entradas. La [guía de inversa](inverse.md) incluye el
teorema, sus condiciones y ejercicios.

## Vectores

Escribe las componentes separadas por comas, punto y coma o espacios,
por ejemplo `1, -2, 3` o `(1 -2 3)`. La dimensión es el número de
componentes. Usa punto para decimales, porque `2,5` representa dos
componentes. Un aviso informa las dos dimensiones si son incompatibles.

**u + v**, **u − v** y **k · u** se muestran como columnas y en una línea
de resultado. El detalle presenta cada componente, como
`u₃ + v₃ = 3 - 1/2 = 5/2`. La presentación convierte `2 - (-3)` en
`2 + 3` y conserva los paréntesis al multiplicar, como `(1/2)(-4)`.

**Combinación lineal** recibe b y un vector vᵢ por línea.

| Tarjeta | Contenido |
| --- | --- |
| Planteamiento | Ecuación `c₁[v₁] + c₂[v₂] = [b]` en grupos de cuatro vectores y sistema por componentes. |
| Paso a paso | Reducción de `[v₁ … vₖ \| b]` con el mismo recorrido de eliminación. |
| Resultado | Rangos, escalares y combinación. Verde si hay una, naranja si hay infinitas y rojo si no existe. |
| Comprobación | Multiplica cada vector por su escalar y suma por columnas y componentes. |

Cuando hay infinitas combinaciones se muestra la familia y se comprueba
un ejemplo con los escalares libres en cero. Si no hay combinación se
indica la fila contradictoria. `core/vectors.py` llama al mismo
solucionador de sistemas que usa Eliminación Gaussiana.

## Conversiones

**Decimal → otra base** divide sucesivamente el valor absoluto por la
base. Cada fila muestra el cociente, el residuo y su dígito, por ejemplo
`43 = 2 · 21 + 1`. Un residuo de 14 en base 16 se escribe `E`. El
resultado se lee de abajo hacia arriba y se verifica con la conversión
inversa.

**Otra base → decimal** desarrolla una combinación de potencias y muestra
una tabla con posiciones, valores y aportes. Las expresiones largas se
parten en grupos de seis términos.

```text
2B₁₆ = 2·16¹ + 11·16⁰
     = 2·16 + 11·1
     = 32 + 11
     = 43
```

Los botones incluyen binario, octal, hexadecimal y **Otra base** (2 a 36).
Se usan `A` a `Z` para valores de 10 a 35. Los números son enteros de
hasta 32 dígitos y se pueden agrupar con espacios. Si hay un carácter
inválido, el aviso indica qué cifras admite la base. El signo inicial se
aplica a toda la magnitud. `+` es opcional y `-0` se normaliza a `0`.
Por ejemplo, `-2B₁₆ = -(32 + 11) = -43`. El signo queda fuera del límite de
dígitos. Esta representación usa signo y magnitud. El ejemplo inicial
representa 43 en la base activa y cambia con ella hasta editarlo.

`core/bases.py` realiza las divisiones y las sumas de potencias con
aritmética entera. **Romano** usa otra regla. Para escribir un numeral,
toma la pieza más grande que cabe en el valor restante y repite. Al leer,
suma las piezas y reconoce los seis pares de resta. Los valores romanos
admitidos van de 1 a 3999.

## Determinante

La entrada muestra una estimación de trabajo según el orden de la matriz
antes de elegir método. Por ejemplo, para 4 × 4 estima 40 multiplicaciones
por cofactores y 20 por LU. Los cofactores permiten seguir a mano matrices
pequeñas. El costo crece rápidamente con el orden.

**Cofactores** elige la fila o columna con más ceros para omitir menores.
Cada término muestra la entrada, el signo `(−1)ⁱ⁺ʲ`, el menor y el
producto. Desarrolla los menores de forma recursiva hasta `ad − bc`.
La vista cuenta los sumandos y limita el desglose a 30. Informa qué
niveles se muestran y da el valor de los menores que no expande. El
límite evita que la altura del lienzo sobrepase la que admite Tk.

**LU** reutiliza la factorización de `core/lu.py`. Presenta la reducción y
los factores, luego multiplica la diagonal de U. Si hubo intercambios,
muestra `PA = LU` y aplica `(−1)^k` al producto. Cuando el tamaño lo
permite, el otro método comprueba el resultado. La comprobación por
cofactores se omite por encima de 7 × 7 y la expansión por cofactores
se limita a 8 × 8.

## Factorización LU

**Factorizar** conserva los multiplicadores de las operaciones en L y
muestra la reducción. Presenta P si se intercambiaron filas, el orden
de las filas, el rango, la invertibilidad y la comparación exacta
`PA = LU`. Si no hay permutación, muestra `A = LU`.

**Resolver A x = b** presenta `Ly = Pb` de arriba hacia abajo y `Ux = y`
de abajo hacia arriba. Las líneas muestran la ecuación, valores sustituidos,
constante trasladada y resultado. Si el coeficiente del pivote requiere
división, añade el paso, por ejemplo `-2y = -8` y `y = 4`. Después comprueba
el sistema original.

**Pivoteo parcial** elige el mayor valor absoluto de la columna. De forma
predeterminada solo se intercambia para evitar un pivote cero.
**Modo estricto** rechaza una matriz singular e indica la columna del
pivote faltante. Fuera de ese modo se puede mostrar la factorización
con ceros en la diagonal. Para resolver con LU se requiere una matriz
invertible. Eliminación Gaussiana clasifica el caso singular.

## Aritmética romana

**Suma**, **Resta** y **Multiplicación** leen los operandos por piezas.
Por ejemplo, `XIV = X + IV = 14`. Los pares de resta son IV, IX, XL,
XC, CD y CM. Se calcula con los valores y se presenta el numeral junto
con su valor decimal. Una lectura final verifica el numeral resultante.

**Notación de suma** aparece en Multiplicación y está activa al entrar.
Expande `X × V` como cinco sumandos X. Si hay más de 30 sumandos,
muestra los primeros 30 y señala el total. Las letras se normalizan a
mayúsculas. Una entrada como `IIII` indica la escritura canónica `IV`.
Para cero, negativos o valores mayores de 3999 se muestra el valor
decimal y el motivo por el que queda fuera del rango romano.

## Bisección y Regula Falsi

Primero se grafica f(x) y luego se muestran los campos de intervalo,
tolerancia y máximo de iteraciones. La gráfica compartida admite zoom
con botones o rueda, arrastre, restablecimiento y vista ampliada.
La [guía de raíces](bisection.md) explica los criterios y los ejemplos.

`RootBracketPage` usa `_draw_walk` para crear `StepWalker`, con un título y
un estado por iteración más el inicial. `LinkButton` comparte el estilo de
las acciones de gráfica, ayuda y paginación. La tabla usa `SegmentedControl`
para **Decimal / Automático** y `Stepper` para seleccionar de 0 a 17
decimales (5 por defecto). Solo las columnas están dentro de `Wide`.
Al cambiar la vista o página, `Wide.refresh()` recalcula si hace falta
desplazamiento horizontal. Los controles permanecen en su lugar.

## Organización de la interfaz

| Componente | Responsabilidad |
| --- | --- |
| `gui/app.py` | Ventana, Inicio, menú, tema y selección de páginas. |
| `gui/theme.py` | Colores como pares claro/oscuro y tipografías. Las fuentes se cargan después de abrir la ventana. |
| `gui/widgets.py` | Tarjetas, matrices, expresiones, fracciones, selectores y navegación compartida. |
| `gui/entry.py` | Cuadrículas de entrada y lectura de ecuaciones. |
| `gui/root_plot.py` | Dibujo y transformación de coordenadas de la gráfica. |
| `gui/pages/` | Entrada y estado de cada herramienta. |
| `ui/presentation.py` | Texto de ecuaciones, clasificación, sustitución y comprobación. |
| `core/` | Cálculos, evaluación de funciones y muestras para dibujar. |

La ventana usa el color azul `#0071e3`, las tarjetas redondeadas y el menú
del diseño de referencia en Figma. Las operaciones se ejecutan con el
motor Python del repositorio. Las páginas se construyen bajo demanda y las
tarjetas de resultado se invalidan al editar su entrada.

### Detalles de Tkinter

- `Application._wire_wheel` aplica unidades verticales de 30 píxeles al
  menú y a la página. Los valores predeterminados de CustomTkinter
  difieren entre Windows y Linux. Los campos con scroll propio lo
  conservan y la gráfica consume la rueda para hacer zoom.
- El divisor de dos píxeles evita el problema de `CTkFrame` cuando su
  ancho de un píxel impide que se dibuje.
- Una barra con `rowspan` separa A y b. Un marco por fila forzaría la
  altura predeterminada de `CTkFrame`.
- El encabezado de una matriz va fuera de la cuadrícula. Así un título
  largo conserva el ancho de las celdas.
- El Canvas usa un color efectivo. `theme.on_change` avisa cuándo volver
  a dibujar lo que depende del tema.
