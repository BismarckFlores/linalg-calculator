"""Biseccion: entrada, resultado, grafica y el recorrido de los intervalos."""

import math
import sys
import tkinter
from typing import Any

import customtkinter as ctk

from core.bisection import (
    BisectionCriterion, BisectionError, BisectionResult, BisectionStop,
    bisect, sample_bisection,
)

from .. import theme
from ..widgets import Card, ErrorBanner, PageHeader, PrimaryButton, ResultsPage, SectionTitle


BISECTION_CRITERIA = {
    "Ancho del intervalo": BisectionCriterion.WIDTH,
    "Residuo |f(c)|": BisectionCriterion.RESIDUAL,
    "Error relativo (%)": BisectionCriterion.RELATIVE,
}
BISECTION_POLYNOMIAL = "x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10"
BISECTION_EXAMPLES = {
    "Polinomio del Excel": (BISECTION_POLYNOMIAL, "0.6", "1", "0.0001", "Residuo |f(c)|"),
    "Raíz de 2": ("x^2 - 2", "1", "2", "0.0001", "Ancho del intervalo"),
    "Potencia décima": ("x^10 - 1", "0", "1.3", "0.0001", "Ancho del intervalo"),
}
BISECTION_PAGE_SIZE = 15


def bisection_text(value: float | None, full: bool = False) -> str:
    """El redondeo pertenece a la presentacion, nunca al calculo."""
    return "—" if value is None else format(value, ".17g" if full else ".10g")


