"""
Build the single file the course is handed.

The assignment wants one self-contained `.py`, but a project split into modules
is what is worth writing. So the file handed in is not written by hand: it is
assembled here out of the modules, in dependency order, with the imports between
them dropped because everything ends up in one namespace anyway.

The repository is the source of truth. Never edit the generated file: edit the
module and build again.

Run:  python build.py
"""

import ast
import io
import sys
import tokenize
from dataclasses import dataclass, field
from pathlib import Path

from translations import COMMENTS, DOCSTRINGS

# ---------------------------------------------------------------------
# What the handed-in file is. The cover page is a separate document, so
# only these two things have to be right here.
# ---------------------------------------------------------------------

GROUP_NUMBER = "5"

PROGRAM_NUMBER = 1
PROGRAM_TITLE = "Solución de Sistemas de Ecuaciones Lineales por Eliminación por Filas"

# ---------------------------------------------------------------------
# The blocks, in the order they have to appear, each with the Spanish
# heading that documents it in the handed-in file.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Block:
    """
    One section of the file handed in, and where its code comes from.

    Almost always a module of this repository. The exception is the handful of
    lines nobody writes in the repository because nothing there needs them:
    joining separate modules into one namespace makes a statement true that was
    not, and a block like that carries its own `code` and its own `imports`.
    """

    source: str = ""
    title: str = ""
    description: str = ""
    code: str = ""
    imports: tuple[str, ...] = ()

@dataclass(frozen=True)
class Program:
    """One thing that can be handed in: a name, a preamble and its blocks."""

    suffix: str
    subtitle: str
    preamble: str
    blocks: list[Block] = field(default_factory=list)

    def filename(self) -> str:
        return f"Programa {PROGRAM_NUMBER}_Grupo{GROUP_NUMBER}{self.suffix}.py"

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
        "ui/presentation.py",
        "EL TEXTO QUE SE MUESTRA",
        "Convierte los objetos anteriores en las frases que lee una persona.\n"
        "Aquí viven las tres clasificaciones con las palabras exactas que pide\n"
        "el enunciado, la barra que separa A de b en la matriz aumentada, y los\n"
        "nombres de las incógnitas.",
    ),
]

# ----- What each of the two programs adds on top of the engine -----

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
        "gui/pages/operations.py",
        "LA PESTAÑA DE OPERACIONES CON MATRICES",
        "Suma, resta, producto de matrices, producto por un escalar y traspuesta.\n"
        "Cada operación es una llamada a la matriz; lo único que se decide aquí\n"
        "es qué tamaños pueden encontrarse, y eso se comprueba antes de llamar\n"
        "para poder explicarlo en castellano.",
    ),
    Block(
        "gui/pages/gauss.py",
        "LA PESTAÑA DE ELIMINACIÓN GAUSSIANA",
        "Resuelve A x = b y enseña las mismas siete secciones que pide el\n"
        "enunciado: la matriz aumentada, la eliminación paso a paso, el sistema\n"
        "equivalente, la clasificación, el despeje y la comprobación. El sistema\n"
        "se entra como coeficientes o escribiendo las ecuaciones, y el método se\n"
        "elige entre Gauss y Gauss-Jordan dentro de la misma pestaña.",
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

PROGRAMS: list[Program] = [
    Program(
        suffix="",
        subtitle="Interfaz grafica",
        preamble="""COMO EJECUTARLO
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
virtual al terminar, y borrar la carpeta .venv lo deshace todo.

CustomTkinter solo dibuja. Toda la matematica de este archivo (la aritmetica
exacta, la eliminacion por filas, la clasificacion, el despeje y la
comprobacion) esta escrita con Python estandar: listas anidadas,
condicionales, bucles y funciones. No emplea NumPy, SciPy ni las funciones de
algebra lineal de math.""",
        blocks=[*ENGINE, *WINDOW_BLOCKS],
    ),
    Program(
        suffix="_consola",
        subtitle="Version de terminal",
        preamble="""COMO EJECUTARLO
---------------
    python "{filename}"

No hace falta instalar nada: el programa se construye utilizando unicamente
Python estandar, con listas anidadas, condicionales, bucles y funciones. No
emplea NumPy, SciPy ni las funciones de algebra lineal de math.""",
        blocks=[*ENGINE, *CONSOLE_BLOCKS],
    ),
]

RULE = "# " + "=" * 70
LOCAL_PACKAGES = ("core", "ui", "gui", "deliverables")

def header(program: Program) -> str:
    """
    What the file says about itself: which program it is and how to run it.

    The cover page is a separate document, so nothing here names anybody. It is
    a raw docstring because the Windows instructions carry a path, and a
    backslash inside an ordinary string is an escape sequence Python complains
    about.
    """
    return f'''r"""
PROGRAMA {PROGRAM_NUMBER} - Grupo {GROUP_NUMBER}
{PROGRAM_TITLE}
{program.subtitle}

Asignatura: Algebra Lineal (MTM0120)

{program.preamble.format(filename=program.filename())}
"""'''

def is_local_import(node: ast.stmt) -> bool:
    """Whether this import points at another module of this project."""
    if isinstance(node, ast.ImportFrom):
        if node.level > 0:  # from .matrix import ...
            return True
        root = (node.module or "").split(".")[0]
        return root in LOCAL_PACKAGES
    if isinstance(node, ast.Import):
        return any(alias.name.split(".")[0] in LOCAL_PACKAGES for alias in node.names)
    return False

def is_type_checking_block(node: ast.stmt) -> bool:
    """`if TYPE_CHECKING:` only exists to help a type checker; drop it."""
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "TYPE_CHECKING"
    )

