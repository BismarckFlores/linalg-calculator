"""
Spanish for every docstring and comment that goes into the handed-in file.

The repository is written in English; the file handed to the course has to read
in Spanish. Rather than keeping two copies of every module, the translation
lives here, keyed by the exact English text, and `build.py` swaps one for the
other while it assembles the file.

Keyed by text on purpose. Edit an English docstring and its Spanish becomes
stale — the build then fails naming it, instead of quietly shipping the old
wording. Add a function and the build fails until its docstring is translated
too.

Module docstrings are not here: `build.py` replaces those with the Spanish
block headings it writes itself.
"""

DOCSTRINGS: dict[str, str] = {
    # ----- core/scalar.py -----
    "Normalize a number or a piece of text into the exact Scalar type.":
        "Convierte un numero o un texto en el tipo exacto Scalar.",
    "Write a scalar the way it goes on the blackboard: 3, -4, 1/3.":
        "Escribe un numero como se escribe en el pizarron: 3, -4, 1/3.",
    "Write a scalar that multiplies a row inside a step label.\n"
    "\n"
    "Negatives and fractions get parentheses so the label stays readable:\n"
    "`f_3 -> (-1)*f_3` and `f_2 -> (1/3)*f_2`, but `f_1 -> 5*f_1`.":
        "Escribe el numero que multiplica a una fila dentro de la etiqueta de un paso.\n"
        "\n"
        "Los negativos y las fracciones llevan parentesis para que la etiqueta se\n"
        "lea bien: f_3 -> (-1)*f_3 y f_2 -> (1/3)*f_2, pero f_1 -> 5*f_1.",

    # ----- core/matrix.py -----
    "A sequence of values, but not a string: str is a Sequence too.":
        "Una secuencia de valores, pero no un texto: str tambien es una secuencia.",
    "An m x n rectangle of exact rationals.":
        "Un rectangulo de m x n numeros racionales exactos.",
    "Build from a list of rows: Matrix([[1, 2], [3, 4]]) is 2x2.":
        "Se construye con una lista de filas: Matrix([[1, 2], [3, 4]]) es 2x2.",
    "The entry a_ij, counting from 1.":
        "El elemento a_ij, contando desde 1.",
    "Row i as a plain list, counting from 1.":
        "La fila i como lista, contando desde 1.",
    "Column j as a plain list, counting from 1.":
        "La columna j como lista, contando desde 1.",
    "The main diagonal, as far as it reaches.":
        "La diagonal principal, hasta donde llegue.",
    "Whether row i is entirely zeros: the shape a fibre of `0 = k` takes.":
        "Si la fila i es toda ceros, que es la forma que toma una fila 0 = k.",
    "Rows become columns.":
        "Las filas pasan a ser columnas.",
    "Glue another matrix to the right: [A | B], and later [A | I].":
        "Pega otra matriz a la derecha: [A | B], y mas adelante [A | I].",
    "Columns `first` to `last`, both included and counted from 1.":
        "Las columnas de first a last, ambas incluidas y contando desde 1.",
    "f_i <-> f_j":
        "f_i <-> f_j",
    "f_i -> k*f_i, with k not zero: multiplying by zero is not reversible.":
        "f_i -> k*f_i, con k distinto de cero: multiplicar por cero no tiene vuelta atras.",
    "f_i -> f_i + k*f_j":
        "f_i -> f_i + k*f_j",
    "A * B if the shapes agree, A * k for a number.":
        "A * B si las dimensiones encajan, A * k si el otro es un numero.",
    "k * A reads better than A * k, and means the same.":
        "k * A se lee mejor que A * k, y significa lo mismo.",
    "The rows x cols matriz of zeros.":
        "La matriz de ceros de tamano filas x columnas.",
    "I_n, with ones down the diagonal.":
        "La identidad I_n, con unos en la diagonal.",
    "A single column, which is how a vector b enters the system.":
        "Una sola columna, que es como entra el vector b al sistema.",
    "Aligned on the widest entry, so the columns line up whatever they hold.":
        "Alineada segun el elemento mas ancho, para que las columnas cuadren siempre.",

    # ----- core/steps.py -----
    "f_i -> k*f_i":
        "f_i -> k*f_i",
    "f_i -> f_i + k*f_j, dropping the factor when it is exactly 1 or -1.":
        "f_i -> f_i + k*f_j, omitiendo el factor cuando vale exactamente 1 o -1.",
    "One elementary operation: what it looked like before, what it did, after.":
        "Una operacion elemental: como estaba antes, que se hizo, y como quedo.",
    "The starting matrix and every operation applied to it, in order.":
        "La matriz inicial y todas las operaciones que se le aplicaron, en orden.",
    "Centre a block of lines inside `height` rows, padding above and below.":
        "Centra un bloque de lineas en una altura dada, rellenando arriba y abajo.",
    "Two matrices with the operation between them, on the middle row.":
        "Dos matrices con la operacion entre ellas, en la fila central.",
    "The step drawn as `before --[ label ]-> after`.":
        "El paso dibujado como  antes --[ etiqueta ]-> despues.",
    "Append one operation and hand back its result, so calls can chain.":
        "Anade una operacion y devuelve su resultado, para poder encadenar llamadas.",
    "Attach a remark to the step just recorded, for an interface to show.":
        "Anade una nota al paso recien registrado, para que la interfaz la muestre.",
    "Where the chain ends: the initial matrix if nothing was applied.":
        "Donde termina la cadena: la matriz inicial si no se aplico nada.",
    "The matrix after `index` operations; `snapshot(0)` is the initial one.\n"
    "\n"
    "This is what a 'previous / next' control calls, and the only reason the\n"
    "log keeps the matrices instead of just the labels.":
        "La matriz despues de index operaciones; snapshot(0) es la inicial.\n"
        "\n"
        "Es lo que llama un control de 'anterior / siguiente', y la unica razon\n"
        "por la que el registro guarda las matrices y no solo las etiquetas.",
    "True when the matrix was already in its final form.":
        "Cierto cuando la matriz ya estaba en su forma final.",
    "Just the numbered operations, no matrices.":
        "Solo las operaciones numeradas, sin matrices.",
    "The whole trace, one block per step.":
        "La traza completa, un bloque por paso.",

    # ----- core/worksheet.py -----
    "A matrix plus the log of the operations applied to it.":
        "Una matriz junto con el registro de las operaciones que se le aplicaron.",
    "f_i <-> f_j. Swapping a row with itself changes nothing and is skipped.":
        "f_i <-> f_j. Intercambiar una fila consigo misma no cambia nada y se omite.",
    "f_i -> k*f_i. A factor of 1 is not written down: it does nothing.":
        "f_i -> k*f_i. Un factor de 1 no se apunta: no hace nada.",
    "f_i -> f_i + k*f_j. A factor of 0 is not written down.":
        "f_i -> f_i + k*f_j. Un factor de 0 no se apunta.",
    "Record the operation and move the blackboard on to its result.":
        "Registra la operacion y deja la pizarra en el resultado.",

    # ----- core/elimination.py -----
    "What a reduction produced: the result, how it got there, where the pivots are":
        "Lo que produjo una reduccion: el resultado, como se llego a el, y donde estan los pivotes",
    "Reduce to a row echelon form, recording every elementary operation.\n"
    "\n"
    "One pivot per column, normalized to 1, with zeros beneath it. A column that\n"
    "is all zeros from `row` down holds no pivot and is left alone; the same row\n"
    "then goes looking one column further right, which is what makes the\n"
    "staircase uneven when a variable turns out to be free.":
        "Reduce a una forma escalonada por filas, registrando cada operacion elemental.\n"
        "\n"
        "Un pivote por columna, normalizado a 1, con ceros por debajo. Una columna\n"
        "que esta toda a cero de esa fila hacia abajo no tiene pivote y se deja\n"
        "estar; la misma fila busca entonces una columna mas a la derecha, que es\n"
        "lo que hace que la escalera quede irregular cuando hay variables libres.",
    "Reduce to the reduced row echelon form: Gauss-Jordan.\n"
    "\n"
    "The same walk down as `to_ref`, and then back up: starting from the pivot\n"
    "furthest to the right, every entry above a pivot is cleared too. What comes\n"
    "out satisfies the two extra conditions of the reduced form, that each\n"
    "leading entry is 1 and is the only non-zero entry in its column.\n"
    "\n"
    "Going back up never moves a pivot, so the positions found on the way down\n"
    "are still the positions on the way out.":
        "Reduce a la forma escalonada reducida por filas: Gauss-Jordan.\n"
        "\n"
        "El mismo recorrido de bajada que to_ref, y despues la vuelta hacia arriba:\n"
        "empezando por el pivote de mas a la derecha, se hacen ceros tambien por\n"
        "encima de cada pivote. Lo que sale cumple las dos condiciones de mas de la\n"
        "forma reducida: cada elemento principal es 1 y es el unico distinto de\n"
        "cero en su columna.\n"
        "\n"
        "La vuelta hacia arriba no mueve ningun pivote, asi que las posiciones\n"
        "encontradas en la bajada siguen siendo las posiciones al salir.",
    "The walk down: find a pivot, scale it to 1, clear everything below it.\n"
    "\n"
    "Returns the pivot positions in the order they were found, which is by row.":
        "La bajada: busca un pivote, lo lleva a 1 y hace ceros por debajo.\n"
        "\n"
        "Devuelve las posiciones de los pivotes en el orden en que se encontraron,\n"
        "que es por filas.",
    "The walk back up: clear the entries above each pivot, rightmost pivot first.\n"
    "\n"
    "Right to left matters. A pivot further right has already been isolated by\n"
    "the time it is used to clear the column of a pivot further left, so no\n"
    "operation here can put back a zero that a later one removed.\n"
    "\n"
    "Nothing is scaled: `_forward` left every pivot at 1 already.":
        "La vuelta hacia arriba: hace ceros por encima de cada pivote, empezando\n"
        "por el de mas a la derecha.\n"
        "\n"
        "El orden de derecha a izquierda importa. Un pivote de mas a la derecha ya\n"
        "esta aislado cuando se usa para limpiar la columna de uno de mas a la\n"
        "izquierda, asi que ninguna operacion de aqui puede deshacer un cero que\n"
        "otra posterior ya habia conseguido.\n"
        "\n"
        "No se multiplica ninguna fila: _forward ya dejo todos los pivotes en 1.",
    "How many pivots the echelon form of this matrix has.":
        "Cuantos pivotes tiene la forma escalonada de esta matriz.",
    "The first row at or below `from_row` whose entry in `col` is not zero.":
        "La primera fila, desde from_row hacia abajo, cuyo elemento en col no es cero.",
    "The number of pivots, which is the rank of the matrix.":
        "El numero de pivotes, que es el rango de la matriz.",
    "The 1-based columns holding a pivot.":
        "Las columnas que tienen pivote, contando desde 1.",
    "The 1-based columns with no pivot: the free variables of a system.":
        "Las columnas sin pivote, contando desde 1: las variables libres del sistema.",
    "The 1-based rows that ended up entirely zero.":
        "Las filas que quedaron todas a cero, contando desde 1.",

    # ----- core/systems.py -----
    "The Rouche-Frobenius classification of a system.":
        "La clasificacion de un sistema segun Rouche-Frobenius.",
    "One unknown cleared from the echelon form, and what it took to clear it.":
        "Una incognita despejada de la forma escalonada, y lo que costo despejarla.",
    "What the echelon form says about the system.":
        "Lo que la forma escalonada dice sobre el sistema.",
    "Solve the system written as an augmented matrix, last column the constants.\n"
    "\n"
    "The whole walk down to the echelon form is in `solution.log`, and the\n"
    "clearing that follows it is in `solution.substitutions`.":
        "Resuelve el sistema escrito como matriz aumentada, con los terminos\n"
        "independientes en la ultima columna.\n"
        "\n"
        "Todo el recorrido hasta la forma escalonada esta en solution.log, y el\n"
        "despeje que viene despues esta en solution.substitutions.",
    "Walk the echelon form upwards, replacing the unknowns already cleared.\n"
    "\n"
    "Only ever called for a system with a unique solution, which is what lets it\n"
    "stay this short: every unknown holds a pivot, and every pivot is already 1\n"
    "because `to_ref` normalizes them. The steps come back in the order the work\n"
    "is done, so the last unknown is first.":
        "Sube por la forma escalonada sustituyendo las incognitas ya despejadas.\n"
        "\n"
        "Solo se llama cuando la solucion es unica, que es lo que permite que sea\n"
        "tan corta: cada incognita tiene pivote, y cada pivote ya vale 1 porque\n"
        "to_ref los normaliza. Los pasos salen en el orden en que se hace el\n"
        "trabajo, asi que la ultima incognita va primero.",
    "The [A | b] the system was handed in as.":
        "La matriz [A | b] tal como se entrego el sistema.",
    "The echelon form the elimination ended on.":
        "La forma escalonada en la que termino la eliminacion.",
    "A on its own, for putting a solution back into the original system.":
        "La matriz A sola, para sustituir la solucion en el sistema original.",
    "b on its own, as a single column.":
        "El vector b solo, como una unica columna.",
    "Rank of the augmented matrix.":
        "Rango de la matriz aumentada.",
    "Rank of A: the pivots that fall on an unknown, not on the constants.":
        "Rango de A: los pivotes que caen sobre una incognita, no sobre los terminos\n"
        "independientes.",

    # ----- core/verification.py -----
    "One equation of the original system with the values put back into it.":
        "Una ecuacion del sistema original con los valores sustituidos en ella.",
    "The same check across every equation of the system.":
        "La misma comprobacion sobre todas las ecuaciones del sistema.",
    "Evaluate A x = b row by row with the values found.\n"
    "\n"
    "`constants` is b as a single column, the same shape it has inside\n"
    "augmented matrix. Each `RowCheck` keeps its terms as\n"
    "(coefficient, value, column) so an interface can write the substitution out\n"
    "in full instead of only reporting the total.":
        "Evalua A x = b fila por fila con los valores hallados.\n"
        "\n"
        "constants es b como una sola columna, la misma forma que tiene dentro de\n"
        "la matriz aumentada. Cada RowCheck guarda sus terminos como\n"
        "(coeficiente, valor, columna) para que la interfaz pueda escribir la\n"
        "sustitucion entera y no solo dar el total.",
    "Whether this equation came out true.":
        "Si esta ecuacion se cumple.",
    "True only when every single equation came out true.":
        "Cierto solo cuando se cumplen todas y cada una de las ecuaciones.",
    "The equations that did not hold, if any did not.":
        "Las ecuaciones que no se cumplieron, si alguna no lo hizo.",

    # ----- core/equations.py -----
    "Something in the text of an equation cannot be read.":
        "Hay algo en el texto de una ecuacion que no se puede leer.",
    "The text does not hold exactly one `=`.":
        "El texto no tiene exactamente un =.",
    "A fragment of a side is not a term. `text` is the fragment itself.":
        "Un trozo de un lado no es un termino. text es el trozo en cuestion.",
    "One equation, tidied: `terms = constant`, with nothing left on the right.":
        "Una ecuacion ya ordenada: terminos = constante, sin nada suelto a la derecha.",
    "Read one written equation.\n"
    "\n"
    "Whatever is on the right moves left and whatever is constant moves right, so\n"
    "`2x = 3y + 1` and `2x - 3y = 1` come back identical. A coefficient that\n"
    "cancels to zero is dropped: after `x + y = x + 2` the system does not mention\n"
    "x at all, and pretending otherwise would invent a column.":
        "Lee una ecuacion escrita.\n"
        "\n"
        "Lo que esta a la derecha pasa a la izquierda y lo que es constante pasa a\n"
        "la derecha, de modo que 2x = 3y + 1 y 2x - 3y = 1 salen identicas. Un\n"
        "coeficiente que se cancela a cero se descarta: despues de x + y = x + 2 el\n"
        "sistema no menciona x, y fingir lo contrario seria inventarse una columna.",
    "Every unknown the equations mention, in the order they become columns.\n"
    "\n"
    "Alphabetical, with trailing digits compared as numbers so that x2 comes\n"
    "before x10. Alphabetical and not order of appearance, because `2y + 3x = 5`\n"
    "should still put x in the first column: that is where a reader looks for it.":
        "Todas las incognitas que mencionan las ecuaciones, en el orden en que van a\n"
        "ser columnas.\n"
        "\n"
        "Por orden alfabetico, con los digitos finales comparados como numeros para\n"
        "que x2 vaya antes que x10. Alfabetico y no por orden de aparicion, porque\n"
        "2y + 3x = 5 tiene que seguir poniendo x en la primera columna: ahi es donde\n"
        "la busca quien lo lee.",
    "Lay the equations out as [A | b] against those names.\n"
    "\n"
    "An unknown that an equation never mentions is a zero in that row, which is\n"
    "what lets somebody write `x + z = 1` and `y = 2` and still get a system of\n"
    "three columns out of it.":
        "Coloca las ecuaciones como [A | b] frente a esos nombres.\n"
        "\n"
        "Una incognita que una ecuacion no menciona es un cero en esa fila, que es\n"
        "lo que permite escribir x + z = 1 e y = 2 y obtener aun asi un sistema de\n"
        "tres columnas.",
    "Read one side into its coefficients and its constant.\n"
    "\n"
    "Whitespace goes first, so `2 x` and `2x` are the same thing, and the text is\n"
    "lowercased, so `X` and `x` are the same unknown. Then terms are taken left to\n"
    "right until the side is used up; anything the pattern cannot consume is\n"
    "reported with the fragment that stopped it.":
        "Lee un lado y lo separa en sus coeficientes y su constante.\n"
        "\n"
        "Primero se quitan los espacios, para que 2 x y 2x sean lo mismo, y se pasa\n"
        "todo a minusculas, para que X y x sean la misma incognita. Despues se van\n"
        "tomando terminos de izquierda a derecha hasta agotar el lado; lo que el\n"
        "patron no consigue leer se informa junto al trozo que lo detuvo.",
    "Letters first, then trailing digits as a number: x, x1, x2, x10, y.":
        "Primero las letras, y luego los digitos finales como numero: x, x1, x2, x10, y.",

    # ----- ui/presentation.py -----
    "The name of the unknown sitting in a 1-based column.\n"
    "\n"
    "Whatever the person called it, when they wrote the system out as equations\n"
    "and there is a name to use. Otherwise the blackboard default: x, y, z, w,\n"
    "and x5 upwards once those run out.":
        "El nombre de la incognita que ocupa esa columna, contando desde 1.\n"
        "\n"
        "El que le haya puesto quien escribio el sistema, cuando lo escribio como\n"
        "ecuaciones y hay un nombre que usar. Si no, los del pizarron de siempre:\n"
        "x, y, z, w, y de ahi en adelante x5, x6...",
    "A step label in typographic notation: `f₂ → f₂ + 3 · f₁`.\n"
    "\n"
    "The same operation the course writes as `f_2 -> f_2 + 3*f_1`, which is what\n"
    "`core/steps.py` produces and what the handed-in file prints. A window has the\n"
    "glyphs for it and a plain transcript cannot be trusted to, so the choice\n"
    "belongs to whoever is drawing rather than to the engine.":
        "Una etiqueta de paso en notacion tipografica: f₂ → f₂ + 3 · f₁.\n"
        "\n"
        "La misma operacion que el curso escribe como f_2 -> f_2 + 3*f_1, que es lo\n"
        "que produce steps.py y lo que imprime el archivo entregado. Una ventana\n"
        "tiene los caracteres para escribirlo y una transcripcion de texto plano no\n"
        "necesariamente, asi que la decision es de quien dibuja, no del motor.",
    "The augmented matrix with the bar between A and b: `[ 1  -2   1 |  0 ]`.\n"
    "\n"
    "The bar is drawn here and not in `Matrix.__str__` because only a system\n"
    "knows that its last column means something different from the rest.":
        "La matriz aumentada con la barra que separa A de b: [ 1  -2   1 |  0 ].\n"
        "\n"
        "La barra se dibuja aqui y no en Matrix.__str__ porque solo un sistema\n"
        "sabe que su ultima columna significa algo distinto que las demas.",
    "The whole elimination, one numbered block per elementary operation.":
        "La eliminacion completa, un bloque numerado por operacion elemental.",
    "The classification, in the exact words the assignment asks for.":
        "La clasificacion, con las palabras exactas que pide el enunciado.",
    "The value of each unknown, or the free ones when there are infinitely many.":
        "El valor de cada incognita, o cuales son libres si hay infinitas soluciones.",
    "The echelon matrix written back as the system of equations it stands for.":
        "La matriz escalonada escrita otra vez como el sistema de ecuaciones que representa.",
    "The clearing, written out line by line the way it is done on paper.":
        "El despeje, escrito linea a linea como se hace en papel.",
    "Each equation of the original system with the values put into it.\n"
    "\n"
    "Two lines per equation: the substitution as it is written, and what each\n"
    "side adds up to. The point is that the reader can follow the arithmetic,\n"
    "not just be told that it worked.":
        "Cada ecuacion del sistema original con los valores sustituidos.\n"
        "\n"
        "Dos lineas por ecuacion: la sustitucion tal como se escribe, y cuanto\n"
        "suma cada lado. La idea es que se pueda seguir la aritmetica, no solo\n"
        "leer que salio bien.",
    "The 1-based row that reads `0 ... 0 | k` with k not zero.\n"
    "\n"
    "That row is the whole reason an inconsistent system is inconsistent, so the\n"
    "reader is shown it by name rather than told that one exists somewhere.":
        "La fila que queda como  0 ... 0 | k  con k distinto de cero, contando desde 1.\n"
        "\n"
        "Esa fila es toda la razon por la que un sistema es inconsistente, asi que\n"
        "se le ensena al lector por su nombre en vez de decirle que hay una.",
    "'1 pivote' or '3 pivotes', so nothing ever reads as '1 pivote(s)'.":
        "'1 pivote' o '3 pivotes', para que nunca se lea '1 pivote(s)'.",
    "One equation with every unknown replaced by its value: `1*(29) + (-2)*(16)`.":
        "Una ecuacion con cada incognita sustituida por su valor: 1*(29) + (-2)*(16).",
    "One term with its sign in front: '+ y', '- 3*z', '+ (1/3)*x'.":
        "Un termino con su signo delante: '+ y', '- 3*z', '+ (1/3)*x'.",

    # ----- ui/prompts.py -----
    "Ask for a whole number inside a range, insisting until one arrives.":
        "Pide un numero entero dentro de un rango, insistiendo hasta conseguirlo.",
    "Ask for one number, accepting integers, decimals and fractions.":
        "Pide un numero, aceptando enteros, decimales y fracciones.",
    "Ask something that only takes yes or no.":
        "Pregunta algo que solo admite si o no.",
    "Wait for Enter, so one section can be read before the next one arrives.\n"
    "\n"
    "Only when a person is watching. With the input redirected there is nobody\n"
    "to press anything, so the program runs straight through instead of stopping\n"
    "on a prompt that will never be answered.":
        "Espera a que se pulse Enter, para poder leer una seccion antes de que\n"
        "llegue la siguiente.\n"
        "\n"
        "Solo si hay alguien mirando. Con la entrada redirigida no hay quien pulse\n"
        "nada, asi que el programa corre de largo en vez de quedarse esperando una\n"
        "tecla que nunca va a llegar.",
    "Ask how the system is going to be written down, and read it that way.\n"
    "\n"
    "Comes back with [A | b] and the names of the unknowns in column order. The\n"
    "names are empty when the coefficients were given one by one, because then\n"
    "nobody ever said what the unknowns are called.":
        "Pregunta como se va a escribir el sistema, y lo lee de esa manera.\n"
        "\n"
        "Devuelve [A | b] y los nombres de las incognitas en el orden de las\n"
        "columnas. Los nombres vienen vacios cuando los coeficientes se dieron uno\n"
        "a uno, porque entonces nadie llego a decir como se llaman las incognitas.",
    "Read the system as equations, one per line, until a blank line ends it.\n"
    "\n"
    "The unknowns are whatever the equations turn out to mention, so nobody has\n"
    "to say up front how many there are. What was understood is read back before\n"
    "anything is done with it: a typo in an equation is much easier to catch as a\n"
    "list of unknowns than as a wrong answer three sections later.":
        "Lee el sistema como ecuaciones, una por linea, hasta que una linea en\n"
        "blanco lo da por terminado.\n"
        "\n"
        "Las incognitas son las que resulten mencionar las ecuaciones, asi que\n"
        "nadie tiene que decir de antemano cuantas hay. Lo que se entendio se\n"
        "devuelve por pantalla antes de hacer nada con ello: una errata en una\n"
        "ecuacion se pilla mucho mejor viendo la lista de incognitas que viendo un\n"
        "resultado equivocado tres secciones mas adelante.",
    "Take equations until a blank line, explaining in Spanish whatever fails.\n"
    "\n"
    "The parser raises one exception per kind of mistake and says nothing to\n"
    "anybody; the sentence a person reads is decided here, like every other\n"
    "sentence in the program.":
        "Va tomando ecuaciones hasta una linea en blanco, explicando en castellano\n"
        "lo que falle.\n"
        "\n"
        "El analizador lanza una excepcion por cada tipo de error y no le dice nada\n"
        "a nadie; la frase que lee una persona se decide aqui, como todas las demas\n"
        "frases del programa.",
    "Ask for the size and then every coefficient, and build [A | b] out of them.\n"
    "\n"
    "The questions go equation by equation, ending each one with its constant\n"
    "term, because that is the order in which the system is written down: a whole\n"
    "equation, then the next.":
        "Pide el tamano y despues cada coeficiente, y construye [A | b] con ellos.\n"
        "\n"
        "Las preguntas van ecuacion por ecuacion, terminando cada una con su\n"
        "termino independiente, porque es el orden en que se escribe un sistema:\n"
        "una ecuacion entera, y luego la siguiente.",

    # ----- deliverables/program1.py -----
    "A section heading, so each requirement is easy to find in the output.\n"
    "\n"
    "It waits for Enter first, so the section just finished can be read before\n"
    "the next one pushes it off the screen. The first heading of a system has\n"
    "nothing above it to read, so it does not wait.":
        "Un titulo de seccion, para localizar facilmente cada requisito en la salida.\n"
        "\n"
        "Antes espera a que se pulse Enter, para poder leer la seccion que acaba\n"
        "de terminar antes de que la siguiente la empuje fuera de la pantalla. El\n"
        "primer titulo no espera, porque no hay nada encima que leer.",
    "Read a system, reduce it, classify it, solve it and check the answer.":
        "Lee un sistema, lo reduce, lo clasifica, lo resuelve y comprueba la respuesta.",
    "Run the program, and offer to solve another system before leaving.":
        "Ejecuta el programa, y ofrece resolver otro sistema antes de salir.",
}

