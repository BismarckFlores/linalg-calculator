"""Matrices, registros y factores presentados en varias herramientas."""

from core.linear_algebra.lu import Factorization
from core.linear_algebra.handlers.matrix import Matrix
from core.linear_algebra.handlers.steps import StepLog
from ui.presentation import pretty_label


def matrix_text(matrix: Matrix, bar_after: int | None = None) -> str:
    rows = []
    for row in matrix.data:
        cells = list(map(str, row))
        if bar_after is not None:
            cells.insert(bar_after, "|")
        rows.append("[ " + "; ".join(cells) + " ]")
    return "\n".join(rows)


def matrix_steps(log: StepLog, initial: str = "Matriz inicial", *, bar_after: int | None = None) -> tuple[str, ...]:
    return (
        f"{initial}\n{matrix_text(log.initial, bar_after)}",
        *(f"{pretty_label(step.label)}\n{matrix_text(step.after, bar_after)}" for step in log),
    )


def factorization_text(found: Factorization) -> str:
    parts = [
        "L", matrix_text(found.lower), "U", matrix_text(found.upper),
        f"Rango: {found.rank} · Intercambios: {found.swaps}",
        "La matriz es singular." if found.singular else "La matriz es invertible.",
    ]
    if found.permuted:
        parts.extend(("P", matrix_text(found.permutation), f"Orden de las filas: {found.row_order}"))
    parts.extend((
        "PA = LU" if found.permuted else "A = LU",
        matrix_text(found.product),
        "La comprobación exacta se cumple." if found.holds else "La comprobación exacta falló.",
    ))
    return "\n".join(parts)
