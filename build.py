"""
Construye el archivo unico que se entrega al curso.

El enunciado pide un solo .py autocontenido, pero lo que vale la pena escribir
es un proyecto repartido en modulos. Asi que el archivo que se entrega no se
escribe a mano: se arma aqui con los modulos, en orden de dependencia, y se
quitan los imports entre ellos porque de todas formas todo acaba en un mismo
espacio de nombres.

El repositorio es la fuente de la verdad. Nunca se edita el archivo generado: se
edita el modulo y se vuelve a construir.

Se ejecuta con:  python build.py
"""

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------
# Que es el archivo que se entrega. La portada es un documento aparte, asi
# que aqui solo tienen que estar bien estas dos cosas.
# ---------------------------------------------------------------------

GROUP_NUMBER = "5"

# ---------------------------------------------------------------------
# Los bloques, en el orden en que tienen que aparecer, cada uno con el
# titulo que lo documenta dentro del archivo entregado.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Block:
    """
    Una seccion del archivo que se entrega, y de donde sale su codigo.

    Casi siempre es un modulo de este repositorio. La excepcion son las pocas
    lineas que nadie escribe en el repositorio porque alli no hacen falta: juntar
    modulos separados en un mismo espacio de nombres vuelve cierta una frase que
    no lo era, y un bloque asi lleva su propio code y sus propios imports.
    """

    source: str = ""
    title: str = ""
    description: str = ""
    code: str = ""
    imports: tuple[str, ...] = ()

@dataclass(frozen=True)
class Program:
    """
    Una tarea del curso, y el archivo unico con que se entrega.

    El numero y el titulo son los de la tarea, no los de este repositorio: el
    archivo se llama como tiene que llamarse la entrega, Programa N_GrupoX.py.
    Una tarea que tiene nombre en vez de numero lleva el nombre ahi.
    """

    number: int | str
    title: str
    preamble: str
    blocks: list[Block] = field(default_factory=list)

    def filename(self) -> str:
        return f"Programa {self.number}_Grupo{GROUP_NUMBER}.py"

