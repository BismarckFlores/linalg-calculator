# Prueba de interfaz de escritorio

La rama `Bismarck/ui-revamp` incluye una prueba de concepto con PySide6.
Conserva la distribución con **Inicio**, menú lateral agrupado, insignias y
tarjetas. Cada sección tiene una herramienta que usa el motor de la calculadora.
El editor y el teclado siguen el tema claro u oscuro de la ventana.

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

En **Bisección**, selecciona **Fracción con raíz** para ver la fórmula con una
raíz y una fracción apilada. Abre **Teclado** para insertar símbolos y estructuras,
o cambia a **Texto** para escribir con la sintaxis de la calculadora.
Pulsa **Graficar función** antes de ajustar el intervalo y la tolerancia.
Puedes hacer zoom con la rueda o los botones y desplazar la gráfica arrastrando.
Con el intervalo del ejemplo, **Calcular raíz** devuelve `x ≈ 3` y muestra la
sustitución en la función y la tabla de iteraciones.

El modo visual se prueba en Bisección con la variable `x`, potencias,
fracciones, raíz cuadrada y las funciones elementales admitidas por el lector.
Los otros módulos de la prueba usan los controles de texto o tabla de Qt.

## Cómo se integra

La ventana, los formularios y la gráfica usan Qt. Las dos interfaces comparten
los colores, radios y familias tipográficas en `ui/theme_tokens.py`.
MathLive se ejecuta en una vista Qt WebEngine dentro del campo visual y convierte la entrada a
texto para el mismo lector de funciones y el mismo algoritmo de Bisección.
MathLive 0.111.4 y sus fuentes se cargan desde `revamp_poc/assets/vendor/`, que
incluye los avisos de licencia. La prueba se puede abrir sin conexión una vez
instaladas las dependencias.
