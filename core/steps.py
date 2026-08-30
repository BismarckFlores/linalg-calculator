"""
The step by step: every elementary row operation, with the matrix before it and
the matrix after it.

A `StepLog` is a chain of row-equivalent matrices. `snapshot(k)` gives the k-th
link, `snapshot(0)` being the matrix you started from, and that single method is
the whole 'anterior / siguiente' of any interface: the terminal walks it with
Enter, the window walks it with two buttons, and neither needs to recompute
anything.

The labels are written in the notation the course uses: `f_2 -> f_2 + 3*f_1`.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .scalar import NumberLike, format_factor

if TYPE_CHECKING:
    # Only the type checker needs this; importing it at runtime would be circular.
    from .matrix import Matrix

def label_swap(i: int, j: int) -> str:
    """f_i <-> f_j"""
    return f"f_{i} <-> f_{j}"

def label_scale(i: int, factor: NumberLike) -> str:
    """f_i -> k*f_i"""
    return f"f_{i} -> {format_factor(factor)}*f_{i}"

def label_add_scaled(i: int, j: int, factor: NumberLike) -> str:
    """f_i -> f_i + k*f_j, dropping the factor when it is exactly 1 or -1."""
    if factor == 1:
        return f"f_{i} -> f_{i} + f_{j}"
    if factor == -1:
        return f"f_{i} -> f_{i} - f_{j}"
    return f"f_{i} -> f_{i} + {format_factor(factor)}*f_{j}"

@dataclass(frozen=True)
class Step:
    """One elementary operation: what it looked like before, what it did, after."""

    before: "Matrix"
    label: str
    after: "Matrix"
    note: str = ""

    def render(self) -> list[str]:
        """The step drawn as `before --[ label ]-> after`."""
        return _side_by_side(
            str(self.before).splitlines(),
            f"--[ {self.label} ]->",
            str(self.after).splitlines(),
        )

    def __str__(self) -> str:
        return "\n".join(self.render())

class StepLog:
    """The starting matrix and every operation applied to it, in order."""

    def __init__(self, initial: "Matrix", title: str = "") -> None:
        self.initial = initial
        self.title = title
        self._steps: list[Step] = []

    def record(self, before: "Matrix", label: str, after: "Matrix", note: str = "") -> "Matrix":
        """Append one operation and hand back its result, so calls can chain."""
        self._steps.append(Step(before, label, after, note))
        return after

    def annotate(self, text: str) -> None:
        """Attach a remark to the step just recorded, for an interface to show."""
        if not self._steps:
            raise ValueError("There is no step to annotate yet.")
        last = self._steps[-1]
        self._steps[-1] = Step(last.before, last.label, last.after, text)

    @property
    def steps(self) -> tuple[Step, ...]:
        return tuple(self._steps)

    @property
    def result(self) -> "Matrix":
        """Where the chain ends: the initial matrix if nothing was applied."""
        return self._steps[-1].after if self._steps else self.initial

    def snapshot(self, index: int) -> "Matrix":
        """
        The matrix after `index` operations; `snapshot(0)` is the initial one.

        This is what a 'previous / next' control calls, and the only reason the
        log keeps the matrices instead of just the labels.
        """
        if not 0 <= index <= len(self._steps):
            raise IndexError(f"There are {len(self._steps)} steps, none at index {index}.")
        if index == 0:
            return self.initial
        return self._steps[index - 1].after

    def is_empty(self) -> bool:
        """True when the matrix was already in its final form."""
        return not self._steps

    def __len__(self) -> int:
        return len(self._steps)

    def __iter__(self) -> Iterator[Step]:
        return iter(self._steps)

    def __getitem__(self, index: int) -> Step:
        return self._steps[index]

    def summary(self) -> str:
        """Just the numbered operations, no matrices."""
        if self.is_empty():
            return "No operations."
        return "\n".join(
            f"{number}. {step.label}" for number, step in enumerate(self._steps, start=1)
        )

    def render(self) -> list[str]:
        """The whole trace, one block per step."""
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
    """Centre a block of lines inside `height` rows, padding above and below."""
    missing = height - len(lines)
    if missing <= 0:
        return list(lines)
    above = missing // 2
    return [""] * above + list(lines) + [""] * (missing - above)

def _side_by_side(left: list[str], middle: str, right: list[str]) -> list[str]:
    """Two matrices with the operation between them, on the middle row."""
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