ENGINE: list[Block] = [
    Block(
        "core/scalar.py",
        "EL NÚMERO EXACTO",
        "Cada entrada de una matriz se guarda como una fracción exacta, no como\n"
        "un decimal. Por eso un tercio se imprime como 1/3 y no como\n"
        "0.3333333333333333, y por eso la eliminación no acumula error de\n"
        "redondeo: el resultado coincide con el hecho a mano.",
    ),
    Block(
        "core/matrix.py",
        "LA MATRIZ",
        "Un rectángulo de números exactos y las operaciones que no necesitan\n"
        "explicarse: suma, resta, producto, y las tres operaciones elementales\n"
        "por filas (intercambiar, multiplicar por un número, sumar un múltiplo\n"
        "de otra fila). Los índices se cuentan desde 1, como en el pizarrón:\n"
        "a_23 es elem(2, 3).",
    ),
    Block(
        "core/steps.py",
        "EL REGISTRO DEL PASO A PASO",
        "Guarda la matriz inicial y, por cada operación elemental, la matriz de\n"
        "antes, la etiqueta de lo que se hizo (f_2 -> f_2 + 3*f_1) y la matriz\n"
        "de después. Es lo que permite imprimir la matriz en cada paso.",
    ),
    Block(
        "core/worksheet.py",
        "LA PIZARRA",
        "Junta una matriz con su registro. Es el único sitio donde una operación\n"
        "elemental se hace y se apunta a la vez, de modo que ningún algoritmo\n"
        "tiene que acordarse de ir dejando constancia. Las operaciones que no\n"
        "cambian nada no se apuntan, para que el paso a paso no tenga relleno.",
    ),
    Block(
        "core/elimination.py",
        "LA ELIMINACIÓN POR FILAS",
        "El método de Gauss: busca un pivote en cada columna, lo lleva a 1 y hace\n"
        "ceros por debajo. Si una columna está toda a cero de esa fila hacia\n"
        "abajo no tiene pivote y se salta, que es lo que hace que la escalera\n"
        "quede irregular cuando hay variables libres.\n"
        "\n"
        "La forma escalonada reducida (Gauss-Jordan) es el mismo recorrido con\n"
        "una segunda pasada de vuelta hacia arriba, y por eso vive aquí al lado\n"
        "y no en otro sitio.",
    ),
    Block(
        "core/systems.py",
        "LA CLASIFICACIÓN Y LA SOLUCIÓN DEL SISTEMA",
        "Clasifica el sistema comparando rangos (Rouché-Frobenius):\n"
        "  rango(A) < rango(A|b)                sin solución\n"
        "  rango(A) = rango(A|b) < incógnitas   infinitas soluciones\n"
        "  rango(A) = rango(A|b) = incógnitas   solución única\n"
        "Cuando la solución es única, despeja las incógnitas hacia atrás, de la\n"
        "última a la primera, guardando cada paso del despeje.",
    ),
    Block(
        "core/verification.py",
        "LA COMPROBACIÓN DE LA SOLUCIÓN",
        "Sustituye los valores hallados en el sistema ORIGINAL y compara los dos\n"
        "lados de cada ecuación. No mira nada de la eliminación a propósito: si\n"
        "comprobara sobre la matriz escalonada estaría comprobando el algoritmo\n"
        "contra sí mismo. La comparación es exacta, sin tolerancia, porque no\n"
        "hubo redondeo en ningún momento.",
    ),
    Block(
        "core/equations.py",
        "LA LECTURA DE UNA ECUACIÓN ESCRITA",
        "Convierte una ecuación escrita como se escribe, 2x + 3y - z = 5, en la\n"
        "fila de la matriz aumentada que le corresponde. Pasa las incógnitas a la\n"
        "izquierda y las constantes a la derecha, y las incógnitas del sistema\n"
        "son las que resulten mencionar las ecuaciones: nadie tiene que decir de\n"
        "antemano cuántas hay ni cómo se llaman.",
    ),
    Block(
        "core/parametric.py",
        "LA SOLUCIÓN GENERAL",
        "Cuando hay infinitas soluciones, escribe la familia entera: cada variable\n"
        "básica (la de una columna pivote) en función de las libres. Se lee de la\n"
        "forma escalonada reducida, donde cada pivote es 1 y está solo en su\n"
        "columna, así que la fila ya es el despeje y no hace falta sustituir hacia\n"
        "atrás.",
    ),
    Block(
        "ui/presentation.py",
        "EL TEXTO QUE SE MUESTRA",
        "Convierte los objetos anteriores en las frases que lee una persona.\n"
        "Aquí viven las tres clasificaciones con las palabras exactas que pide\n"
        "el enunciado, la barra que separa A de b en la matriz aumentada, y los\n"
        "nombres de las incógnitas.",
    ),
]

# ----- Lo que cada programa anade encima del motor -----

CONSOLE_BLOCKS: list[Block] = [
    Block(
        "ui/prompts.py",
        "LA LECTURA DE DATOS POR TECLADO",
        "Dos maneras de entrar el sistema. O se escriben las ecuaciones tal como\n"
        "se leen, una por línea, y de ahí salen los coeficientes; o se pide el\n"
        "número de ecuaciones m, el número de variables n, y después cada\n"
        "coeficiente por su nombre: a_11, a_12, ..., b_1. Si la respuesta no\n"
        "sirve, vuelve a preguntar; ninguna entrada equivocada corta el programa.",
    ),
    Block(
        "deliverables/program1.py",
        "EL PROGRAMA PRINCIPAL",
        "Ordena el trabajo en siete secciones numeradas igual que los requisitos\n"
        "del enunciado: entrada de datos, matriz aumentada inicial, eliminación\n"
        "por filas, sistema equivalente, clasificación, solución y comprobación.",
    ),
]

