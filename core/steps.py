"""
El paso a paso: cada operacion elemental de fila, con la matriz de antes y la de
despues.

Un StepLog es una cadena de matrices equivalentes por filas. snapshot(k) da el
eslabon k-esimo, y snapshot(0) es la matriz de la que se partio; ese unico
metodo es todo el 'anterior / siguiente' de cualquier interfaz: la terminal lo
recorre con Enter, la ventana con dos botones, y ninguna necesita recalcular
nada.

Las etiquetas van en la notacion que usa el curso: f_2 -> f_2 + 3*f_1.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .scalar import NumberLike, format_factor

if TYPE_CHECKING:
    # Solo lo necesita el verificador de tipos; importarlo en ejecucion seria circular.
    from .matrix import Matrix

def label_swap(i: int, j: int) -> str:
    """f_i <-> f_j"""
    return f"f_{i} <-> f_{j}"

def label_scale(i: int, factor: NumberLike) -> str:
    """f_i -> k*f_i"""
    return f"f_{i} -> {format_factor(factor)}*f_{i}"

def label_add_scaled(i: int, j: int, factor: NumberLike) -> str:
    """f_i -> f_i + k*f_j, omitiendo el factor cuando vale exactamente 1 o -1."""
    if factor == 1:
        return f"f_{i} -> f_{i} + f_{j}"
    if factor == -1:
        return f"f_{i} -> f_{i} - f_{j}"
    return f"f_{i} -> f_{i} + {format_factor(factor)}*f_{j}"

@dataclass(frozen=True)
class Step:
    """Una operacion elemental: como estaba antes, que se hizo, y como quedo."""

    before: "Matrix"
    label: str
    after: "Matrix"
    note: str = ""

    def render(self) -> list[str]:
        """El paso dibujado como  antes --[ etiqueta ]-> despues."""
        return _side_by_side(
            str(self.before).splitlines(),
            f"--[ {self.label} ]->",
            str(self.after).splitlines(),
        )

    def __str__(self) -> str:
        return "\n".join(self.render())

class StepLog:
    """La matriz inicial y todas las operaciones que se le aplicaron, en orden."""

    def __init__(self, initial: "Matrix", title: str = "") -> None:
        self.initial = initial
        self.title = title
        self._steps: list[Step] = []

    def record(self, before: "Matrix", label: str, after: "Matrix", note: str = "") -> "Matrix":
        """Anade una operacion y devuelve su resultado, para poder encadenar llamadas."""
        self._steps.append(Step(before, label, after, note))
        return after

    def annotate(self, text: str) -> None:
        """Anade una nota al paso recien registrado, para que la interfaz la muestre."""
        if not self._steps:
            raise ValueError("There is no step to annotate yet.")
        last = self._steps[-1]
        self._steps[-1] = Step(last.before, last.label, last.after, text)

    @property
    def steps(self) -> tuple[Step, ...]:
        return tuple(self._steps)

    @property
    def result(self) -> "Matrix":
        """Donde termina la cadena: la matriz inicial si no se aplico nada."""
        return self._steps[-1].after if self._steps else self.initial

    def snapshot(self, index: int) -> "Matrix":
        """
        La matriz despues de index operaciones; snapshot(0) es la inicial.

        Es lo que llama un control de 'anterior / siguiente', y la unica razon
        por la que el registro guarda las matrices y no solo las etiquetas.
        """
        if not 0 <= index <= len(self._steps):
            raise IndexError(f"There are {len(self._steps)} steps, none at index {index}.")
        if index == 0:
            return self.initial
        return self._steps[index - 1].after

    def is_empty(self) -> bool:
        """Cierto cuando la matriz ya estaba en su forma final."""
        return not self._steps

    def __len__(self) -> int:
        return len(self._steps)

    def __iter__(self) -> Iterator[Step]:
        return iter(self._steps)

    def __getitem__(self, index: int) -> Step:
        return self._steps[index]

    def summary(self) -> str:
        """Solo las operaciones numeradas, sin matrices."""
        if self.is_empty():
            return "No operations."
        return "\n".join(
            f"{number}. {step.label}" for number, step in enumerate(self._steps, start=1)
        )

    def render(self) -> list[str]:
        """La traza completa, un bloque por paso."""
        lines: list[str] = []
        if self.title:
            lines.extend([self.title, ""])
        if self.is_empty():
            lines.extend(str(self.initial).splitlines())
            lines.extend(["", "No operations."])
            return lines
        for number, step in enumerate(self._steps, start=1):
            lines.append(f"Step {number}:")
            lines.extend(step.render())
            if step.note:
                lines.append(f"  ({step.note})")
            lines.append("")
        return lines

    def __str__(self) -> str:
        return "\n".join(self.render())

def _pad_block(lines: list[str], height: int) -> list[str]:
    """Centra un bloque de lineas en una altura dada, rellenando arriba y abajo."""
    missing = height - len(lines)
    if missing <= 0:
        return list(lines)
    above = missing // 2
    return [""] * above + list(lines) + [""] * (missing - above)

def _side_by_side(left: list[str], middle: str, right: list[str]) -> list[str]:
    """Dos matrices con la operacion entre ellas, en la fila central."""
    height = max(len(left), len(right), 1)
    left = _pad_block(left, height)
    right = _pad_block(right, height)
    width = max((len(line) for line in left), default=0)
    middle_row = height // 2

    return [
        f"  {left[row].ljust(width)}  "
        f"{middle if row == middle_row else ' ' * len(middle)}  {right[row]}"
        for row in range(height)
    ]