class BisectionPlot(ctk.CTkFrame):
    """Lienzo con zoom y arrastre; no consulta puntos ni muestra valores al cursor."""

    def __init__(self, master: Any, result: BisectionResult) -> None:
        super().__init__(master, fg_color="transparent")
        self._result = result
        self._drag_origin: tuple[int, int, tuple[float, ...]] | None = None
        self._points: tuple[tuple[float, float | None], ...] = ()
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 10))
        for text, command in (
            ("+  Acercar", lambda: self.zoom(0.7)),
            ("−  Alejar", lambda: self.zoom(1 / 0.7)),
            ("Restablecer", self.reset),
        ):
            ctk.CTkButton(
                controls, text=text, command=command, width=100, height=30,
                fg_color=theme.FIELD, hover_color=theme.FIELD_HOVER,
                text_color=theme.INK, font=theme.font("button"), corner_radius=15,
            ).pack(side="left", padx=(0, 8))
        self._plot_canvas = tkinter.Canvas(
            self, width=1, height=300, highlightthickness=0, borderwidth=0, cursor="fleur",
        )
        self._plot_canvas.pack(fill="x")
        self._plot_canvas.bind("<Configure>", lambda _event: self._paint())
        self._plot_canvas.bind("<ButtonPress-1>", self._start_drag)
        self._plot_canvas.bind("<B1-Motion>", self._drag)
        self._plot_canvas.bind("<ButtonRelease-1>", self._end_drag)
        self.bind("<Destroy>", lambda event: theme.off_change(self._paint) if event.widget is self else None)
        theme.on_change(self._paint)
        self.reset()

    def reset(self) -> None:
        result = self._result
        a, b = result.initial_a, result.initial_b
        self._points = sample_bisection(result.function, a, b)
        values = [y for _, y in self._points if y is not None]
        low, high = min([0.0, *values]), max([0.0, *values])
        # Normalizar evita que el margen desborde con ordenadas cercanas a float.max.
        scale = max(abs(low), abs(high)) or 1.0
        self._y_scale = scale
        padding = max((high / scale - low / scale) * 0.1, 0.1)
        limit = sys.float_info.max / scale
        ymin = max(-limit, low / scale - padding)
        ymax = min(limit, high / scale + padding)
        # El eje vertical se transforma en unidades de scale para que la resta
        # entre ordenadas grandes y de signo contrario siga siendo finita.
        self._view = (a, b, ymin, ymax)
        self._paint()

    def _set_view(self, view: tuple[float, ...]) -> None:
        x0, x1, y0, y1 = view
        if not all(math.isfinite(v) for v in (
            *view, x1 - x0, y1 - y0, y0 * self._y_scale, y1 * self._y_scale,
        )):
            return
        if x0 >= x1 or y0 >= y1:
            return
        if x0 == x0 + (x1 - x0) / 2 or y0 == y0 + (y1 - y0) / 2:
            return
        if (x0, x1) != self._view[:2]:
            self._points = sample_bisection(self._result.function, x0, x1)
        self._view = view
        self._paint()

    def zoom(self, factor: float) -> None:
        x0, x1, y0, y1 = self._view
        mx, my = x0 + (x1 - x0) / 2, y0 + (y1 - y0) / 2
        dx, dy = (x1 - x0) * factor / 2, (y1 - y0) * factor / 2
        self._set_view((mx - dx, mx + dx, my - dy, my + dy))

    def _start_drag(self, event: Any) -> None:
        self._drag_origin = (event.x, event.y, self._view)

    def _drag(self, event: Any) -> None:
        if self._drag_origin is None:
            return
        px, py, (x0, x1, y0, y1) = self._drag_origin
        width = max(self._plot_canvas.winfo_width() - 84, 1)
        height = max(self._plot_canvas.winfo_height() - 52, 1)
        dx = (event.x - px) / width * (x1 - x0)
        dy = (event.y - py) / height * (y1 - y0)
        self._set_view((x0 - dx, x1 - dx, y0 + dy, y1 + dy))

    def _end_drag(self, _event: Any) -> None:
        self._drag_origin = None

    def _paint(self) -> None:
        if not self.winfo_exists() or not hasattr(self, "_view"):
            return
        canvas = self._plot_canvas
        canvas.configure(background=theme.resolve(theme.CARD))
        canvas.delete("all")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 120:
            return
        left, top, right, bottom = 64, 18, width - 20, height - 34
        x0, x1, y0, y1 = self._view
        sx = lambda x: left + (x - x0) / (x1 - x0) * (right - left)
        sy = lambda y: bottom - (y - y0) / (y1 - y0) * (bottom - top)
        ink, muted = theme.resolve(theme.INK), theme.resolve(theme.MUTED)
        for i in range(5):
            fraction = i / 4
            x, y = x0 + (x1 - x0) * fraction, y0 + (y1 - y0) * fraction
            px, py = left + (right - left) * fraction, bottom - (bottom - top) * fraction
            canvas.create_line(px, top, px, bottom, fill=theme.resolve(theme.BORDER))
            canvas.create_line(left, py, right, py, fill=theme.resolve(theme.BORDER))
            canvas.create_text(px, bottom + 16, text=f"{x:.5g}", fill=muted, font=theme.font("small"))
            canvas.create_text(left - 8, py, text=f"{y * self._y_scale:.4g}", anchor="e", fill=muted, font=theme.font("small"))
        if y0 <= 0 <= y1:
            canvas.create_line(left, sy(0), right, sy(0), fill=muted, width=2)
        if x0 <= 0 <= x1:
            canvas.create_line(sx(0), top, sx(0), bottom, fill=muted, width=2)
        previous = None
        for x, y in self._points:
            scaled_y = y / self._y_scale if y is not None else None
            point = (sx(x), sy(scaled_y)) if scaled_y is not None and y0 <= scaled_y <= y1 else None
            # Un salto de casi toda la altura no se une como si fuera una raiz.
            if point and previous and abs(point[1] - previous[1]) < (bottom - top) * 0.8:
                canvas.create_line(*previous, *point, fill=theme.ACCENT, width=2)
            previous = point
        for x, color, label in (
            (self._result.initial_a, muted, "a"),
            (self._result.initial_b, muted, "b"),
            (self._result.root, theme.ORANGE, "c"),
        ):
            if x0 <= x <= x1:
                px = sx(x)
                canvas.create_line(px, top, px, bottom, fill=color, dash=(4, 4))
                canvas.create_text(px, top + 7, text=label, fill=color, font=theme.font("small"))
        canvas.create_text(right, height - 9, text="x", fill=ink, font=theme.font("small"))
        canvas.create_text(left + 18, top - 7, text="f(x)", anchor="sw", fill=ink, font=theme.font("small"))


