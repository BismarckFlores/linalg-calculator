# Bisección y Regula Falsi

Abre `python main.py` y elige **Método de Bisección** o **Regula Falsi** en
**Métodos Numéricos**. Ambos métodos comparten una página de Qt con MathLive,
gráfica, selector de iteración y tabla.

## Entrada y gráfica

Escribe la función y pulsa **Graficar función**. La vista inicial abarca
`x ∈ [−10, 10]`. Los controles de resolución aparecen debajo. Editar la
función oculta la gráfica y los controles hasta volver a graficar.
Editar los parámetros conserva la vista e invalida la respuesta y sus marcas.
**Cargar ejemplo** llena la función y los parámetros. Pulsa **Graficar
función** y luego **Calcular raíz** para ejecutarlo.

- Introduce el lado izquierdo de `f(x) = 0`.
- Se admiten productos implícitos como `5x^3`, `(1/2)x`, `2(x+1)`,
  `(x+1)(x-1)` y `2sin(x)`. También puedes usar `*`.
- Para potencias usa `^` o `**`. Las funciones requieren paréntesis.
- Funciones admitidas: `sin`, `cos`, `tan`, `exp`, `ln`, `log` (natural),
  `log10`, `sqrt` y `abs`. Las constantes son `pi` y `e`.
- Escribe `pi x` o `pi*x` para multiplicar dos nombres. Los identificadores
  completos se conservan. `1e-3x` se lee como `0.001*x`.
- `1/2x` se interpreta como `(1/2)*x`. Usa `1/(2x)` para poner el producto
  en el denominador.
- Dentro de la función usa punto decimal. Los campos a, b y E admiten
  fracciones y coma decimal.

La gráfica permite **Acercar**, **Alejar**, **Restablecer**, zoom con la
rueda y desplazamiento mediante arrastre. **Maximizar** abre una ventana
con la vista actual. Puedes cerrarla con **Cerrar** o Escape.
Arrastra para desplazar la vista en ambos ejes conservando la escala.
La rueda amplía o reduce alrededor del puntero. Las líneas verticales
identifican a, b y la aproximación c al resolver. **Restablecer** encuadra
el intervalo inicial si ya hay un resultado. Las muestras fuera del
dominio dejan huecos.

## Intervalo y criterios de parada

Introduce a, b, la tolerancia positiva E y un máximo de 1 a 1000 iteraciones
(100 por defecto). Los métodos requieren continuidad en todo `[a, b]` y
signos opuestos en los extremos para garantizar que el intervalo contenga
una raíz. Si un extremo evalúa a cero, se devuelve directamente. Los signos
iguales indican que hace falta otro intervalo para aplicar el método. Una
función como `1/x` cambia de signo al cruzar cero sin tener una raíz. Revisa
el dominio además de la gráfica, que usa un número finito de muestras.

| Criterio | Comparación | Unidades |
| --- | --- | --- |
| Ancho del intervalo | `b − a < E` | Unidades de x. Predeterminado en Bisección. |
| Residuo | `abs(f(c)) < E` | Unidades de f(x). Coincide con la columna de error de Bisección.xlsx. |
| Error relativo (%) | `abs((c − c_anterior) / c) × 100 < E` | Porcentaje. E = 1 significa 1 %. Predeterminado en Regula Falsi. |

Las comparaciones son estrictas. Un cero evaluado también detiene el
cálculo. El error relativo se muestra como un guion en la primera iteración,
si c es cero o si el porcentaje excede la representación disponible. El
límite de iteraciones y el estancamiento se identifican como motivos de parada
distintos de cumplir la tolerancia. Si c coincide con un extremo por
redondeo, un cambio relativo nulo no cuenta como convergencia.

## Cómo leer los resultados

La tarjeta de respuesta muestra c, el motivo de parada, el intervalo final,
la comprobación por sustitución, el residuo y el cambio relativo. Si el
intervalo encierra una raíz, la cota geométrica para la distancia desde c
es `max(c − a, b − c)`. En Bisección equivale aproximadamente a la mitad
del ancho. El residuo mide f(c) y el cambio relativo compara iteraciones.
Un cero calculado indica que f(c) dio cero en la aritmética de punto flotante.

En **Procedimiento**, el selector **Iteración** permite recorrer los cálculos.
Usa **Anterior**, **Siguiente** o **Ver todos los pasos** para consultar el
registro guardado. Seleccionar una iteración enfoca su fila en la tabla.

**Tabla de iteraciones** muestra hasta 15 filas por página. **Automático**
usa diez cifras significativas y cambia a notación científica cuando
corresponde. **Decimal** permite elegir de 0 a 17 decimales. El formato se
conserva entre cálculos y solo afecta la presentación. Al situar el cursor
sobre una celda, su ayuda emergente muestra el valor que guardó el motor.
Cuando una tabla excede el ancho, se puede desplazar horizontalmente.

## Bisección

El algoritmo calcula `c = a + (b − a)/2`, equivalente a `(a + b)/2` y
adecuado para evitar el desbordamiento de la suma de extremos grandes del
mismo signo. Evalúa f(c), guarda las medidas y revisa la parada. Si f(a) y
f(c) tienen signos opuestos, conserva `[a,c]`. En el otro caso conserva
`[c,b]`. Comparar los signos por separado evita desbordamientos al multiplicar
las ordenadas.

