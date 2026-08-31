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
from pathlib import Path

from translations import COMMENTS, DOCSTRINGS

# ---------------------------------------------------------------------
# What the handed-in file is. The cover page is a separate document, so
# only these two things have to be right here.
# ---------------------------------------------------------------------

GROUP_NUMBER = "x"

PROGRAM_NUMBER = 1
PROGRAM_TITLE = "Solución de Sistemas de Ecuaciones Lineales por Eliminación por Filas"

# ---------------------------------------------------------------------
# The blocks, in the order they have to appear, each with the Spanish
# heading that documents it in the handed-in file.
# ---------------------------------------------------------------------

Block = tuple[str, str, str]

BLOCKS: list[Block] = [
    (
        "core/scalar.py",
        "EL NÚMERO EXACTO",
        "Cada entrada de una matriz se guarda como una fracción exacta, no como\n"
        "un decimal. Por eso un tercio se imprime como 1/3 y no como\n"
        "0.3333333333333333, y por eso la eliminación no acumula error de\n"
        "redondeo: el resultado coincide con el hecho a mano.",
    ),
    (
        "core/matrix.py",
        "LA MATRIZ",
        "Un rectángulo de números exactos y las operaciones que no necesitan\n"
        "explicarse: suma, resta, producto, y las tres operaciones elementales\n"
        "por filas (intercambiar, multiplicar por un número, sumar un múltiplo\n"
        "de otra fila). Los índices se cuentan desde 1, como en el pizarrón:\n"
        "a_23 es elem(2, 3).",
    ),
    (
        "core/steps.py",
        "EL REGISTRO DEL PASO A PASO",
        "Guarda la matriz inicial y, por cada operación elemental, la matriz de\n"
        "antes, la etiqueta de lo que se hizo (f_2 -> f_2 + 3*f_1) y la matriz\n"
        "de después. Es lo que permite imprimir la matriz en cada paso.",
    ),
    (
        "core/worksheet.py",
        "LA PIZARRA",
        "Junta una matriz con su registro. Es el único sitio donde una operación\n"
        "elemental se hace y se apunta a la vez, de modo que ningún algoritmo\n"
        "tiene que acordarse de ir dejando constancia. Las operaciones que no\n"
        "cambian nada no se apuntan, para que el paso a paso no tenga relleno.",
    ),
    (
        "core/elimination.py",
        "LA ELIMINACIÓN POR FILAS",
        "El método de Gauss: busca un pivote en cada columna, lo lleva a 1 y hace\n"
        "ceros por debajo. Si una columna está toda a cero de esa fila hacia\n"
        "abajo no tiene pivote y se salta, que es lo que hace que la escalera\n"
        "quede irregular cuando hay variables libres.",
    ),
    (
        "core/systems.py",
        "LA CLASIFICACIÓN Y LA SOLUCIÓN DEL SISTEMA",
        "Clasifica el sistema comparando rangos (Rouché-Frobenius):\n"
        "  rango(A) < rango(A|b)                sin solución\n"
        "  rango(A) = rango(A|b) < incógnitas   infinitas soluciones\n"
        "  rango(A) = rango(A|b) = incógnitas   solución única\n"
        "Cuando la solución es única, despeja las incógnitas hacia atrás, de la\n"
        "última a la primera, guardando cada paso del despeje.",
    ),
    (
        "core/verification.py",
        "LA COMPROBACIÓN DE LA SOLUCIÓN",
        "Sustituye los valores hallados en el sistema ORIGINAL y compara los dos\n"
        "lados de cada ecuación. No mira nada de la eliminación a propósito: si\n"
        "comprobara sobre la matriz escalonada estaría comprobando el algoritmo\n"
        "contra sí mismo. La comparación es exacta, sin tolerancia, porque no\n"
        "hubo redondeo en ningún momento.",
    ),
    (
        "ui/presentation.py",
        "EL TEXTO QUE SE MUESTRA",
        "Convierte los objetos anteriores en las frases que lee una persona.\n"
        "Aquí viven las tres clasificaciones con las palabras exactas que pide\n"
        "el enunciado, la barra que separa A de b en la matriz aumentada, y los\n"
        "nombres de las incógnitas.",
    ),
    (
        "ui/prompts.py",
        "LA LECTURA DE DATOS POR TECLADO",
        "Pide el número de ecuaciones m, el número de variables n, y después\n"
        "cada coeficiente por su nombre: a_11, a_12, ..., b_1. Si la respuesta\n"
        "no sirve, vuelve a preguntar; ninguna entrada equivocada corta el\n"
        "programa.",
    ),
    (
        "deliverables/program1.py",
        "EL PROGRAMA PRINCIPAL",
        "Ordena el trabajo en siete secciones numeradas igual que los requisitos\n"
        "del enunciado: entrada de datos, matriz aumentada inicial, eliminación\n"
        "por filas, sistema equivalente, clasificación, solución y comprobación.",
    ),
]

RULE = "# " + "=" * 70
LOCAL_PACKAGES = ("core", "ui", "deliverables")

def header() -> str:
    """
    What the file says about itself. The cover page is a separate document,
    so this only identifies the program and states the restriction it obeys.
    """
    return f'''"""
PROGRAMA {PROGRAM_NUMBER} - Grupo {GROUP_NUMBER}
{PROGRAM_TITLE}

Asignatura: Algebra Lineal (MTM0120)

El programa se construye utilizando unicamente Python estandar: listas
anidadas, condicionales, bucles y funciones. No emplea NumPy, SciPy ni las
funciones de algebra lineal de math.
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
        edits.append((quote.lineno - 1, quote.end_lineno, as_docstring(spanish, indent)))

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
        span = range(node.lineno - 1, node.end_lineno)

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
            else:
                # Gathered by module, so two files asking for different names
                # out of the same one end up on a single line.
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

def build() -> tuple[str, list[str]]:
    """Assemble the whole file, and report anything left untranslated."""
    plain: set[str] = set()
    grouped: dict[str, set[str]] = {}
    blocks: list[str] = []
    missing: list[str] = []

    for filename, title, description in BLOCKS:
        body = split_module(Path(filename), plain, grouped, missing)
        blocks.append(f"{block_heading(title, description)}\n\n{body}")

    text = "\n\n\n".join([header(), render_imports(plain, grouped), *blocks]) + "\n"
    return text, missing

def main() -> None:
    """Build the file, check that it compiles, and say where it landed."""
    text, missing = build()

    if missing:
        print("No se puede construir: falta traducir esto en translations.py\n")
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
    target = out / f"Programa {PROGRAM_NUMBER}_Grupo{GROUP_NUMBER}.py"
    target.write_text(text, encoding="utf-8")

    print(f"Escrito: {target}")
    print(f"  {len(text.splitlines())} lineas, {len(BLOCKS)} bloques, sin dependencias")
    print(f"  Todo el texto del archivo esta en castellano.")
    print(f"  Se ejecuta con:  python '{target.name}'")

if __name__ == "__main__":
    main()
