from typing import Any

import customtkinter as ctk

from core.inverse import InverseResult, InverseSystem, SingularMatrix, invert, solve_with_inverse
from core.matrix import Matrix
from core.scalar import to_scalar
from ui.presentation import pretty_label

from .. import theme
from ..widgets import Card, ErrorBanner, PageHeader, PrimaryButton, SectionTitle, SegmentedControl


INVERSE_EXERCISES = {
    "Ejemplo 2×2": ("Inversa A⁻¹", "3 4\n5 6", "3\n7"),
    "Práctica 2.2": ("Inversa A⁻¹", "1 -2 -1\n-1 5 6\n5 -4 5", ""),
    "Teorema 2.3": ("Inversa A⁻¹", "2 3 4\n2 3 4\n2 3 4", ""),
    "Aplicación Ax=b": ("Aplicación Ax=b", "3 4\n5 6", "3\n7"),
    "Aplicación 3×3": (
        "Aplicación Ax=b", "1 0 -2\n3 1 -2\n-5 -1 9", "3\n7\n-16"
    ),
}

INVERSE_THEOREMS = """DEFINICIÓN — Si A es n×n, A⁻¹ existe cuando AA⁻¹ = Iₙ y A⁻¹A = Iₙ.

ORDEN 2 — Si A = [[a,b],[c,d]] y ad − bc ≠ 0, entonces
A⁻¹ = [[d,−b],[−c,a]] / (ad − bc). Si ad − bc = 0, A es singular.

SISTEMAS — Si A es invertible de orden n, entonces, para cada b ∈ ℝⁿ,
Ax = b tiene la solución única x = A⁻¹b.

OPERACIONES — Si A es invertible, (A⁻¹)⁻¹ = A y
(Aᵀ)⁻¹ = (A⁻¹)ᵀ. Si A y B son invertibles del mismo orden,
(AB)⁻¹ = B⁻¹A⁻¹.

TEOREMA DE LA MATRIZ INVERTIBLE — Para A cuadrada n×n, las condiciones
siguientes son equivalentes: todas son verdaderas o todas falsas.
a) A es invertible.
b) A es equivalente por filas a Iₙ.
c) A tiene n posiciones pivote.
d) Ax = 0 solo tiene la solución trivial.
e) Las columnas de A son linealmente independientes.
f) La transformación x ↦ Ax es uno a uno.
g) Ax = b tiene solución para toda b ∈ ℝⁿ.
h) Las columnas de A generan ℝⁿ.
i) La transformación x ↦ Ax mapea ℝⁿ sobre ℝⁿ.
j) Existe C de orden n con CA = Iₙ.
k) Existe D de orden n con AD = Iₙ.
l) Aᵀ es invertible."""


def parse_inverse_matrix(text: str) -> Matrix:
    rows = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        row = []
        for column_number, token in enumerate(line.replace(";", " ").split(), start=1):
            try:
                row.append(to_scalar(token))
            except (ValueError, TypeError):
                raise ValueError(
                    f"Fila {line_number}, columna {column_number}: "
                    f"'{token}' no es un número válido."
                ) from None
        rows.append(row)

    if not rows:
        raise ValueError("Escribe al menos una fila de la matriz A.")

    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("Todas las filas de A deben tener la misma cantidad de entradas.")

    return Matrix(rows)


def parse_inverse_vector(text: str, size: int) -> Matrix:
    tokens = text.replace(";", " ").split()
    if len(tokens) != size:
        raise ValueError(f"El vector b debe tener {size} entradas; tiene {len(tokens)}.")

    values = []
    for position, token in enumerate(tokens, start=1):
        try:
            values.append(to_scalar(token))
        except (ValueError, TypeError):
            raise ValueError(
                f"Entrada {position} de b: '{token}' no es un número válido."
            ) from None
    return Matrix.column_vector(values)