class BisectionPage(ResultsPage):
    """La pagina conserva el calculo y navega su traza sin volver a resolverlo."""

    def __init__(self, master: Any) -> None:
        super().__init__(master)
        self._result: BisectionResult | None = None
        self._step_index = 0
        self._table_page = 0
        self._variables: list[ctk.StringVar] = []
        PageHeader(
            self, "½", "Método de Bisección",
            "Encuentra una raíz de f(x) = 0 reduciendo un intervalo a la mitad.",
        ).pack(anchor="w", pady=(0, 18))
        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)
        self._function = self._field(inside, "Función f(x)", BISECTION_POLYNOMIAL)
        boxes = ctk.CTkFrame(inside, fg_color="transparent")
        boxes.pack(fill="x", pady=(14, 0))
        boxes.grid_columnconfigure((0, 1), weight=1, uniform="bisection")
        self._a = self._grid_field(boxes, 0, 0, "Extremo inferior a", "0.6")
        self._b = self._grid_field(boxes, 0, 1, "Extremo superior b", "1")
        self._tolerance = self._grid_field(boxes, 1, 0, "Tolerancia E", "0.0001")
        self._limit = self._grid_field(boxes, 1, 1, "Máximo de iteraciones", "100")
        self._label(inside, "Criterio de parada").pack(anchor="w", pady=(12, 4))
        self._criterion = ctk.CTkOptionMenu(
            inside, values=list(BISECTION_CRITERIA), command=lambda _value: self._changed(),
            fg_color=theme.FIELD, button_color=theme.FIELD_HOVER,
            button_hover_color=theme.BORDER, text_color=theme.INK, font=theme.font("body"),
        )
        self._criterion.pack(fill="x")
        self._muted(
            inside, "Ancho: b − a < E · Residuo: |f(c)| < E · Relativo: |(c − c anterior)/c| × 100 < E.\n"
            "En el criterio relativo, E se escribe en porcentaje: 1 significa 1 %.",
        ).pack_configure(pady=(8, 0))
        self._help_button = ctk.CTkButton(
            inside, text="Sintaxis y condiciones  ▾", command=self._toggle_help,
            fg_color="transparent", hover_color=theme.FIELD, text_color=theme.MUTED,
            font=theme.font("button"), anchor="w",
        )
        self._help_button.pack(fill="x", pady=(12, 0))
        self._help = ctk.CTkLabel(
            inside, text="Escribe el lado izquierdo de f(x) = 0. Multiplica con * y usa ^ o ** para potencias.\n"
            "Funciones: sin, cos, tan, exp, ln, log, log10, sqrt, abs. Constantes: pi, e.\n"
            "En a, b y E también se aceptan fracciones y coma decimal.\n"
            "La garantía exige continuidad en todo [a, b] y signos opuestos en los extremos.\n"
            "La gráfica y un muestreo finito no demuestran continuidad.",
            justify="left", anchor="w", wraplength=580,
            font=theme.font("small"), text_color=theme.MUTED,
        )
        examples = ctk.CTkFrame(inside, fg_color="transparent")
        examples.pack(fill="x", pady=(14, 0))
        self._label(examples, "Cargar ejemplo").pack(side="left", padx=(0, 12))
        self._examples = ctk.CTkOptionMenu(
            examples, values=list(BISECTION_EXAMPLES), command=self._example,
            fg_color=theme.FIELD, button_color=theme.FIELD_HOVER,
            button_hover_color=theme.BORDER, text_color=theme.INK, font=theme.font("body"),
        )
        self._examples.set("Elegir ejemplo…")
        self._examples.pack(side="left", fill="x", expand=True)
        self._error = ErrorBanner(inside)
        buttons = ctk.CTkFrame(inside, fg_color="transparent")
        buttons.pack(fill="x", pady=(18, 0))
        PrimaryButton(buttons, "Calcular raíz  →", self._calculate).pack(side="right")
        self._error.appear_before(buttons)

    def _label(self, master: Any, text: str) -> ctk.CTkLabel:
        return ctk.CTkLabel(master, text=text, font=theme.font("small"), text_color=theme.MUTED)

    def _field(self, master: Any, label: str, value: str) -> ctk.CTkEntry:
        self._label(master, label).pack(anchor="w", pady=(0, 4))
        variable = ctk.StringVar(value=value)
        self._variables.append(variable)
        entry = ctk.CTkEntry(
            master, textvariable=variable, height=40, font=theme.font("mono"),
            fg_color=theme.FIELD, border_color=theme.BORDER, text_color=theme.INK,
            corner_radius=theme.FIELD_RADIUS,
        )
        entry.pack(fill="x")
        entry.bind("<Return>", lambda _event: self._calculate())
        variable.trace_add("write", lambda *_args: self._changed())
        return entry

    def _grid_field(self, master: Any, row: int, column: int, label: str, value: str) -> ctk.CTkEntry:
        box = ctk.CTkFrame(master, fg_color="transparent")
        box.grid(row=row, column=column, sticky="ew", padx=(0, 8) if column == 0 else (8, 0), pady=(0, 10))
        return self._field(box, label, value)

    def _toggle_help(self) -> None:
        if self._help.winfo_manager():
            self._help.pack_forget()
            self._help_button.configure(text="Sintaxis y condiciones  ▾")
        else:
            self._help.pack(fill="x", pady=(8, 0), after=self._help_button)
            self._help_button.configure(text="Sintaxis y condiciones  ▴")

    def _changed(self) -> None:
        self._clear_output()
        self._result = None
        if hasattr(self, "_error"):
            self._error.hide()

    def _example(self, name: str) -> None:
        function, a, b, tolerance, criterion = BISECTION_EXAMPLES[name]
        self._examples.set(name)
        for entry, value in zip((self._function, self._a, self._b, self._tolerance, self._limit),
                                (function, a, b, tolerance, "100")):
            entry.delete(0, "end")
            entry.insert(0, value)
        self._criterion.set(criterion)
        self._changed()

    def _calculate(self) -> None:
        self._changed()
        try:
            try:
                limit = int(self._limit.get())
            except ValueError:
                raise BisectionError("El máximo de iteraciones debe ser un entero entre 1 y 1000.") from None
            result = bisect(
                self._function.get(), self._a.get(), self._b.get(), self._tolerance.get(),
                criterion=BISECTION_CRITERIA[self._criterion.get()], max_iterations=limit,
            )
        except BisectionError as problem:
            self._error.show(str(problem))
            return
        self._result = result
        self._step_index = self._table_page = 0
        self._draw_answer(result)
        self._draw_plot(result)
        if result.steps:
            self._draw_steps()
            self._draw_table()

    def _reason(self, result: BisectionResult) -> str:
        if result.stop is BisectionStop.ZERO:
            return "f(c) = 0 en la aritmética del programa."
        if result.stop is BisectionStop.LIMIT:
            return "Se alcanzó el máximo de iteraciones sin cumplir la tolerancia."
        if result.stop is BisectionStop.STAGNATION:
            return "La precisión numérica ya no permite dividir el intervalo; no se alcanzó la tolerancia."
        name = next(name for name, criterion in BISECTION_CRITERIA.items() if criterion is result.criterion)
        return f"{name} menor que E = {bisection_text(result.tolerance)}."

    def _draw_answer(self, result: BisectionResult) -> None:
        inside = self._card("Resultado", f"{len(result.steps)} iteraciones")
        ctk.CTkLabel(
            inside, text=f"x ≈ {result.root:.12g}", font=theme.font("title"),
            text_color=theme.ACCENT if result.converged else theme.ORANGE,
        ).pack(anchor="w")
        self._muted(inside, self._reason(result)).pack_configure(pady=(8, 12))
        details = (
            ("Intervalo final [a, b]", f"[{result.a:.12g}, {result.b:.12g}]"),
            ("Cota geométrica en x", bisection_text(result.bound)),
            ("Comprobación en la función original", f"f({result.root:.12g}) = {result.function(result.root):.12g}"),
            ("Residuo |f(c)|", bisection_text(abs(result.value))),
            ("Error relativo aproximado (%)", bisection_text(result.steps[-1].relative_error) if result.steps else "—"),
        )
        for label, value in details:
            self._muted(inside, label)
            ctk.CTkLabel(inside, text=value, font=theme.font("mono"), text_color=theme.INK).pack(anchor="w", pady=(0, 8))
        self._muted(
            inside, "La cota en x supone continuidad. El residuo y el cambio relativo no son el error real en x.\n"
            "Los valores se redondean solo al mostrarlos; el cálculo usa toda la precisión disponible.",
        )

    def _draw_plot(self, result: BisectionResult) -> None:
        inside = ctk.CTkFrame(self._add_card(), fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=22)
        SectionTitle(inside, "La función y el intervalo").pack(fill="x", pady=(0, 12))
        self._plot = BisectionPlot(inside, result)
        self._plot.pack(fill="x")
        self._muted(inside, "Azul: f(x) · Límites a y b: intervalo inicial · Naranja: aproximación c.\n"
                    "Acerca con +, aleja con − y arrastra para mover. Restablecer recupera la vista inicial.\n"
                    "El muestreo puede omitir discontinuidades; los puntos fuera del dominio se dejan sin unir.")

    def _draw_steps(self) -> None:
        self._step_body, self._step_title = self._titled_card("Procedimiento paso a paso", " ")
        self._step_text = ctk.CTkLabel(
            self._step_body, text="", justify="left", anchor="w",
            font=theme.font("mono"), text_color=theme.INK, wraplength=580,
        )
        self._step_text.pack(fill="x")
        controls = ctk.CTkFrame(self._step_body, fg_color="transparent")
        controls.pack(fill="x", pady=(16, 0))
        self._previous = self._nav_button(controls, "‹  Anterior", lambda: self._move_step(-1))
        self._next = self._nav_button(controls, "Siguiente  ›", lambda: self._move_step(1))
        self._show_step()

    def _nav_button(self, master: Any, text: str, command: Any) -> ctk.CTkButton:
        button = ctk.CTkButton(
            master, text=text, command=command, width=110, height=30,
            fg_color=theme.FIELD, hover_color=theme.FIELD_HOVER,
            text_color=theme.INK, font=theme.font("button"), corner_radius=15,
        )
        button.pack(side="left", padx=(0, 8))
        return button

    def _move_step(self, delta: int) -> None:
        assert self._result is not None
        self._step_index = max(0, min(len(self._result.steps) - 1, self._step_index + delta))
        self._show_step()

    def _show_step(self) -> None:
        result = self._result
        assert result is not None
        step = result.steps[self._step_index]
        if self._step_index == len(result.steps) - 1:
            decision = self._reason(result)
        elif step.keep_left:
            decision = "f(a) y f(c) tienen signos opuestos: conservar [a, c], sustituir b por c."
        else:
            decision = "f(a) y f(c) tienen el mismo signo: conservar [c, b], sustituir a por c."
        self._step_title.set_badge(f"{step.index} / {len(result.steps)}")
        self._step_text.configure(text=(
            f"a = {step.a:.12g}    b = {step.b:.12g}\n"
            f"c = (a + b) / 2 = {step.c:.12g}\n\n"
            f"f(a) = {step.fa:.10g}\nf(b) = {step.fb:.10g}\nf(c) = {step.fc:.10g}\n\n"
            f"Ancho = {step.width:.10g}\n|f(c)| = {step.residual:.10g}\n"
            f"Error relativo (%) = {bisection_text(step.relative_error)}\n\n{decision}"
        ))
        self._previous.configure(state="normal" if self._step_index else "disabled")
        self._next.configure(state="normal" if self._step_index + 1 < len(result.steps) else "disabled")

    def _draw_table(self) -> None:
        inside = self._card("Tabla de iteraciones")
        self._muted(inside, "Ancho = b − a · Cota ≈ (b − a)/2 · Ea = |(c − c anterior)/c| × 100 %.\n"
                    "Ea no aplica en la primera iteración, si c = 0 o si no se puede representar.")
        self._full = ctk.CTkSwitch(
            inside, text="Mostrar 17 cifras significativas", command=self._show_table,
            font=theme.font("small"), text_color=theme.INK, progress_color=theme.ACCENT,
        )
        self._full.pack(anchor="w", pady=(12, 10))
        self._table = ctk.CTkFrame(inside, fg_color="transparent")
        self._table.pack(fill="x")
        controls = ctk.CTkFrame(inside, fg_color="transparent")
        controls.pack(fill="x", pady=(12, 0))
        self._table_previous = self._nav_button(controls, "‹  Anterior", lambda: self._move_table(-1))
        self._table_next = self._nav_button(controls, "Siguiente  ›", lambda: self._move_table(1))
        self._table_count = self._label(controls, "")
        self._table_count.pack(side="left", padx=12)
        self._show_table()

    def _move_table(self, delta: int) -> None:
        assert self._result is not None
        last = (len(self._result.steps) - 1) // BISECTION_PAGE_SIZE
        self._table_page = max(0, min(last, self._table_page + delta))
        self._show_table()

    def _show_table(self) -> None:
        assert self._result is not None
        for widget in self._table.winfo_children():
            widget.destroy()
        headers = ("i", "a", "b", "c", "f(a)", "f(b)", "f(c)", "Ancho", "Cota en x", "|f(c)|", "Ea (%)")
        start = self._table_page * BISECTION_PAGE_SIZE
        steps = self._result.steps[start:start + BISECTION_PAGE_SIZE]
        rows = [headers]
        for step in steps:
            rows.append((str(step.index), *(bisection_text(v, bool(self._full.get())) for v in (
                step.a, step.b, step.c, step.fa, step.fb, step.fc,
                step.width, step.bound, step.residual, step.relative_error,
            ))))
        for i, row in enumerate(rows):
            for j, text in enumerate(row):
                ctk.CTkLabel(
                    self._table, text=text, font=theme.font("label" if i == 0 else "mono_small"),
                    text_color=theme.ACCENT if j == 3 else theme.INK,
                    fg_color=theme.FIELD if i % 2 == 0 else theme.CARD,
                    anchor="e", padx=10, height=32,
                ).grid(row=i, column=j, sticky="nsew")
        total = len(self._result.steps)
        self._table_count.configure(text=f"{start + 1}–{start + len(steps)} de {total}")
        self._table_previous.configure(state="normal" if start else "disabled")
        self._table_next.configure(state="normal" if start + len(steps) < total else "disabled")
