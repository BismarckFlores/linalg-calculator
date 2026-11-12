# Migración a PySide6 y MathLive

PySide6 es la interfaz de escritorio. El punto de entrada es
`main.py` y las dependencias están en `requirements.txt`.
Consulta [la guía de la interfaz](gui.md) para ejecutar y usar la versión actual.

## Estado de la migración

- **Métodos Abiertos** reúne Newton–Raphson y Secante en una herramienta
  de Qt. Los dos métodos tienen un ejemplo guiado de Semana 13, la
  práctica integradora, selección de puntos en la gráfica, traza, tabla
  y parada por cambio absoluto o máximo de iteraciones.

- Se agregó **Derivadas e integrales** al catálogo Qt con derivación
  simbólica, evaluación opcional, antiderivada e integral definida.
  Se verificaron los tres modos, la navegación, la invalidación al
  editar, los errores, la limpieza y ambos temas.

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

### Incidencias en Windows

Se reportaron campos de MathLive encima de la gráfica ampliada, un icono
genérico en la barra de tareas y una recreación aparente de la ventana al
abrir una herramienta desde Inicio.

En Linux con X11, la primera apertura de Bisección cambió el identificador
nativo de la ventana con el renderizado predeterminado. Con el renderizado
por software se abrió cada una de las once herramientas sin ese cambio.
La corrección aplica el renderizado por software también en Windows y
registra la identidad de la aplicación antes de crear la ventana. La gráfica
ampliada oculta las vistas visibles de MathLive y las restaura con sus
valores al cerrar con el botón o con Escape.

Se comprobó el arranque y la navegación por las once herramientas en Linux
con X11. Queda pendiente verificar los tres casos en Windows, incluida la
identidad de la aplicación en la barra de tareas.

### Teclado de funciones

El teclado incorpora una plantilla de logaritmo con base editable y usa
barras para el valor absoluto. Se verificaron en Linux el avance con Tab,
la exportación de ambas plantillas y su evaluación. Las expresiones de
texto `log(x)`, `log10(x)` y `abs(x)` conservan su significado.

### Encabezados ilustrados

Inicio y las once herramientas usan un encabezado común con ilustraciones
SVG locales. Se revisaron los doce encabezados en los temas claro y oscuro,
con ventanas de 960 y 1180 píxeles de ancho. Pasaron `check.py` y las 52
pruebas de la suite.

### Notación trigonométrica

El editor y el motor admiten las seis funciones trigonométricas y sus
inversas en radianes. Se verificaron en Regula Falsi los doce botones del
teclado y en Bisección la gráfica de una función con arcoseno y una potencia
de coseno. Pasaron `check.py` y las 55 pruebas de la suite.

### Limpieza de entradas

Las once herramientas tienen una acción para limpiar las entradas y
quitar los resultados. Las matrices conservan sus dimensiones y quedan
en cero. El teclado matemático puede limpiar el campo activo. Se verificó
el botón en las once herramientas y el atajo con entradas Qt y MathLive.
Pasaron `check.py` y las 56 pruebas de la suite.

### Iconos del menú lateral

El menú lateral usa SVG para Inicio y las once herramientas. Se verificaron
el contraste y el estado de selección en ambos temas y el renderizado a
escalas 1× y 2×. Pasaron `check.py` y las 56 pruebas de la suite.

### Accesos ilustrados en Inicio

Los once accesos de Inicio reutilizan la ilustración de su herramienta.
Se comprobó la distribución en una y dos columnas, ambos temas y la
apertura con clic en la tarjeta o con el botón Abrir mediante el teclado.
Pasaron `check.py` y las 56 pruebas de la suite.

### Ilustraciones de Cálculo

El banner de Derivadas e integrales combina una tangente y un área
sombreada bajo la curva. El icono del menú reúne un signo de integral y
una tangente. Qt reconoce ambos SVG en sus tamaños previstos.

Cálculo aparece como sección propia justo antes de Métodos Numéricos
en Inicio y en el menú lateral. Ambas vistas siguen el orden del catálogo.

### Presentación de Newton–Raphson

Newton–Raphson sigue la presentación de Bisección y Regula Falsi para
el selector de ejemplos, el formulario y el resumen. Los tres métodos
comparten una tabla paginada con formato numérico y selección de la fila
desde el paso a paso. Se comprobó el flujo de Newton con una ventana de
960 píxeles, la selección de x₀ en ambas vistas de la gráfica y la tabla.
Pasaron `check.py` y las 68 pruebas.

### Ilustraciones y notación científica

Bisección destaca el punto medio del intervalo, Regula Falsi la secante,
Newton–Raphson la iteración y Cálculo el área bajo la curva. La interfaz
presenta la notación científica con potencias de diez en el editor,
los resultados, las tablas, las etiquetas de la gráfica y los errores.
Se comprobó el intercambio de un valor en notación científica entre
MathLive y el lector de números.

### LaTeX en resultados y procedimientos

MathLive renderiza las matrices, los sistemas, las fracciones, los
subíndices y las operaciones de los pasos. Las matrices aumentadas
conservan el separador y el planteamiento conserva el producto matricial.
Las instrucciones y los mensajes de estado se muestran como texto.
La vista de respaldo conserva la transcripción si MathLive no carga.
Se verificó el renderizado de los ejemplos de álgebra, conversiones,
romanos y cálculo, incluidos los pasos desplegados de Gauss.

### Separadores de resultados e iconos compartidos

Los resultados agrupan datos y soluciones en fichas y separan las
comprobaciones por ecuación. El paso a paso usa el mismo encabezado
numerado al recorrer un paso y al desplegar el procedimiento. Las
matrices aumentadas muestran ambos lados en LaTeX, alineados alrededor
de un divisor continuo. Los banners y los accesos de Inicio usan el
mismo SVG que el menú lateral para identificar cada herramienta.
Se revisó Gauss en claro y oscuro y el encabezado de Newton–Raphson
en los dos modos del paso a paso.

### Escala de la gráfica

La gráfica de raíces muestra el zoom respecto a la vista de referencia.
Al restablecer vuelve a 1:1. La regla se ajusta al rango visible.
Se comprobó en la vista pequeña y la ampliada,
incluida la restauración de la vista al cerrar. Pasaron `check.py`
y las 69 pruebas.

### Controles integrados en la gráfica

Bisección, Regula Falsi y Newton–Raphson alojan la gráfica y los
parámetros de resolución en el mismo panel. La vista ampliada usa
los mismos campos y conserva sus valores. Los botones de icono
controlan el zoom, el restablecimiento y el cambio de vista.
En la vista ampliada, el lienzo ocupa toda el área de la ventana y
los parámetros flotan en un formulario plegable. Se corrigió el icono
de restablecer el zoom. Se comprobó el cálculo desde la vista ampliada
en los tres métodos y la navegación al resultado. Pasaron `check.py`
y las 69 pruebas.

### Secante y selección de métodos abiertos

Secante parte de dos puntos y usa sus evaluaciones para calcular cada
aproximación. La tabla incluye el cambio absoluto y el residuo del
nuevo punto en ambos métodos. Se comprobaron el ejemplo guiado, la
práctica integradora, el denominador nulo, los límites de parada y el
cálculo desde la gráfica ampliada. Pasaron `check.py` y las 73 pruebas.

En Inicio, Métodos Abiertos ocupa las dos columnas cuando el catálogo
usa una cuadrícula de dos columnas.
