# linalg-calculator

Calculadora de Álgebra Lineal y Métodos Numéricos del curso MTM0120 de la
Universidad Americana (UAM). La entrega del curso es este repositorio.

La aplicación de escritorio usa PySide6 y MathLive. Desde **Inicio** se
puede acceder a las once herramientas. Los recursos matemáticos se cargan
localmente.

## Ejecutar la calculadora

Usa Python 3.12 o posterior y [activa un entorno virtual](docs/usage.md#preparar-el-entorno-virtual).
Desde la raíz del repositorio, ejecuta estos comandos.

```bash
pip install -r requirements.txt
python main.py
```

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
  scalar.py, notation.py     Aritmética exacta y notación global
  linear_algebra/           Sistemas, formas escalonadas, inversa, LU, determinante y vectores
    handlers/               Matrices, ecuaciones, reducción y trazas compartidas
  number_systems/           Conversiones de bases y aritmética romana
    handlers/               Normalización de numerales
  numerical_methods/        Bisección y Regula Falsi
    handlers/               Lectura de funciones y búsqueda por intervalo
ui/
  presentation.py           Formato de resultados independiente de Qt
  theme_tokens.py           Paleta, radios y tipografía
desktop/
  window.py                 Ventana, Inicio y navegación
  core/                     Formularios, tarjetas y MathLive compartidos
    handlers/               Preferencias de tema y comunicación con MathLive
  tools/
    registry.py             Registro de las once herramientas
    linear_algebra/         Páginas de matrices, sistemas y vectores
    number_systems/         Páginas de conversión y aritmética romana
    numerical_methods/      Páginas de Bisección y Regula Falsi
  assets/                   Editor MathLive local, fuentes, iconos y licencias
tests/                      Pruebas del motor y de la interfaz
docs/                       Guías de uso, diseño y referencia
main.py                     Punto de entrada de la calculadora
check.py                    Comprobaciones del motor
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

El motor usa la biblioteca estándar de Python. La interfaz usa PySide6 y MathLive en Qt WebEngine. Los identificadores del código siguen la convención en inglés y
los comentarios, mensajes y guías se escriben en español.

## Verificar cambios

```bash
python check.py
python -m unittest discover -s tests -v
```

`check.py` comprueba el motor. Las pruebas de la ventana requieren
PySide6 y una sesión gráfica.

## Documentación

- [Guía de uso](docs/usage.md)
- [Un sistema resuelto de principio a fin](docs/how-it-works.md)
- [Interfaz de escritorio](docs/gui.md)
- [Bisección y Regula Falsi](docs/bisection.md)
- [Matriz inversa y ejercicios](docs/inverse.md)
- [Decisiones de diseño](docs/design.md)
- [Referencia del código](docs/reference.md)
- [Historial de la migración a PySide6](docs/migration.md)
