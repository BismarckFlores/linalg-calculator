# Interfaz de escritorio con PySide6 y MathLive

Abre la calculadora con `python main.py` después de instalar
`requirements.txt`. **Inicio** y el menú lateral agrupan las
herramientas. El menú lateral usa un icono vectorial por herramienta y
resalta la selección. En Inicio, cada acceso reutiliza el banner de su
herramienta. Haz clic en la tarjeta o usa **Abrir**. Los accesos se muestran
en dos columnas cuando hay espacio.
Cada página se crea al abrirla por primera vez y conserva sus entradas al
cambiar de herramienta. Inicio y cada herramienta tienen un encabezado
ilustrado que sigue el tema activo. El botón junto a **Álgebra Lineal** abre el menú
**Apariencia**. El monitor indica **Automático** y sigue el modo del sistema.
El sol indica **Claro** y la luna, **Oscuro**. El menú marca la opción
seleccionada y la conserva al volver a abrir la aplicación.

Una luz azul difusa nace en la esquina superior izquierda del fondo de puntos
y símbolos matemáticos. Las tarjetas y el menú lateral tienen una superficie
al 75 % de opacidad sobre el patrón desenfocado, con más contraste en modo claro.

## Entrada y resultados

En **Coeficientes** ajusta filas y columnas, edita las celdas o pega una
matriz. Separa las filas con saltos de línea y los coeficientes con punto
y coma. Para una entrada por **Ecuaciones**, escribe una ecuación por
línea y usa **Enter** para agregar otra. Las matrices y los vectores
admiten fracciones. Si falla el editor visual, pulsa **Usar entrada de
texto** en el campo afectado. Los resultados tienen respaldo de texto
automático.

Los métodos y las formas de entrada se eligen con botones segmentados.
En las matrices, **−** y **+** cambian las dimensiones. La matriz A y el
vector b se muestran en paralelo cuando hay espacio, y sus filas se
ajustan juntas.

Cuando la operación tiene una traza, usa **Anterior**, **Siguiente** o
los puntos bajo el procedimiento para navegar. En recorridos largos,
los puntos se sustituyen por un contador. **Ver todos los pasos** despliega
la traza completa y la rueda desplaza la página. Cada paso conserva su
encabezado numerado en ambas vistas. MathLive muestra las operaciones y las
matrices en LaTeX, con un divisor continuo en las matrices aumentadas. Los
resúmenes agrupan los valores y las comprobaciones se separan por ecuación.
Las tablas permiten desplazarse para inspeccionar todas las
columnas. La notación científica se muestra como `2.5 × 10⁻⁶`. Editar una
entrada invalida el cálculo anterior.

En cada herramienta, **Limpiar** o **Ctrl+Mayús+Supr** borra las entradas y
quita los resultados. Las matrices quedan en cero y conservan sus dimensiones.
En las herramientas de búsqueda de raíces también se quita la gráfica. El botón **Limpiar**
del teclado matemático borra el campo que estás editando.

| Herramienta | Controles y resultados |
| --- | --- |
| Eliminación Gaussiana | Gauss o Gauss–Jordan, entrada por coeficientes o ecuaciones, reducción, rangos, soluciones y comprobación. |
| Formas Escalonadas | Matriz o ecuaciones, cinco propiedades, posiciones pivote y libres, y recorrido de reducción. |
| Operaciones Matriciales | Suma, resta, producto, escala y transpuesta con matrices de tamaño editable. |
| Matriz Inversa | Invertir A o resolver Ax = b, reducción de [A \| I] y verificación exacta. |
| Factorización LU | Factorizar o resolver, pivoteo parcial, modo estricto, traza y sustituciones. |
| Determinante | Cofactores o LU, costo estimado, desarrollo y comparación cuando el orden lo permite. |
| Operaciones Vectoriales | Suma, resta, escala y combinación lineal. Para combinar, escribe un generador por línea. |
| Conversiones | Decimal, bases de 2 a 36 y romanos en ambos sentidos, con tabla y conversión inversa. |
| Aritmética Romana | Suma, resta y producto, lectura por piezas y suma repetida opcional. |
| Método de Bisección | Punto medio, criterios configurables, gráfica, tabla y procedimiento. |
| Regula Falsi | Cruce de la secante, cambio relativo o residuo, gráfica, tabla y procedimiento. |
| Newton–Raphson | Derivación automática, selección de x₀ en la gráfica, cambio absoluto, tabla y sustitución por iteración. |
| Derivadas e integrales | Derivada simbólica con evaluación opcional, antiderivada con constante e integral definida exacta. |

### Derivadas e integrales

Abre **Cálculo → Derivadas e integrales** y escribe una función de `x`.
Con **Derivada**, deja el punto vacío para obtener la fórmula o ingrésalo
para ver también el valor. Por ejemplo, para `x^3 - x - 2` en `1.5` se
obtiene `3x² − 1` y `23/4`.

Con **Integral indefinida**, la antiderivada incluye `+ C`. Con
**Integral definida**, indica dos límites reales finitos. La función
debe ser real y continua en el intervalo. Por ejemplo, `x^2` de `0` a
`1` da `1/3`. Si el motor no puede verificar el dominio u obtener
un resultado simbólico, la página muestra un mensaje.

### Newton–Raphson

1. En **Métodos Numéricos → Newton–Raphson**, escribe `f(x)` y pulsa
   **Graficar función** para localizar visualmente un cruce con el eje x.
2. Haz clic en la gráfica para seleccionar y marcar **x₀**, o escribe
   su valor en **Aproximación inicial x₀**. La vista ampliada también
   permite seleccionarlo.
3. Ajusta la tolerancia y el máximo de iteraciones. Pulsa **Calcular
   raíz** y consulta el motivo de parada, la sustitución en cada paso
   y la tabla con el cambio absoluto `|xₙ₊₁ − xₙ|`. Al avanzar en el
   paso a paso, la tabla selecciona la fila de esa iteración. Puedes
   cambiar el formato numérico y la cantidad de decimales.

**Cargar ejemplo de Semana 13** prepara `x^3 - x - 2`, `x₀ = 1.5`
y tolerancia `0.000001`. Grafica y calcula para obtener
`x ≈ 1.5213797068` en tres iteraciones. Cambia el máximo a uno
para comprobar la otra condición de parada.

## Editor de funciones

En **Métodos Numéricos** escribe con el teclado físico o pulsa **Teclado**
para usar los símbolos Qt. `^` abre el exponente, `/` crea una fracción y
la flecha derecha sale del exponente o del denominador. Puedes pegar
expresiones como `5x^3` o `sqrt(x+1)/2`. El botón **log** coloca el cursor en
la base del logaritmo. Pulsa **Tab** para pasar al argumento. El botón
**|x|** inserta las barras de valor absoluto. El teclado también incluye
las seis funciones trigonométricas y sus inversas. El editor acepta el
exponente sobre el nombre de la función, como en `cos^2(2x)`.
**Graficar función** muestra los
controles de intervalo y tolerancia. El zoom con la rueda y el arrastre
permiten inspeccionar el intervalo. **Maximizar** amplía la gráfica sobre
la misma ventana. Consulta [los métodos numéricos](bisection.md) para ver
la sintaxis y los criterios.

MathLive 0.111.4, sus fuentes y los avisos de licencia se cargan desde
`desktop/assets/vendor/`. La aplicación funciona sin conexión tras
instalar sus dependencias.

La [guía heredada](legacy-gui.md) conserva la descripción de la versión
CustomTkinter para consulta histórica.
