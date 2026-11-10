# linalg-calculator

Calculadora de Álgebra Lineal y Métodos Numéricos del curso MTM0120 de la
Universidad Americana (UAM). La entrega del curso es este repositorio.

La aplicación de escritorio abre en **Inicio**, con accesos a las once
herramientas agrupadas por tema. Puedes volver al inicio desde el menú lateral
y continuar con los datos que escribiste en cada herramienta.

## Ejecutar la calculadora

Desde la raíz del repositorio, con Python 3.12 o posterior:

```bash
python -m pip install -r requirements-gui.txt
python main.py
```

Si tu instalación de Python no incluye Tkinter, instala también el paquete de
Tk de tu distribución. La [guía de uso](docs/usage.md) explica la entrada de
datos y cómo ejecutar las pruebas.

## Herramientas

| Área | Herramientas |
| --- | --- |
| Sistemas lineales | Eliminación Gaussiana y Gauss–Jordan. Formas escalonadas y pivotes. |
| Matrices | Suma, resta, multiplicación, producto por escalar y transpuesta. Inversa, factorización LU y determinante. |
| Vectores | Suma, resta, producto por escalar y combinaciones lineales. |
| Sistemas numéricos | Conversiones entre bases de 2 a 36 y números romanos. Aritmética romana. |
| Métodos numéricos | Bisección y Regula Falsi, con gráfica, paso a paso y tabla de iteraciones. |

## Organización del repositorio

```text
core/
  scalar.py          Números racionales exactos y su formato
  matrix.py          Matrices y operaciones elementales
  steps.py           Registro de operaciones por filas
  worksheet.py       Matriz de trabajo con registro de sus operaciones
  elimination.py     Reducción a forma escalonada y escalonada reducida
  systems.py         Clasificación y solución de sistemas lineales
  verification.py    Comprobación de las soluciones
  equations.py       Lectura de ecuaciones lineales
  notation.py        Multiplicación implícita compartida
  echelon.py         Propiedades de las formas escalonadas y pivotes
  parametric.py      Solución general de sistemas indeterminados
  inverse.py         Inversa y sistemas resueltos por inversa
  lu.py              Factorización PA = LU y sustituciones
  determinant.py     Determinantes por cofactores y por LU
  vectors.py         Operaciones con vectores de Rⁿ
  bases.py           Conversiones entre bases
  roman.py           Lectura, escritura y aritmética romana
  real_function.py   Lectura y muestreo de funciones reales
  root_bracket.py    Intervalo, criterios de parada y registro compartido
  bisection.py       Estimación de la raíz por punto medio
  regula_falsi.py    Estimación de la raíz por el cruce de la secante
ui/
  presentation.py    Formato de ecuaciones, sustituciones y resultados
gui/
  app.py             Inicio, navegación y selección de herramienta
  theme.py           Colores, tipografías y tema claro u oscuro
  widgets.py         Componentes compartidos
  entry.py           Entrada por coeficientes o ecuaciones
  root_plot.py       Gráfica de funciones, zoom y arrastre
  pages/            Pantallas de cada herramienta
tests/              Pruebas del motor y de la interfaz
docs/               Guías de uso, diseño y referencia
main.py             Punto de entrada de la calculadora
check.py            Comprobaciones del motor
```

## Cómo calcula

Las matrices y los vectores usan `Fraction` para conservar el valor exacto de
cada entrada. Una matriz ofrece operaciones por filas y `Worksheet` registra
cada operación en un `StepLog`. El paso a paso consulta esos estados para
avanzar y retroceder.

La eliminación lleva los pivotes a uno y crea ceros debajo. Gauss–Jordan añade
una pasada hacia arriba. La clasificación compara `rango(A)`, `rango(A|b)`
y el número de incógnitas. Una solución única se comprueba sustituyéndola en el
sistema original. Una solución indeterminada muestra las variables libres y
su familia de soluciones.

La inversa reduce `[A | I]` y comprueba ambos productos con A. LU conserva la
permutación de filas en P y permite resolver `Ly = Pb` y `Ux = y`. El
determinante se calcula por cofactores o a partir de la diagonal de U y el signo
de la permutación. Una combinación lineal de vectores se convierte en un
sistema y reutiliza el mismo solucionador.

Para búsqueda de raíces se usa `float` y las funciones elementales de `math`.
Bisección y Regula Falsi comparten el lector de funciones, el intervalo con
cambio de signo y el registro. En ambos casos la gráfica aparece antes de
introducir el intervalo de resolución. La tabla y el paso a paso se construyen
con las iteraciones calculadas.

El motor usa la biblioteca estándar de Python. CustomTkinter se usa para la
interfaz. Los identificadores del código siguen la convención en inglés y
los comentarios, mensajes y guías se escriben en español.

## Verificar cambios

```bash
python check.py
python -m unittest discover -s tests -v
```

`check.py` comprueba el motor. Las pruebas de la ventana requieren
CustomTkinter y una pantalla Tk.

## Documentación

- [Guía de uso](docs/usage.md)
- [Un sistema resuelto de principio a fin](docs/how-it-works.md)
- [Interfaz de escritorio](docs/gui.md)
- [Bisección y Regula Falsi](docs/bisection.md)
- [Matriz inversa y ejercicios](docs/inverse.md)
- [Decisiones de diseño](docs/design.md)
- [Referencia del código](docs/reference.md)
