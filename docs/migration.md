# Migración a PySide6 y MathLive

PySide6 es la interfaz de las once herramientas. El punto de entrada es
`main.py` y las dependencias están en `requirements.txt`.
Consulta [la guía de la interfaz](gui.md) para ejecutar y usar la versión actual.

## Estado de la migración

- Fase 1. Regula Falsi reutiliza la página de Bisección y el motor de
  intervalos. Las pruebas de Qt están en `tests/test_qt_roots.py`.
  El informe editable y el PDF se conservan localmente en `deliverables/out/`.
- El primer merge de Regula Falsi se publicó en `main`. La rama de desarrollo
  incorpora ese estado y el commit que retiró los informes de la versión publicada.
  Ambos archivos siguen excluidos por `.gitignore`.

### Auditoría funcional

| Herramienta | Estado en Qt al primer merge | Criterio de equivalencia |
| --- | --- | --- |
| Eliminación Gaussiana | Entrada por ecuaciones y solución básica | Coeficientes y ecuaciones, Gauss y Gauss–Jordan, traza, familia paramétrica, despejes y comprobación. |
| Formas Escalonadas | Pendiente | Analizar cinco propiedades, ubicar fallos y pivotes, reducir con traza y reconocer sistemas aumentados. |
| Operaciones Matriciales | Pendiente | Operar matrices rectangulares con tamaños compatibles, cinco operaciones y resultado exacto. |
| Matriz Inversa | Pendiente | Reducir la aumentada con la identidad, comprobar ambos productos y resolver con A⁻¹b. |
| Factorización LU | Pendiente | Factores P, L y U, opciones de pivoteo y singularidad, traza, sustituciones y verificación. |
| Determinante | Cofactores para 2 × 2 | Admitir matrices cuadradas de distinto orden, estimar costo, mostrar menores y diagonal de U, y contrastar métodos. |
| Operaciones Vectoriales | Suma con detalle por componente | Añadir resta, escala y combinación, con clasificación, pasos y comprobación. |
| Conversiones | Decimal a binario | Convertir en ambos sentidos, bases 2 a 36 y romano, con tablas y comprobación. |
| Aritmética Romana | Pendiente | Sumar, restar y multiplicar, mostrar piezas y suma repetida, y distinguir resultados fuera de rango. |
| Bisección | Cálculo, criterios, gráfica, tabla y pasos | Recuperar los ejemplos de clase, la ampliación, la precisión de la tabla y el detalle del intervalo. |
| Regula Falsi | Entrega publicada | Conservar el flujo validado y aplicar las mejoras compartidas de gráfica y tabla. |

El catálogo de referencia y las interacciones heredadas están descritos en
[la guía de CustomTkinter](legacy-gui.md). La auditoría conserva las APIs de
`core/`. Sus módulos separan cálculos con datos y trazas propios, y el
mayor solapamiento estaba en los formularios y en la presentación de la
interfaz. La consolidación se concentra en los componentes Qt compartidos.

### Validación de la migración

Las once herramientas ya están registradas en el catálogo Qt. La interfaz
usa un formulario compartido para las operaciones de álgebra, un recorrido
común para matrices y raíces y la misma tabla para conversiones e
iteraciones. El motor Python conserva sus APIs. Las pruebas gráficas
validaron los modos principales, la navegación, la invalidación de
resultados, la ampliación de la gráfica y la precisión de la tabla.

El primer merge fue `a1e3fb4`. El commit `b106fce` retiró el Word y el PDF
de la versión publicada de `main`. Las copias siguen en el historial de ese
primer merge y los archivos de trabajo se conservan localmente, ignorados
por Git.

La interfaz heredada ocupaba 19 módulos Python. La interfaz final usa 11
módulos Python, incluidos los adaptadores de MathLive y el teclado. Las
páginas reutilizan `ToolPage`, `StepView`, `MatrixInput` y `ResultTable`.
Bisección y Regula Falsi comparten `RootBracketPage` y `FunctionPlot`.
Se mantuvieron las APIs de `core/` y se retiró la dependencia de CustomTkinter.
El segundo merge integra este reemplazo desde `Bismarck/ui-revamp`.

La validación final incluyó una instalación limpia, `pip check`,
`python check.py` y la suite de 46 pruebas. Se repitió la suite con la
red aislada en Linux. El teclado físico, el pegado, el teclado Qt y el
cambio de tema se comprobaron en una sesión gráfica.

### Fidelidad visual

Se compararon las once pantallas de entrada con la versión de CustomTkinter
del commit `b106fce`. Qt recuperó los selectores segmentados, los controles
horizontales de tamaño y la disposición compacta de los formularios. En
Gauss, el planteamiento, el recorrido, el sistema equivalente y la
comprobación se muestran en tarjetas separadas.

Los resultados usan bloques de lectura que crecen con el contenido.
MathLive sigue a cargo de la entrada editable. El paso a paso conserva
la banda de cada operación, las matrices y la separación de la columna
aumentada. Las gráficas tienen ejes independientes y el tema puede seguir
al sistema o fijarse en claro u oscuro.

El fondo de trabajo combina puntos y símbolos matemáticos con una luz
azul difusa en la esquina superior izquierda en ambos temas. Las tarjetas
y la barra lateral muestran el patrón desenfocado bajo una capa al 75 %
de opacidad. El modo claro refuerza el contraste del patrón. MathLive
mantiene la nitidez de las expresiones.

La rama de migración se integró en `main` y se retiró. El desarrollo
continúa en `main`.

### Organización posterior

El motor se agrupó en álgebra lineal, sistemas numéricos y métodos
numéricos. Cada área reúne sus utilidades compartidas en `handlers/`.
La aritmética exacta y la notación siguen disponibles en la raíz de `core/`
para todos los grupos. Se conservaron las rutas de importación anteriores.

En Qt, `desktop/core/` contiene los formularios, controles y manejadores
compartidos. `desktop/tools/` reúne los módulos de las once herramientas
por área. El menú Apariencia usa iconos para los tres modos y marca la
opción seleccionada.

En `main` se verificaron `check.py`, las 49 pruebas de la suite y el
menú de tema con ratón y teclado en Linux.