Cada vuelta reutiliza la evaluación del extremo que conserva. Después de las
evaluaciones iniciales, hace una nueva evaluación por iteración. Si hay p
nodos en la expresión y n iteraciones, el cálculo cuesta O(n p) y el registro
ocupa O(n). El ancho antes del corte de la fila n es aproximadamente
`ancho_inicial / 2**(n-1)`.

Para `x^4 - 5x^3 + 0.5x^2 - 11x + 10` en `[0.6, 1]` y E = 0.0001:

| Criterio | Iteraciones | Aproximación | Residuo |
| --- | ---: | ---: | ---: |
| Ancho | 13 | 0.763916015625 | 0.00027542280657 |
| Residuo | 15 | 0.76392822265625 | 0.000065382481667 |

Con ancho, la cota en x es aproximadamente 0.000048828125. El ejemplo
**Polinomio del Excel** usa residuo y reproduce los 15 puntos medios de
la hoja. También se incluyen `x^2 - 2` en `[1, 2]` y `x^10 - 1` en `[0, 1.3]`.

## Regula Falsi

La estimación c, llamada xᵣ en la guía, es el cruce con el eje x de la
recta que une `(a, f(a))` y `(b, f(b))`.

```text
c = b − f(b)(a − b)/(f(a) − f(b))
```

El código calcula la distancia equivalente desde el extremo más cercano al
cruce, con un cociente de valores absolutos que evita restar ordenadas grandes
de signo contrario. La actualización conserva el subintervalo con cambio
de signo. El método clásico puede dejar un extremo fijo muchas iteraciones,
como en `x^10 - 1`. La gráfica y el residuo ayudan a interpretar ese caso.
La tolerancia inicial es 0.01 % de cambio relativo y también se puede
seleccionar residuo.

**Ejercicio de la guía** usa `x^3 - 4.23603x^2 - 2.73620x - 13.09037` en
`[4.95, 5.5]`, de la sección 1.2 de `guia-busqueda-raices.pdf`. La tabla
impresa difiere de los resultados del polinomio. Evaluar la función da
`f(4.95) = -9.140510075` y `f(5.5) = 10.0956225`. La primera estimación
es 5.2113457004 y la cuarta, 5.2360505080. La cuarta tiene un cambio relativo
de aproximadamente 0.002862 % y un residuo de 0.0004642. Las aproximaciones
coinciden con el PDF ilustrado `Búsqueda_Numérica_de_Raíces.pdf`, págs. 5–7.
Ese material también explica la variante modificada para el estancamiento.

## Material de clase

Las referencias incluyen `MÉTODOS NUMERICOS.pptx` (diapositivas 3, 6, 8 y 14),
`Errores.pptx`, `Bisección.xlsx` (Hoja1), `guia-busqueda-raices.pdf`,
`Búsqueda_Numérica_de_Raíces.pdf` y `Anatomía_de_la_Incertidumbre_Computacional.pdf`.
Los dos PDF ilustrados se revisaron como imágenes. Las fotos de referencia
orientaron la selección de información en la interfaz.

En la primera tabla de la guía, los valores impresos tampoco corresponden al
polinomio de Bisección. La diapositiva 6 mezcla valores de error relativo y
aproximación final. La app evalúa la expresión introducida. Los valores
guardados en el Excel sirven como referencia para la prueba del residuo.
La derivada que se revisa en Newton corresponde a otro método.

## Código y defensa

| Archivo | Responsabilidad |
| --- | --- |
| `core/notation.py` | Inserta productos implícitos y conserva nombres, llamadas y literales científicos. |
| `core/real_function.py` | Lee la función con un AST restringido y la evalúa sin `eval`. También toma muestras para la gráfica. |
| `core/root_bracket.py` | Valida parámetros, conserva el intervalo y registra `BracketStep` y `BracketResult`. |
| `core/bisection.py` y `core/regula_falsi.py` | Definen la estimación y la tolerancia inicial de cada método. |
| `desktop/plot.py` | Dibuja con Qt y administra zoom, arrastre y vista ampliada. |
| `desktop/roots.py` | Organiza la entrada, gráfica, controles, resultado y tabla. Configura ambos métodos. |
| `desktop/forms.py` y `desktop/widgets.py` | Comparten el recorrido de pasos y la tabla. |
| `desktop/window.py` | Registra las herramientas en Inicio y el menú. |

El lector limita el tamaño de la expresión y los exponentes. Los problemas
de dominio, resultados no finitos y pérdidas por subdesbordamiento se
reportan. `math` se usa para evaluar funciones elementales. Los métodos
usan un ciclo y condiciones para obtener la aproximación. El gráfico usa
401 muestras por vista horizontal y las reutiliza al repintar.

## Verificación

```bash
python -m unittest discover -s tests -v
python check.py
python main.py
```

Las pruebas cubren los ejemplos de clase, la conservación del intervalo,
raíces en extremos y puntos interiores, cambio relativo, residuo, entradas
inválidas, estancamiento, límite y magnitudes extremas. También se prueba la
interfaz compartida, su recorrido, paginación, formato, desplazamiento y
gráfica previa. La entrega se ejecuta directamente desde el repositorio.