def imports_only_type_checking(node: ast.stmt) -> bool:
    """`from typing import TYPE_CHECKING` goes when its block goes."""
    return (
        isinstance(node, ast.ImportFrom)
        and node.module == "typing"
        and all(alias.name == "TYPE_CHECKING" for alias in node.names)
    )

def last_line(node: ast.stmt) -> int:
    """
    The last line a statement covers.

    `end_lineno` is optional in the AST because a hand-built tree may not carry
    positions, but everything here comes from `ast.parse`, where it is always
    set. Falling back to the first line keeps the type checker happy without
    inventing a case that can happen.
    """
    return node.end_lineno or node.lineno

def translate_comments(source: str, missing: list[str]) -> str:
    """
    Swap every `#` comment for its Spanish.

    The comments are found with `tokenize` rather than by looking for a `#`,
    because a `#` inside a string is not a comment and must not be touched.
    Line count never changes, so nothing downstream has to be renumbered.
    """
    lines = source.splitlines()
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)

    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        row, column = token.start
        spanish = COMMENTS.get(token.string)
        if spanish is None:
            missing.append(token.string)
            continue
        lines[row - 1] = lines[row - 1][:column] + spanish

    return "\n".join(lines)

def as_docstring(text: str, indent: str) -> list[str]:
    """Write a piece of text back out as a triple-quoted docstring."""
    if "\n" not in text:
        return [f'{indent}"""{text}"""']
    body = [f"{indent}{line}".rstrip() for line in text.splitlines()]
    return [f'{indent}"""', *body, f'{indent}"""']

def translate_docstrings(source: str, missing: list[str]) -> str:
    """
    Swap every function and class docstring for its Spanish.

    Module docstrings are skipped: `split_module` drops those, and the Spanish
    block heading written by this file takes their place. Replacements are
    applied from the bottom up so that changing the length of one docstring
    cannot move the line numbers of the ones not yet reached.
    """
    lines = source.splitlines()
    edits: list[tuple[int, int, list[str]]] = []

    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        english = ast.get_docstring(node)
        if english is None:
            continue
        spanish = DOCSTRINGS.get(english)
        if spanish is None:
            missing.append(english.splitlines()[0])
            continue
        quote = node.body[0]
        indent = " " * quote.col_offset
        edits.append((quote.lineno - 1, last_line(quote), as_docstring(spanish, indent)))

    for start, end, replacement in sorted(edits, reverse=True):
        lines[start:end] = replacement

    return "\n".join(lines)

def named(alias: ast.alias) -> str:
    """`numpy as np` or just `sys`, whichever the import wrote."""
    return f"{alias.name} as {alias.asname}" if alias.asname else alias.name

def split_module(
    path: Path, plain: set[str], grouped: dict[str, set[str]], missing: list[str]
) -> str:
    """
    Take one module apart, adding its imports to the shared collections and
    returning the code it defines, translated into Spanish.

    Whole lines are kept verbatim so that every comment survives; only the
    ranges belonging to the module docstring and to the imports are cut out.
    """
    source = path.read_text(encoding="utf-8")
    source = translate_comments(source, missing)
    source = translate_docstrings(source, missing)
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
                # Gathered by module, so two files asking for different names
                # out of the same one end up on a single line. A missing module
                # means `from . import x`, which `is_local_import` already took.
                grouped.setdefault(node.module, set()).update(
                    named(alias) for alias in node.names
                )

    body = "\n".join(line for i, line in enumerate(lines) if i not in cut)
    return body.strip("\n")

def render_imports(plain: set[str], grouped: dict[str, set[str]]) -> str:
    """Every import the file needs, merged, deduplicated and in order."""
    lines = [f"import {name}" for name in sorted(plain)]
    lines.extend(
        f"from {module} import {', '.join(sorted(names))}"
        for module, names in sorted(grouped.items())
    )
    return "\n".join(lines)

def block_heading(title: str, description: str) -> str:
    """The Spanish comment that documents one block of the handed-in file."""
    lines = [RULE, f"# BLOQUE: {title}", "#"]
    lines.extend(f"# {line}".rstrip() for line in description.splitlines())
    lines.append(RULE)
    return "\n".join(lines)

def build(program: Program) -> tuple[str, list[str]]:
    """Assemble one whole file, and report anything left untranslated."""
    plain: set[str] = set()
    grouped: dict[str, set[str]] = {}
    blocks: list[str] = []
    missing: list[str] = []

    for block in program.blocks:
        plain.update(block.imports)
        body = (
            block.code
            if block.code
            else split_module(Path(block.source), plain, grouped, missing)
        )
        blocks.append(f"{block_heading(block.title, block.description)}\n\n{body}")

    text = "\n\n\n".join(
        [header(program), render_imports(plain, grouped), *blocks]
    ) + "\n"
    return text, missing

def write(program: Program) -> None:
    """Build one program, check that it compiles, and say where it landed."""
    text, missing = build(program)

    if missing:
        print(f"No se puede construir {program.filename()}:")
        print("falta traducir esto en translations.py\n")
        for text_in_english in missing:
            print(f"  {text_in_english}")
        sys.exit(1)

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
    """Build every program that can be handed in."""
    for program in PROGRAMS:
        write(program)

if __name__ == "__main__":
    main()