WINDOW_BLOCKS: list[Block] = [
    Block(
        "core/echelon.py",
        "LAS FORMAS ESCALONADAS Y LOS PIVOTES",
        "Lee la forma de una matriz, en vez de ponerla en una. Comprueba las cinco\n"
        "propiedades numeradas de la definición, una por una, y señala la entrada\n"
        "que rompe la que falle:\n"
        "  1. Las filas no nulas están arriba de las filas de ceros.\n"
        "  2. Cada entrada principal está a la derecha de la de la fila superior.\n"
        "  3. Debajo de una entrada principal, su columna es toda ceros.\n"
        "  4. Cada entrada principal es 1.\n"
        "  5. Cada entrada principal 1 es la única distinta de cero en su columna.\n"
        "Las tres primeras definen la forma escalonada; las cinco, la reducida.\n"
        "\n"
        "Una posición pivote no se lee de la matriz tal como está, sino del lugar\n"
        "que ocupa una entrada principal en su forma escalonada reducida, así que\n"
        "para localizarlas hay que reducir primero.",
    ),
    Block(
        "core/bases.py",
        "LOS SISTEMAS NUMÉRICOS",
        "Escribe un número entero en cualquier base del 2 al 36, y lee uno de esas\n"
        "bases de vuelta en base 10, sin usar int(texto, base), bin, oct ni hex.\n"
        "Las cifras mayores que 9 se escriben con letras, de la A (10) a la Z (35):\n"
        "  - Hacia otra base, por divisiones sucesivas: n = b·q + r. Cada residuo\n"
        "    es una cifra, y se leen de la última división a la primera.\n"
        "  - Hacia base 10, por la combinación lineal que representa el número:\n"
        "    d_k·b^k + ... + d_1·b^1 + d_0·b^0.\n"
        "Un número negativo se convierte como a mano, en cualquier base: se\n"
        "convierte su valor absoluto y el signo menos va delante de las cifras y\n"
        "de toda la combinación, -2B en base 16 = -(2·16^1 + 11·16^0) = -43.",
    ),
    Block(
        "core/roman.py",
        "LOS NÚMEROS ROMANOS",
        "Lee y escribe números romanos, y hace con ellos lo que pide el enunciado:\n"
        "  - Un número romano es la suma de sus piezas, escritas de mayor a menor.\n"
        "    Las seis parejas IV, IX, XL, XC, CD y CM valen una resta.\n"
        "  - Sumar y restar se hace sobre los valores: se leen los dos números, se\n"
        "    opera y el resultado se vuelve a escribir en romano.\n"
        "  - Multiplicar dos símbolos se hace por notación de suma, que es como se\n"
        "    enseña: X × V es X + X + X + X + X.\n"
        "Solo existen los números del 1 al 3999 (MMMCMXCIX): no había símbolo para\n"
        "el cero, ni para los negativos, ni por encima de M.",
    ),
    Block(
        "core/vectors.py",
        "LOS VECTORES DE Rn",
        "Un vector es una tupla de números exactos, y su dimensión n es la\n"
        "cantidad de componentes que tenga: no se fija de antemano. Las\n"
        "operaciones se hacen componente a componente:\n"
        "  u + v = (u1 + v1, ..., un + vn)\n"
        "  u - v = (u1 - v1, ..., un - vn)\n"
        "  k u   = (k u1, ..., k un)\n"
        "\n"
        "b es combinación lineal de v1, ..., vk si hay escalares con\n"
        "c1 v1 + ... + ck vk = b. Componente a componente eso es un sistema de n\n"
        "ecuaciones con k incógnitas, cuya matriz aumentada tiene los vectores como\n"
        "columnas, [ v1 ... vk | b ], y se resuelve con la misma eliminación de\n"
        "arriba: una solución es una manera de combinarlos, infinitas son\n"
        "infinitas maneras, y ninguna quiere decir que b no es combinación lineal.",
    ),
    Block(
        "core/inverse.py",
        "LA INVERSA DE UNA MATRIZ",
        "Reduce [A | I] mediante Gauss-Jordan. Si el bloque izquierdo llega a I, "
        "el derecho es la inversa. Comprueba ambos productos con A y permite "
        "resolver Ax = b como x = A^-1 b cuando A es invertible.",
    ),
    Block(
        "core/determinant.py",
        "EL DETERMINANTE",
        "Calcula det A por los dos caminos del enunciado, y dice de antemano cual\n"
        "conviene:\n"
        "  - Por cofactores: det A es la suma, a lo largo de una fila o una columna,\n"
        "    de cada entrada por su cofactor C_ij = (-1)^(i+j) · M_ij, donde el menor\n"
        "    M_ij es el determinante de lo que queda al tachar esa fila y esa\n"
        "    columna. Se desarrolla por la linea con mas ceros, porque cada cero se\n"
        "    salta un menor entero.\n"
        "  - Por LU: se reduce A a una escalonada U con reemplazos de fila, que no\n"
        "    cambian el determinante, guardando los multiplicadores en L. Como U es\n"
        "    triangular, det A es el producto de su diagonal; si hubo intercambios,\n"
        "    lo factorizado es PA = LU y cada intercambio cambia el signo.\n"
        "El costo decide: los cofactores piden del orden de n! multiplicaciones y LU\n"
        "del orden de n^3/3, asi que de 4 x 4 en adelante conviene LU. Una matriz de\n"
        "25 x 25 por cofactores serian unas 1.5e25 multiplicaciones.",
    ),
    Block(
        "gui/theme.py",
        "EL ASPECTO DE LA VENTANA",
        "Los colores, las tipografías y el interruptor entre modo claro y modo\n"
        "oscuro. Cada color es una pareja (claro, oscuro), que es justo lo que\n"
        "lee CustomTkinter: por eso cambiar de modo es una sola llamada y no hay\n"
        "que reconstruir ningún elemento de la ventana.",
    ),
    Block(
        title="EL TEMA COMO ESPACIO DE NOMBRES",
        description="En el repositorio esto es un módulo aparte, y el resto del código lo\n"
        "usa escribiendo theme.INK o theme.font(...). Al juntar todos los\n"
        "módulos en un solo archivo esos nombres pasan a estar aquí mismo, así\n"
        "que basta con que theme apunte a este archivo para que todas esas\n"
        "referencias sigan encontrando lo que buscan, sin cambiar ni una línea\n"
        "del código original.",
        imports=("sys",),
        code="theme = sys.modules[__name__]",
    ),
    Block(
        "gui/widgets.py",
        "LAS PIEZAS DE LA VENTANA",
        "CustomTkinter trae botones y cajas de texto, pero no trae matrices. Aquí\n"
        "están las formas que hacen falta y la librería no da: la tarjeta, el\n"
        "contador de filas y columnas, la matriz que se escribe, la matriz ya\n"
        "calculada y los corchetes que las rodean. Ninguna de ellas calcula nada.",
    ),
    Block(
        "gui/entry.py",
        "LAS DOS MANERAS DE ENTRAR UNA MATRIZ",
        "La tarjeta que pide los datos, que es la misma en las dos páginas que la\n"
        "necesitan: una cuadrícula de números, o el sistema escrito como se lee,\n"
        "una ecuación por línea. Lo que devuelve es la matriz, los nombres de las\n"
        "incógnitas cuando algo las nombró, y cuántas columnas son coeficientes.\n"
        "Aquí está también lo que se dice en castellano cuando algo no se puede\n"
        "leer, con el número de la línea que lo provoca.",
    ),
    Block(
        "gui/pages/vectors.py",
        "LA PESTAÑA DE VECTORES",
        "Suma y resta de vectores, producto por un escalar, y la pregunta de si un\n"
        "vector b es combinación lineal de v1, ..., vk. Las operaciones se\n"
        "muestran como columnas y componente a componente. La combinación se\n"
        "plantea como ecuación vectorial, se escribe como el sistema que es, se\n"
        "resuelve paso a paso y se comprueba volviendo a sumar los vectores.",
    ),
    Block(
        "gui/pages/operations.py",
        "LA PESTAÑA DE OPERACIONES CON MATRICES",
        "Suma, resta, producto de matrices, producto por un escalar y traspuesta.\n"
        "Cada operación es una llamada a la matriz; lo único que se decide aquí\n"
        "es qué tamaños pueden encontrarse, y eso se comprueba antes de llamar\n"
        "para poder explicarlo en castellano.",
    ),
    Block(
        "gui/pages/echelon.py",
        "LA PESTAÑA DE FORMAS ESCALONADAS",
        "Toma una matriz tal como está y responde las preguntas de la definición:\n"
        "si está en forma escalonada, si está en la reducida, cuáles son sus\n"
        "entradas principales y dónde quedan sus posiciones y columnas pivote.\n"
        "Cuando una propiedad no se cumple, dice cuál y señala la entrada que la\n"
        "rompe, que es lo que sirve para aprenderla.",
    ),
    Block(
        "gui/pages/determinant.py",
        "LA PESTAÑA DEL DETERMINANTE",
        "Antes de elegir metodo dice lo que costaria cada uno con esa matriz, que es\n"
        "una cuenta que solo depende del tamano. Despues muestra el procedimiento\n"
        "entero: los menores con su signo en el desarrollo por cofactores, o la\n"
        "reduccion con L, U y el producto de la diagonal en LU. Al final calcula el\n"
        "mismo determinante por el otro metodo, como comprobacion.",
    ),
    Block(
        "gui/pages/gauss.py",
        "LA PESTAÑA DE ELIMINACIÓN GAUSSIANA",
        "Resuelve A x = b y enseña las mismas siete secciones que pide el\n"
        "enunciado: la matriz aumentada, la eliminación paso a paso, el sistema\n"
        "equivalente, la clasificación, el despeje y la comprobación. El sistema\n"
        "se entra como coeficientes o escribiendo las ecuaciones, y el método se\n"
        "elige entre Gauss y Gauss-Jordan dentro de la misma pestaña.\n"
        "\n"
        "Antes de resolver, muestra el sistema como la ecuación matricial A x = b;\n"
        "y una solución única se comprueba también con el producto de matrices\n"
        "A x, que tiene que dar b.",
    ),
    Block(
        "gui/pages/bases.py",
        "LA PESTAÑA DE SISTEMAS NUMÉRICOS",
        "Convierte un número decimal, positivo o negativo, a binario, octal,\n"
        "hexadecimal o cualquier otra base del 2 al 36, que se escribe en un campo\n"
        "propio, y cualquiera de esas bases de vuelta a decimal. En el primer\n"
        "sentido escribe cada división como la ecuación que es; en el segundo\n"
        "escribe la combinación lineal completa y una tabla con lo que aporta cada\n"
        "posición.\n"
        "Cada conversión se comprueba con la contraria.",
    ),
    Block(
        "gui/pages/inverse.py",
        "LA PESTAÑA DE MATRIZ INVERSA",
        "Recibe matrices por coeficientes o ecuaciones con las mismas entradas "
        "de las otras páginas. Muestra la inversa con fracciones, la reducción "
        "paso a paso y ambos productos de comprobación, y resuelve Ax = b "
        "mediante la inversa.",
    ),
    Block(
        "gui/pages/roman.py",
        "LA PESTAÑA DE NÚMEROS ROMANOS",
        "Suma, resta y multiplica números romanos. Muestra cómo se lee cada\n"
        "número pieza por pieza, la operación en romano y en nuestros números, y\n"
        "la multiplicación escrita como la suma repetida que representa. Cuando\n"
        "el resultado es cero, negativo o mayor que MMMCMXCIX, lo dice: eso es la\n"
        "respuesta, porque los romanos no escribían esos números.",
    ),
    Block(
        "gui/app.py",
        "LA VENTANA",
        "El menú de la izquierda, la página abierta a la derecha y el cambio de\n"
        "tema. Una página se construye la primera vez que se abre y se conserva,\n"
        "así que volver a ella encuentra la matriz que se había escrito.",
    ),
    Block(
        "gui/__main__.py",
        "EL ARRANQUE",
        "Abre la ventana y le cede el control.",
    ),
]