class InversePage(ctk.CTkFrame):
    def __init__(self, master: Any) -> None:
        super().__init__(master, fg_color="transparent")
        self._mode = "Inversa A⁻¹"
        self._result: Card | None = None
        self._step_log = None
        self._step_index = 0

        PageHeader(
            self,
            "⁻¹",
            "Matriz Inversa",
            "Gauss-Jordan con [A | Iₙ], comprobación y aplicación a Ax = b.",
        ).pack(anchor="w", pady=(0, 18))

        self._mode_control = SegmentedControl(
            self, ["Inversa A⁻¹", "Aplicación Ax=b"], self._pick_mode
        )
        self._mode_control.pack(anchor="w", pady=(0, 16))

        input_card = Card(self)
        input_card.pack(fill="x")
        inside = ctk.CTkFrame(input_card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)

        ctk.CTkLabel(
            inside, text="Ejercicio", font=theme.font("label"), text_color=theme.INK
        ).pack(anchor="w")
        ctk.CTkOptionMenu(
            inside, values=list(INVERSE_EXERCISES), command=self._load_exercise
        ).pack(anchor="w", pady=(6, 16))

        ctk.CTkLabel(
            inside,
            text="Matriz A: una fila por línea; separa las entradas con espacios.",
            font=theme.font("label"),
            text_color=theme.INK,
        ).pack(anchor="w")
        self._a_text = ctk.CTkTextbox(
            inside, height=155, font=theme.font("mono"), wrap="none"
        )
        self._a_text.pack(fill="x", pady=(6, 0))
        self._a_text.insert("1.0", "3 4\n5 6")
        self._a_text.bind("<KeyRelease>", lambda _event: self._clear_result())

        self._b_frame = ctk.CTkFrame(inside, fg_color="transparent")
        ctk.CTkLabel(
            self._b_frame,
            text="Vector b: una entrada por línea o separadas con espacios.",
            font=theme.font("label"),
            text_color=theme.INK,
        ).pack(anchor="w")
        self._b_text = ctk.CTkTextbox(
            self._b_frame, height=75, font=theme.font("mono"), wrap="none"
        )
        self._b_text.pack(fill="x", pady=(6, 0))
        self._b_text.insert("1.0", "3\n7")
        self._b_text.bind("<KeyRelease>", lambda _event: self._clear_result())

        self._error = ErrorBanner(inside)
        self._buttons = ctk.CTkFrame(inside, fg_color="transparent")
        self._buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(self._buttons, "Calcular  →", self._calculate).pack(side="right")
        self._error.appear_before(self._buttons)

        self._theorems = Card(self)
        self._theorems.pack(fill="x", pady=(16, 0))
        theorem_inside = ctk.CTkFrame(self._theorems, fg_color="transparent")
        theorem_inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(theorem_inside, "Teoremas", "Con sus condiciones").pack(
            fill="x", pady=(0, 10)
        )
        self._text_block(theorem_inside, INVERSE_THEOREMS, 330, wrap="word")

    def _pick_mode(self, mode: str) -> None:
        self._mode = mode
        self._clear_result()
        if mode == "Aplicación Ax=b":
            self._b_frame.pack(fill="x", pady=(16, 0), before=self._buttons)
        else:
            self._b_frame.pack_forget()

    def _load_exercise(self, name: str) -> None:
        mode, matrix, vector = INVERSE_EXERCISES[name]
        self._a_text.delete("1.0", "end")
        self._a_text.insert("1.0", matrix)
        self._b_text.delete("1.0", "end")
        self._b_text.insert("1.0", vector)
        self._mode_control.set(mode)
        self._pick_mode(mode)

    def _calculate(self) -> None:
        self._clear_result()
        try:
            matrix = parse_inverse_matrix(self._a_text.get("1.0", "end"))
            if not matrix.is_square():
                raise ValueError(
                    f"A debe ser cuadrada; recibí {matrix.rows}×{matrix.cols}."
                )

            solved = None
            if self._mode == "Aplicación Ax=b":
                constants = parse_inverse_vector(
                    self._b_text.get("1.0", "end"), matrix.rows
                )
                solved = solve_with_inverse(matrix, constants)
                result = solved.inverse_result
            else:
                result = invert(matrix)

        except SingularMatrix:
            self._error.show(
                "A es singular: su bloque izquierdo no se reduce a Iₙ. "
                "No existe A⁻¹ ni puede aplicarse x = A⁻¹b."
            )
            return
        except MemoryError:
            self._error.show(
                "No hay memoria suficiente para esta matriz. Prueba una de menor tamaño."
            )
            return
        except ArithmeticError:
            self._error.show("La comprobación exacta falló; revisa el cálculo.")
            return
        except ValueError as problem:
            self._error.show(str(problem))
            return

        self._error.hide()
        self._show(result, solved)

    def _show(self, result: InverseResult, solved: InverseSystem | None) -> None:
        self._result = Card(self)
        self._result.pack(fill="x", pady=(16, 0), before=self._theorems)
        inside = ctk.CTkFrame(self._result, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)

        SectionTitle(
            inside, "Resultado", f"Matriz de orden {result.original.rows}"
        ).pack(fill="x", pady=(0, 10))
        output = (
            f"A⁻¹ =\n{result.inverse}\n\n"
            f"A · A⁻¹ =\n{result.left_check}\n\n"
            f"A⁻¹ · A =\n{result.right_check}\n\n"
            "Ambos productos son la identidad."
        )
        if solved is not None:
            output += (
                f"\n\nAplicación: x = A⁻¹b\n"
                f"b =\n{solved.constants}\n\n"
                f"x =\n{solved.solution}\n\n"
                f"Comprobación: Ax =\n{solved.check}"
            )
        self._text_block(inside, output, 250)

        SectionTitle(
            inside, "Gauss-Jordan", "Operaciones sobre [A | Iₙ]"
        ).pack(fill="x", pady=(18, 10))
        self._step_log = result.reduction.log
        self._step_index = 0
        self._step_counter = ctk.CTkLabel(
            inside, text="", font=theme.font("label"), text_color=theme.INK
        )
        self._step_counter.pack(anchor="w")
        self._step_text = self._text_block(inside, "", 190)

        navigation = ctk.CTkFrame(inside, fg_color="transparent")
        navigation.pack(fill="x", pady=(10, 0))
        self._previous = ctk.CTkButton(
            navigation, text="‹ Anterior", command=lambda: self._move_step(-1)
        )
        self._previous.pack(side="left")
        self._next = ctk.CTkButton(
            navigation, text="Siguiente ›", command=lambda: self._move_step(1)
        )
        self._next.pack(side="right")
        self._update_step()

    def _text_block(
        self, master: Any, content: str, height: int, wrap: str = "none"
    ) -> ctk.CTkTextbox:
        box = ctk.CTkTextbox(
            master, height=height, font=theme.font("mono"), wrap=wrap
        )
        box.pack(fill="x")
        box.insert("1.0", content)
        box.configure(state="disabled")
        return box

    def _move_step(self, change: int) -> None:
        if self._step_log is None:
            return
        self._step_index = max(
            0, min(len(self._step_log), self._step_index + change)
        )
        self._update_step()

    def _update_step(self) -> None:
        if self._step_log is None:
            return
        count = len(self._step_log)
        if self._step_index == 0:
            caption = "Matriz inicial [A | Iₙ]"
        else:
            caption = pretty_label(self._step_log[self._step_index - 1].label)

        self._step_counter.configure(
            text=f"Paso {self._step_index} de {count}: {caption}"
        )
        self._step_text.configure(state="normal")
        self._step_text.delete("1.0", "end")
        self._step_text.insert(
            "1.0", str(self._step_log.snapshot(self._step_index))
        )
        self._step_text.configure(state="disabled")
        self._previous.configure(
            state="normal" if self._step_index > 0 else "disabled"
        )
        self._next.configure(
            state="normal" if self._step_index < count else "disabled"
        )

    def _clear_result(self) -> None:
        if self._result is not None:
            self._result.destroy()
            self._result = None
        self._step_log = None
        self._error.hide()
