# Prueba de interfaz de escritorio

La rama `Bismarck/ui-revamp` incluye una prueba de concepto con PySide6.
Conserva la distribución con **Inicio**, menú lateral agrupado, insignias y
tarjetas. Cada sección tiene una herramienta que usa el motor de la calculadora.
El teclado usa los botones Qt de la calculadora. El teclado y el editor
siguen el tema claro u oscuro de la ventana.

## Ejecutar la prueba

Desde la rama `Bismarck/ui-revamp`, [crea y activa el entorno virtual](usage.md#preparar-el-entorno-virtual).
Luego ejecuta estos comandos desde la raíz del repositorio.

```bash
pip install -r requirements-poc.txt
python revamp.py
```

La calculadora de CustomTkinter se sigue abriendo con `python main.py`.

## Qué probar

| Sección | Herramienta de muestra | Resultado con los datos iniciales |
| --- | --- | --- |
| Sistemas lineales | Eliminación gaussiana por ecuaciones | `x = 2`, `y = 1` |
| Matrices | Determinante de una matriz 2 × 2 | `−2` |
| Vectores | Suma de dos vectores | `(5, −2, 5/2)` |
| Sistemas numéricos | Conversión de decimal a binario | `43 → 101011` |
| Métodos numéricos | Bisección por ancho del intervalo | `x ≈ 1.414215` |

Las cinco herramientas usan MathLive para las entradas y los resultados
matemáticos. En Gauss, escribe una ecuación por línea y pulsa **Enter** para
agregar otra. En Determinante, pulsa una celda para editarla. Puedes pegar una
matriz con una fila por línea y sus dos valores separados por punto y coma
o espacios. En Vectores, separa las componentes con comas.

En **Bisección**, selecciona **Fracción con raíz** para ver una fracción
apilada. Escribe con el teclado físico o usa los botones de **Teclado**.
`^` abre el exponente, `/` crea una fracción y la flecha derecha sale del
exponente o del denominador. También puedes pegar expresiones lineales como
`5x^3` o `sqrt(x+1)/2`. Al escribir `(`, el cursor queda entre los paréntesis.
Pulsa **Graficar función** antes de ajustar el intervalo y la tolerancia.
Puedes hacer zoom con la rueda o los botones y desplazar la gráfica arrastrando.
Con el intervalo del ejemplo, **Calcular raíz** devuelve `x ≈ 3` y muestra la
sustitución en la función y la tabla de iteraciones.

Si MathLive falla, **Usar entrada de texto** activa el respaldo de cada
campo. Los resultados matemáticos pasan a texto automáticamente si su vista
falla. La gráfica y la tabla de iteraciones se muestran en Qt.

## Cómo se integra

La ventana, los formularios y la gráfica usan Qt. Las dos interfaces comparten
los colores, radios y familias tipográficas en `ui/theme_tokens.py`.
MathLive se ejecuta en una vista Qt WebEngine dentro del campo visual. Las
teclas Qt le envían comandos de edición para conservar el cursor y la
selección. El campo devuelve la expresión en texto al mismo lector de
la herramienta. Las vistas del editor local comparten el proceso de
renderizado de Qt WebEngine.
En Linux, el editor usa renderizado por software para evitar que Qt vuelva a
crear la superficie de la ventana al entrar por primera vez en Bisección.
MathLive 0.111.4 y sus fuentes se cargan desde `revamp_poc/assets/vendor/`, que
incluye los avisos de licencia. La prueba se puede abrir sin conexión una vez
instaladas las dependencias.