# Como ejecutar un archivo que abre una ventana: lo unico que hay que instalar
# para cualquier entrega de aqui. Cada programa anade un parrafo con su
# matematica.
WINDOW_HOWTO = """COMO EJECUTARLO
---------------
Este programa abre una ventana, y para dibujarla usa CustomTkinter, que no
viene incluida con Python. Se instala dentro de un entorno virtual propio
(un .venv), que es una carpeta con su propia copia de las librerias, para
no tocar la instalacion de Python del sistema.

En Windows, desde PowerShell o CMD, en la carpeta donde este este archivo:

    py -m venv .venv
    .venv\\Scripts\\activate
    pip install customtkinter
    python "{filename}"

En Linux o macOS, desde la terminal:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install customtkinter
    python3 "{filename}"

Hace falta Python 3.12 o posterior. El comando deactivate cierra el entorno
virtual al terminar, y borrar la carpeta .venv lo deshace todo."""

PROGRAMS: list[Program] = [
    Program(
        number=1,
        title="Solucion de Sistemas de Ecuaciones Lineales por Eliminacion por Filas",
        preamble="""COMO EJECUTARLO
---------------
    python "{filename}"

No hace falta instalar nada: el programa se construye utilizando unicamente
Python estandar, con listas anidadas, condicionales, bucles y funciones. No
emplea NumPy, SciPy ni las funciones de algebra lineal de math.""",
        blocks=[*ENGINE, *CONSOLE_BLOCKS],
    ),
    Program(
        number=2,
        title="Reduccion a la Forma Escalonada Reducida (Gauss-Jordan)\n"
        "e Identificacion de Columnas Pivote",
        preamble=WINDOW_HOWTO + """

CustomTkinter solo dibuja. Toda la matematica de este archivo (la aritmetica
exacta, la eliminacion por filas, la clasificacion, el despeje y la
comprobacion) esta escrita con Python estandar: listas anidadas,
condicionales, bucles y funciones. No emplea NumPy, SciPy ni las funciones de
algebra lineal de math.""",
        blocks=[*ENGINE, *WINDOW_BLOCKS],
    ),
    Program(
        number="Determinante",
        title="Determinante de una Matriz por Cofactores y por Factorizacion LU",
        preamble=WINDOW_HOWTO + """

El determinante esta en la pestana Determinante de la ventana, dentro del grupo
Matrices del menu de la izquierda:

  Antes de elegir metodo    la pagina dice cuantas multiplicaciones pide cada
                            uno con esa matriz, y cual conviene
  Cofactores                desarrollo por la fila o la columna con mas ceros,
                            con el menor y el signo de cada entrada
  LU                        reduccion a A = LU (o PA = LU si hay intercambios)
                            y producto de la diagonal de U

Los dos metodos se comprueban entre si: al terminar, el determinante se vuelve
a calcular por el otro camino y los dos valores tienen que coincidir.

CustomTkinter solo dibuja. Toda la matematica esta escrita con Python estandar:
listas anidadas, condicionales, bucles y funciones, con fracciones exactas. No
emplea NumPy, SciPy ni las funciones de algebra lineal de math.""",
        blocks=[*ENGINE, *WINDOW_BLOCKS],
    ),
    Program(
        number="Matriz Inversa",
        title="Inversa de una Matriz y Solucion de A x = b por la Inversa",
        preamble=WINDOW_HOWTO + """

La inversa esta en la pestana Matriz Inversa de la ventana, dentro del grupo
Matrices del menu de la izquierda:

  Calcular A^-1                    boton Inversa A^-1. Reduce [ A | I ] por
                                   Gauss-Jordan hasta [ I | A^-1 ], muestra el
                                   paso a paso y comprueba A A^-1 = A^-1 A = I
  Resolver A x = b con la inversa  boton Resolver Ax = b. Calcula x = A^-1 b y
                                   comprueba A x = b en la A original

La matriz se escribe como coeficientes o como ecuaciones, igual que en las
demas paginas. Si A no es cuadrada, o no se puede reducir a la identidad, el
programa lo dice: esa matriz es singular y no tiene inversa.

CustomTkinter solo dibuja. Toda la matematica esta escrita con Python estandar:
listas anidadas, condicionales, bucles y funciones, con fracciones exactas. No
emplea NumPy, SciPy ni las funciones de algebra lineal de math.""",
        blocks=[*ENGINE, *WINDOW_BLOCKS],
    ),
    # Dos tareas entregadas en un solo archivo: las dos son paginas de la misma ventana.
    Program(
        number="Numeros Romanos",
        title="Suma, Resta y Multiplicacion de Numeros Romanos",
        preamble=WINDOW_HOWTO + """

Las operaciones con numeros romanos estan en la pestana Numeros Romanos de la
ventana, la ultima del menu de la izquierda:

  Sumar y restar numeros romanos    botones Suma y Resta
  Multiplicar por notacion de suma  boton Multiplicacion, un simbolo en cada
                                    casilla (I, V, X, L, C, D o M)

CustomTkinter solo dibuja. La lectura y la escritura de los numeros romanos
estan hechas con Python estandar: listas, condicionales, bucles y funciones. No
se usa ninguna libreria de numeros romanos, ni NumPy, SciPy o funciones
avanzadas de math.""",
        blocks=[*ENGINE, *WINDOW_BLOCKS],
    ),
    Program(
        number="Vectores y Sistemas Numericos",
        title="Vectores en Rn, Operaciones Matriciales y Ecuaciones Matriciales\n"
        "Conversion de Numeros entre Sistemas Numericos",
        preamble=WINDOW_HOWTO + """

DONDE ESTA CADA REQUISITO
-------------------------
Los dos programas son pestanas de la misma ventana, en el menu de la izquierda:

  Programa Vectores
    Modulo de vectores (Rn)          pestana Vectores
      suma, resta, k por un vector   botones u + v, u - v, k . u
      combinacion lineal             boton Combinacion lineal
    Operaciones matriciales          pestana Operaciones Matriciales
    Ecuacion matricial A x = b       pestana Eliminacion Gaussiana, que es el
                                     programa elaborado anteriormente

  Programa Sistemas Numericos
    Decimal a binario, octal,        pestana Sistemas Numericos,
    hexadecimal (u otra base)        Decimal -> otra base
    Binario, octal, hexadecimal      pestana Sistemas Numericos,
    (u otra base) a decimal          Otra base -> decimal

La ventana trae ademas la pestana Numeros Romanos, que se entrega tambien por
su cuenta como Programa Numeros Romanos_Grupo5.py.

CustomTkinter solo dibuja. Toda la matematica esta escrita con Python
estandar: listas, condicionales, bucles y funciones. No se usan NumPy, SciPy,
funciones avanzadas de math, ni int(texto, base), bin, oct o hex: las
conversiones se hacen por divisiones sucesivas y por la combinacion lineal de
potencias de la base.""",
        blocks=[*ENGINE, *WINDOW_BLOCKS],
    ),
]