COMMENTS: dict[str, str] = {
    # ----- core/scalar.py -----
    "# What an entry is once it is inside a matrix: always an exact Fraction.":
        "# Lo que es una entrada una vez dentro de una matriz: siempre una fraccion exacta.",
    '# What `to_scalar` knows how to read: a number, or text like "3", "-2.5", "1/3".':
        '# Lo que to_scalar sabe leer: un numero, o texto como "3", "-2.5", "1/3".',
    "# bool is a subclass of int, and True as a matrix entry is always a bug.":
        "# bool hereda de int, y un True como entrada de una matriz siempre es un error.",
    "# Through str() so 0.1 becomes 1/10 and not a binary approximation.":
        "# Pasando por str() para que 0.1 sea 1/10 y no una aproximacion binaria.",

    # ----- core/matrix.py -----
    "# ----- Reading -----":
        "# ----- Lectura -----",
    "# ----- Shape -----":
        "# ----- Forma -----",
    "# ----- elemtary row operations -----":
        "# ----- operaciones elementales por filas -----",
    "# ----- arithmetic -----":
        "# ----- aritmetica -----",
    "# ----- building -----":
        "# ----- construccion -----",
    "# ----- comparing and printing -----":
        "# ----- comparacion e impresion -----",
    "# to_scalar reads \"1/2\" as well as 0.5, and complains about anything else.":
        "# to_scalar lee tanto \"1/2\" como 0.5, y protesta con cualquier otra cosa.",

    # ----- core/steps.py -----
    "# Only the type checker needs this; importing it at runtime would be circular.":
        "# Solo lo necesita el verificador de tipos; importarlo en ejecucion seria circular.",

    # ----- core/systems.py -----
    "# A pivot landed on the constants column: some row reads 0 = k.":
        "# Un pivote cayo en la columna de terminos independientes: alguna fila dice 0 = k.",
    "# Fewer pivots than unknowns: the ones left over are free.":
        "# Menos pivotes que incognitas: las que sobran son libres.",

    # ----- core/equations.py -----
    "# One term: an optional sign, an optional coefficient written plainly or inside":
        "# Un termino: un signo opcional, un coeficiente opcional escrito tal cual o entre",
    "# parentheses, an optional `*`, and an optional name. Everything is optional":
        "# parentesis, un * opcional y un nombre opcional. Todo es opcional porque",
    "# because `x`, `2`, `-3y` and `(1/2)z` are all terms; a match with neither a":
        "# x, 2, -3y y (1/2)z son todos terminos; una coincidencia que no tiene ni",
    "# number nor a name is the one combination that means nothing.":
        "# numero ni nombre es la unica combinacion que no significa nada.",
    "# A name split into its letters and its trailing digits, for sorting.":
        "# Un nombre partido en sus letras y sus digitos finales, para poder ordenarlo.",
    "# A lone sign. What went wrong is whatever comes after it.":
        "# Un signo suelto. Lo que esta mal es lo que venga detras de el.",
    "# A written coefficient is read by `to_scalar`, so `1/3`, `2.5` and":
        "# Un coeficiente escrito lo lee to_scalar, asi que 1/3, 2.5 y 2,5",
    "# `2,5` mean here exactly what they mean everywhere else.":
        "# significan aqui exactamente lo mismo que en todo lo demas.",

    # ----- ui/presentation.py -----
    "# Named after the blackboard for the sizes that fit on it; x5, x6... beyond.":
        "# Con los nombres del pizarron mientras quepan; a partir de ahi x5, x6...",
    "# Digits as subscripts, for writing f_12 as f₁₂ where the glyphs are available.":
        "# Los digitos como subindices, para escribir f_12 como f₁₂ donde se pueda.",
    "# A and b get their own width, so a wide coefficient does not stretch b too.":
        "# A y b llevan su propio ancho, para que un coeficiente largo no estire tambien b.",
    "# Pad the numbering so equation 9 and equation 10 still line up.":
        "# Se rellena la numeracion para que la ecuacion 9 y la 10 sigan cuadrando.",

    # ----- deliverables/program1.py -----
    "# Ctrl+D or Ctrl+C: leave without a traceback, the run was cut short.":
        "# Ctrl+D o Ctrl+C: se sale sin traza de error, la ejecucion se corto.",
}
