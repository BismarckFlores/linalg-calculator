# Interfaz de escritorio con PySide6 y MathLive

Abre la calculadora con `python main.py` después de instalar
`requirements.txt`. **Inicio** y el menú lateral agrupan las once
herramientas. Las tarjetas se muestran en dos columnas cuando hay espacio.
Cada página se crea al abrirla por primera vez y conserva sus entradas al
cambiar de herramienta. El botón junto a **Álgebra Lineal** cambia el tema.

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
los puntos se sustituyen por un contador. **Ver todos los pasos** reúne
la traza. Las tablas permiten desplazarse para inspeccionar todas las
columnas. Editar una entrada invalida el cálculo anterior.

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

## Editor de funciones

En **Métodos Numéricos** escribe con el teclado físico o pulsa **Teclado**
para usar los símbolos Qt. `^` abre el exponente, `/` crea una fracción y
la flecha derecha sale del exponente o del denominador. Puedes pegar
expresiones como `5x^3` o `sqrt(x+1)/2`. **Graficar función** muestra los
controles de intervalo y tolerancia. El zoom con la rueda y el arrastre
permiten inspeccionar el intervalo. **Maximizar** abre la gráfica en una
ventana separada. Consulta [los métodos numéricos](bisection.md) para ver
la sintaxis y los criterios.

MathLive 0.111.4, sus fuentes y los avisos de licencia se cargan desde
`desktop/assets/vendor/`. La aplicación funciona sin conexión tras
instalar sus dependencias.

La [guía heredada](legacy-gui.md) conserva la descripción de la versión
CustomTkinter para consulta histórica.