RULE = "# " + "=" * 70
LOCAL_PACKAGES = ("core", "ui", "gui", "deliverables")

def header(program: Program) -> str:
    """
    Lo que el archivo dice de si mismo: que programa es y como se ejecuta.

    La portada es un documento aparte, asi que aqui no se nombra a nadie. Es un
    docstring en crudo porque las instrucciones de Windows llevan una ruta, y una
    barra invertida dentro de una cadena normal es una secuencia de escape de la
    que Python se queja.
    """
    return f'''r"""
PROGRAMA {program.number} - Grupo {GROUP_NUMBER}
{program.title}

Asignatura: Algebra Lineal (MTM0120)

{program.preamble.format(filename=program.filename())}
"""'''

def is_local_import(node: ast.stmt) -> bool:
    """Si este import apunta a otro modulo de este proyecto."""
    if isinstance(node, ast.ImportFrom):
        if node.level > 0:  # from .matrix import ..., o sea, un import de aqui
            return True
        root = (node.module or "").split(".")[0]
        return root in LOCAL_PACKAGES
    if isinstance(node, ast.Import):
        return any(alias.name.split(".")[0] in LOCAL_PACKAGES for alias in node.names)
    return False

def is_type_checking_block(node: ast.stmt) -> bool:
    """if TYPE_CHECKING: solo existe para el verificador de tipos; se quita."""
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "TYPE_CHECKING"
    )

def imports_only_type_checking(node: ast.stmt) -> bool:
    """from typing import TYPE_CHECKING se va cuando se va su bloque."""
    return (
        isinstance(node, ast.ImportFrom)
        and node.module == "typing"
        and all(alias.name == "TYPE_CHECKING" for alias in node.names)
    )

def last_line(node: ast.stmt) -> int:
    """
    La ultima linea que ocupa una sentencia.

    end_lineno es opcional en el AST porque un arbol construido a mano puede no
    llevar posiciones, pero aqui todo viene de ast.parse, donde siempre esta. Caer
    de vuelta en la primera linea deja contento al verificador de tipos sin
    inventar un caso que pueda ocurrir.
    """
    return node.end_lineno or node.lineno

def named(alias: ast.alias) -> str:
    """numpy as np, o solo sys, segun lo que escribiera el import."""
    return f"{alias.name} as {alias.asname}" if alias.asname else alias.name

def split_module(path: Path, plain: set[str], grouped: dict[str, set[str]]) -> str:
    """
    Desarma un modulo: anade sus imports a las colecciones comunes y devuelve el
    codigo que define.

    Las lineas se conservan tal cual, para que no se pierda ningun comentario;
    solo se recortan los tramos del docstring del modulo y de los imports. El
    codigo ya esta en castellano, asi que aqui no se traduce nada: lo unico que
    se le anade al archivo entregado es el titulo de cada bloque.
    """
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source)
    cut: set[int] = set()

    for index, node in enumerate(tree.body):
        span = range(node.lineno - 1, last_line(node))

        docstring = (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
        if docstring or is_type_checking_block(node) or imports_only_type_checking(node):
            cut.update(span)
            continue

        if isinstance(node, (ast.Import, ast.ImportFrom)):
            cut.update(span)
            if is_local_import(node):
                continue
            if isinstance(node, ast.Import):
                plain.update(named(alias) for alias in node.names)
            elif node.module:
                # Agrupados por modulo, para que dos archivos que piden nombres
                # distintos del mismo acaben en una sola linea. Que no haya
                # modulo significa from . import x, que is_local_import ya tomo.
                grouped.setdefault(node.module, set()).update(
                    named(alias) for alias in node.names
                )

    body = "\n".join(line for i, line in enumerate(lines) if i not in cut)
    return body.strip("\n")

def render_imports(plain: set[str], grouped: dict[str, set[str]]) -> str:
    """Todos los imports que necesita el archivo, juntos, sin repetir y en orden."""
    lines = [f"import {name}" for name in sorted(plain)]
    lines.extend(
        f"from {module} import {', '.join(sorted(names))}"
        for module, names in sorted(grouped.items())
    )
    return "\n".join(lines)

def block_heading(title: str, description: str) -> str:
    """El comentario que documenta un bloque del archivo entregado."""
    lines = [RULE, f"# BLOQUE: {title}", "#"]
    lines.extend(f"# {line}".rstrip() for line in description.splitlines())
    lines.append(RULE)
    return "\n".join(lines)

def clashes(program: Program) -> list[str]:
    """
    Todo nombre global que definan dos bloques del mismo programa.

    En el repositorio cada modulo tiene su propio espacio de nombres, asi que dos
    de ellos pueden tener cada uno su SUBTITLES y no encontrarse nunca. Juntos en
    un solo archivo comparten un unico espacio, el segundo pisa al primero sin
    decir nada, y la pagina que dependia del primero se rompe solo al abrirla.
    Por eso la construccion se niega.
    """
    owners: dict[str, str] = {}
    found: list[str] = []
    for block in program.blocks:
        if not block.source:
            continue
        for node in ast.parse(Path(block.source).read_text(encoding="utf-8")).body:
            names: list[str] = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names = [node.name]
            elif isinstance(node, ast.Assign):
                names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names = [node.target.id]
            for name in names:
                if name in owners and owners[name] != block.source:
                    found.append(f"{name}: {owners[name]} y {block.source}")
                owners.setdefault(name, block.source)
    return found

def build(program: Program) -> str:
    """Arma un archivo entero, bloque por bloque."""
    plain: set[str] = set()
    grouped: dict[str, set[str]] = {}
    blocks: list[str] = []

    for block in program.blocks:
        plain.update(block.imports)
        body = (
            block.code
            if block.code
            else split_module(Path(block.source), plain, grouped)
        )
        blocks.append(f"{block_heading(block.title, block.description)}\n\n{body}")

    return "\n\n\n".join(
        [header(program), render_imports(plain, grouped), *blocks]
    ) + "\n"

def write(program: Program) -> None:
    """Construye un programa, comprueba que compila, y dice donde quedo."""
    repeated = clashes(program)
    if repeated:
        print(f"No se puede construir {program.filename()}:")
        print("dos modulos definen el mismo nombre, y en un solo archivo se pisarian\n")
        for clash in repeated:
            print(f"  {clash}")
        sys.exit(1)

    text = build(program)

    try:
        compile(text, "<entregable>", "exec")
    except SyntaxError as error:
        print(f"El archivo generado no compila: linea {error.lineno}: {error.msg}")
        sys.exit(1)

    out = Path("deliverables/out")
    out.mkdir(parents=True, exist_ok=True)
    target = out / program.filename()
    target.write_text(text, encoding="utf-8")

    print(f"Escrito: {target}")
    print(f"  {len(text.splitlines())} lineas, {len(program.blocks)} bloques")
    print("  Todo el texto del archivo esta en castellano.")

def main() -> None:
    """Construye todos los programas que se pueden entregar."""
    for program in PROGRAMS:
        write(program)

if __name__ == "__main__":
    main()
