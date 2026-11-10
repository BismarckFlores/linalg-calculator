"""Pantallas de bisección y regla falsa. Comparten gráfica y recorrido."""

import math
import sys
import tkinter
from typing import Any

import customtkinter as ctk

from core.bisection import (
    BisectionCriterion, BisectionError, BisectionResult, BisectionStop,
    RealFunction, bisect, regula_falsi, sample_bisection,
)

from .. import theme
from ..widgets import (
    Card, ErrorBanner, LinkButton, MathBlock, MathLine, PageHeader, PrimaryButton,
    ResultsPage, SectionTitle, SegmentedControl, Stepper, Wide,
)


BISECTION_CRITERIA = {
    "Ancho del intervalo": BisectionCriterion.WIDTH,
    "Residuo |f(c)|": BisectionCriterion.RESIDUAL,
    "Error relativo (%)": BisectionCriterion.RELATIVE,
}
BISECTION_POLYNOMIAL = "x^4 - 5x^3 + 0.5x^2 - 11x + 10"
BISECTION_EXAMPLES = {
    "Polinomio del Excel": (BISECTION_POLYNOMIAL, "0.6", "1", "0.0001", "Residuo |f(c)|"),
    "Raíz de 2": ("x^2 - 2", "1", "2", "0.0001", "Ancho del intervalo"),
    "Potencia décima": ("x^10 - 1", "0", "1.3", "0.0001", "Ancho del intervalo"),
}
BISECTION_PAGE_SIZE = 15


def bisection_text(
    value: float | None, *, decimals: int | None = None,
) -> str:
    """El redondeo pertenece a la presentacion, nunca al calculo."""
    if value is None:
        return "—"
    if decimals is None:
        return format(value, ".10g")
    return format(value, f".{decimals}f")


class BisectionPlot(ctk.CTkFrame):
    """Lienzo con zoom y arrastre; no consulta puntos ni muestra valores al cursor."""

    def __init__(self, master: Any, result: BisectionResult | None = None, *,
                 function: RealFunction | None = None, expandable: bool = True) -> None:
        super().__init__(master, fg_color="transparent")
        self._result = result
        self._function = result.function if result else function
        self._popup = None
        self._drag_origin: tuple[int, int, tuple[float, ...]] | None = None
        self._points: tuple[tuple[float, float | None], ...] = ()
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 10))
        for text, command in (
            ("+  Acercar", lambda: self.zoom(0.7)),
            ("−  Alejar", lambda: self.zoom(1 / 0.7)),
            ("Restablecer", self.reset),
        ):
            LinkButton(controls, text, command).pack(side="left", padx=(0, 8))
        if expandable:
            LinkButton(controls, "Maximizar", self.maximize).pack(side="right")
        self._plot_canvas = tkinter.Canvas(
            self, width=1, height=300, highlightthickness=0, borderwidth=0, cursor="fleur",
        )
        self._plot_canvas.pack(fill="both", expand=True)
        self._plot_canvas.bind("<Configure>", lambda _event: self._paint())
        self._plot_canvas.bind("<ButtonPress-1>", self._start_drag)
        self._plot_canvas.bind("<B1-Motion>", self._drag)
        self._plot_canvas.bind("<ButtonRelease-1>", self._end_drag)
        for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self._plot_canvas.bind(event, self._wheel)
        theme.on_change(self._paint)
        self.reset()

    def reset(self) -> None:
        result = self._result
        a, b = (result.initial_a, result.initial_b) if result else (-10.0, 10.0)
        self._points = sample_bisection(self._function, a, b)
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
            self._points = sample_bisection(self._function, x0, x1)
        self._view = view
        self._paint()

    def zoom(self, factor: float) -> None:
        x0, x1, y0, y1 = self._view
        mx, my = x0 + (x1 - x0) / 2, y0 + (y1 - y0) / 2
        dx, dy = (x1 - x0) * factor / 2, (y1 - y0) * factor / 2
        self._set_view((mx - dx, mx + dx, my - dy, my + dy))

    def _wheel(self, event: Any) -> str:
        direction = 1 if getattr(event, "num", None) == 4 else -1 if getattr(event, "num", None) == 5 else getattr(event, "delta", 0)
        if direction:
            self.zoom(0.8 if direction > 0 else 1.25)
        return "break"

    def destroy(self) -> None:
        theme.off_change(self._paint)
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()
        super().destroy()

    def maximize(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.lift()
            return
        owner = self.winfo_toplevel()
        owner.update_idletasks()
        popup = self._popup = ctk.CTkToplevel(owner)
        popup.title("Gráfica de la función")
        popup.geometry(f"{owner.winfo_width()}x{owner.winfo_height()}+{owner.winfo_rootx()}+{owner.winfo_rooty()}")
        popup.transient(owner)
        LinkButton(popup, "Cerrar  ×", popup.destroy).pack(anchor="e", padx=12, pady=8)
        plot = BisectionPlot(popup, self._result, function=self._function, expandable=False)
        plot.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        plot._y_scale = self._y_scale
        plot._set_view(self._view)
        popup.bind("<Escape>", lambda _event: popup.destroy())
        popup.lift()

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
        for x, color, label in ((
            (self._result.initial_a, muted, "a"),
            (self._result.initial_b, muted, "b"),
            (self._result.root, theme.ORANGE, "c"),
        ) if self._result else ()):
            if x0 <= x <= x1:
                px = sx(x)
                canvas.create_line(px, top, px, bottom, fill=color, dash=(4, 4))
                canvas.create_text(px, top + 7, text=label, fill=color, font=theme.font("small"))
        canvas.create_text(right, height - 9, text="x", fill=ink, font=theme.font("small"))
        canvas.create_text(left + 18, top - 7, text="f(x)", anchor="sw", fill=ink, font=theme.font("small"))


class BisectionPage(ResultsPage):
    """La pagina conserva el calculo y navega su traza sin volver a resolverlo."""

    _glyph = "½"
    _title = "Método de Bisección"
    _subtitle = "Encuentra una raíz de f(x) = 0 reduciendo un intervalo a la mitad."
    _initial_inputs = (BISECTION_POLYNOMIAL, "0.6", "1", "0.0001")
    _example_data = BISECTION_EXAMPLES
    _criteria = BISECTION_CRITERIA
    _criterion_help = (
        "Ancho: b − a < E · Residuo: |f(c)| < E · Relativo: |(c − c anterior)/c| × 100 < E.\n"
        "En el criterio relativo, E se escribe en porcentaje: 1 significa 1 %."
    )
    _step_caption = "punto medio y cambio de signo"
    _estimate_formula = "(a + b) / 2"
    _solve = staticmethod(bisect)

    def __init__(self, master: Any) -> None:
        super().__init__(master)
        self._result: BisectionResult | None = None
        self._table_page = 0
        self._table_format = "Decimal"
        self._table_decimals = 5
        self._variables: list[ctk.StringVar] = []
        PageHeader(
            self, self._glyph, self._title, self._subtitle,
        ).pack(anchor="w", pady=(0, 18))
        card = Card(self)
        card.pack(fill="x")
        inside = ctk.CTkFrame(card, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)
        function, a, b, tolerance = self._initial_inputs
        self._function = self._field(inside, "Función f(x)", function)
        self._function.bind("<Return>", lambda _event: self._graph())
        self._variables[-1].trace_add("write", lambda *_args: self._function_changed())
        self._label(inside, "Cargar ejemplo").pack(anchor="w", pady=(14, 4))
        self._examples = SegmentedControl(inside, tuple(self._example_data), self._example)
        self._examples.set("")
        self._examples.pack(anchor="w")
        PrimaryButton(inside, "Graficar función  →", self._graph).pack(anchor="e", pady=(14, 0))
        self._graph_error = ErrorBanner(inside)
        self._preview_host = Card(self)
        self._controls = Card(self)
        inside = ctk.CTkFrame(self._controls, fg_color="transparent")
        inside.pack(fill="x", padx=24, pady=24)
        boxes = ctk.CTkFrame(inside, fg_color="transparent")
        boxes.pack(fill="x", pady=(14, 0))
        boxes.grid_columnconfigure((0, 1), weight=1, uniform="bisection")
        self._a = self._grid_field(boxes, 0, 0, "Extremo inferior a", a)
        self._b = self._grid_field(boxes, 0, 1, "Extremo superior b", b)
        self._tolerance = self._grid_field(boxes, 1, 0, "Tolerancia E", tolerance)
        self._limit = self._grid_field(boxes, 1, 1, "Máximo de iteraciones", "100")
        self._label(inside, "Criterio de parada").pack(anchor="w", pady=(12, 4))
        self._criterion = SegmentedControl(
            inside, tuple(self._criteria), lambda _value: self._changed(),
        )
        self._criterion.pack(anchor="w")
        self._muted(inside, self._criterion_help).pack_configure(pady=(8, 0))
        self._help_button = LinkButton(
            inside, "Sintaxis y condiciones  ▾", self._toggle_help,
            color=theme.MUTED, anchor="w",
        )
        self._help_button.pack(fill="x", pady=(12, 0))
        self._help = ctk.CTkLabel(
            inside, text="Escribe el lado izquierdo de f(x) = 0. Puedes usar 5x^3, 2(x+1) o 5*x^3.\n"
            "Usa ^ o ** para potencias y paréntesis en las funciones: sin(x), ln(x), etc.\n"
            "Funciones: sin, cos, tan, exp, ln, log, log10, sqrt, abs. Constantes: pi, e.\n"
            "En a, b y E también se aceptan fracciones y coma decimal.\n"
            "La garantía exige continuidad en todo [a, b] y signos opuestos en los extremos.\n"
            "La gráfica y un muestreo finito no demuestran continuidad.",
            justify="left", anchor="w", wraplength=580,
            font=theme.font("small"), text_color=theme.MUTED,
        )
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
        plot = getattr(self, "_plot", None)
        if plot is not None and plot.winfo_exists() and plot._result is not None:
            plot._result = None
            if plot._popup is not None and plot._popup.winfo_exists():
                plot._popup.destroy()
            plot._paint()
        if hasattr(self, "_error"):
            self._error.hide()

    def _function_changed(self) -> None:
        if not hasattr(self, "_controls"):
            return
        self._controls.pack_forget()
        self._preview_host.pack_forget()
        for child in self._preview_host.winfo_children():
            child.destroy()
        self._graph_error.hide()

    def _graph(self) -> None:
        try:
            function = RealFunction(self._function.get())
        except BisectionError as problem:
            self._graph_error.show(str(problem))
            return
        self._changed()
        self._graph_error.hide()
        for child in self._preview_host.winfo_children():
            child.destroy()
        self._preview_host.pack(fill="x", pady=(16, 0))
        SectionTitle(self._preview_host, "Gráfica de la función").pack(fill="x", padx=24, pady=(22, 12))
        self._plot = BisectionPlot(self._preview_host, function=function)
        self._plot.pack(fill="x", padx=24)
        self._muted(self._preview_host, "Vista inicial: x entre −10 y 10. Usa la rueda para acercar o alejar y arrastra para mover.\nInspecciona la gráfica antes de elegir [a, b]. El dibujo puede omitir discontinuidades; no demuestra continuidad.").pack_configure(padx=24, pady=(0, 22))
        self._controls.pack(fill="x", pady=(16, 0))

    def _example(self, name: str) -> None:
        function, a, b, tolerance, criterion = self._example_data[name]
        self._examples.set(name)
        for entry, value in zip((self._function, self._a, self._b, self._tolerance, self._limit),
                                (function, a, b, tolerance, "100")):
            entry.delete(0, "end")
            entry.insert(0, value)
        self._criterion.set(criterion)
        self._changed()
        self._graph()

    def _calculate(self) -> None:
        if not self._controls.winfo_manager():
            self._graph()
            return
        self._changed()
        try:
            try:
                limit = int(self._limit.get())
            except ValueError:
                raise BisectionError("El máximo de iteraciones debe ser un entero entre 1 y 1000.") from None
            result = self._solve(
                self._function.get(), self._a.get(), self._b.get(), self._tolerance.get(),
                criterion=self._criteria[self._criterion.get()], max_iterations=limit,
            )
        except BisectionError as problem:
            self._error.show(str(problem))
            return
        self._result = result
        self._table_page = 0
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
            return "La aproximación coincide con un extremo por precisión numérica y el intervalo ya no se reduce."
        name = next(name for name, criterion in self._criteria.items() if criterion is result.criterion)
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
            MathLine(inside, value).pack(anchor="w", pady=(0, 8))
        self._muted(
            inside, "La cota en x supone continuidad. El residuo y el cambio relativo no son el error real en x.\n"
            "Los valores se redondean solo al mostrarlos; el cálculo usa toda la precisión disponible.",
        )

    def _draw_plot(self, result: BisectionResult) -> None:
        inside = self._preview_host
        for child in inside.winfo_children():
            child.destroy()
        SectionTitle(inside, "La función y el intervalo").pack(fill="x", padx=24, pady=(22, 12))
        self._plot = BisectionPlot(inside, result)
        self._plot.pack(fill="x", padx=24)
        self._muted(inside, "Azul: f(x) · Límites a y b: intervalo inicial · Naranja: aproximación c.\n"
                    "Acerca con +, aleja con − y arrastra para mover. Restablecer recupera la vista inicial.\n"
                    "El muestreo puede omitir discontinuidades; los puntos fuera del dominio se dejan sin unir.").pack_configure(padx=24, pady=(0, 22))

    def _draw_steps(self) -> None:
        result = self._result
        assert result is not None
        captions = (
            "Intervalo inicial  [ a, b ]",
            *(f"Iteración {step.index}: {self._step_caption}" for step in result.steps),
        )
        self._walker, self._step_title = self._draw_walk(
            None, captions[0], captions=captions, draw_snapshot=self._draw_iteration,
        )

    def _draw_iteration(self, master: Any, index: int) -> None:
        """El contenido numerico; StepWalker ya pone el titulo y los controles."""
        result = self._result
        assert result is not None
        if index == 0:
            first = result.steps[0]
            MathBlock(master, (
                f"f(x) = {result.function.text}\n"
                f"a = {result.initial_a:.12g}    b = {result.initial_b:.12g}\n"
                f"f(a) = {first.fa:.10g}\nf(b) = {first.fb:.10g}\n"
                f"E = {bisection_text(result.tolerance)}"
            ), "left", "mono").pack(anchor="w")
            self._muted(master, "Los extremos tienen signos opuestos. La garantía de una raíz exige "
                        "continuidad en todo el intervalo.").pack_configure(pady=(14, 0))
            return
        step = result.steps[index - 1]
        if index == len(result.steps):
            decision = self._reason(result)
        elif step.keep_left:
            decision = "f(a) y f(c) tienen signos opuestos: conservar [a, c], sustituir b por c."
        else:
            decision = "f(a) y f(c) tienen el mismo signo: conservar [c, b], sustituir a por c."
        MathBlock(master, (
            f"a = {step.a:.12g}    b = {step.b:.12g}\n"
            f"c = {self._estimate_formula} = {step.c:.12g}\n\n"
            f"f(a) = {step.fa:.10g}\nf(b) = {step.fb:.10g}\nf(c) = {step.fc:.10g}\n\n"
            f"Ancho = {step.width:.10g}\n|f(c)| = {step.residual:.10g}\n"
            f"Error relativo (%) = {bisection_text(step.relative_error)}"
        ), "left", "mono").pack(anchor="w")
        self._muted(master, decision).pack_configure(pady=(14, 0))

    def _draw_table(self) -> None:
        inside, _heading = self._titled_card("Tabla de iteraciones", scrollable=False)
        self._muted(inside, "Ancho = b − a · Cota = max(c − a, b − c) · Ea = |(c − c anterior)/c| × 100 %.\n"
                    "Ea no aplica en la primera iteración, si c = 0 o si no se puede representar.", width=480)
        formatting = ctk.CTkFrame(inside, fg_color="transparent")
        formatting.pack(fill="x", pady=(12, 8))
        self._format_choice = SegmentedControl(
            formatting, ("Decimal", "Automático"), self._choose_table_format,
        )
        self._format_choice.set(self._table_format)
        self._format_choice.pack(side="left", padx=(0, 16))
        self._decimal_controls = ctk.CTkFrame(formatting, fg_color="transparent")
        self._decimal_controls.pack(side="left")
        self._label(self._decimal_controls, "Decimales").pack(side="left", padx=(0, 8))
        self._decimal_count = Stepper(
            self._decimal_controls, self._table_decimals, minimum=0, maximum=17,
            command=self._choose_table_decimals,
        )
        self._decimal_count.pack(side="left")
        if self._table_format != "Decimal":
            self._decimal_controls.pack_forget()
        self._muted(
            inside, "El formato solo cambia la vista; el cálculo conserva su precisión.\n"
            "Si un valor pequeño se muestra como cero, aumenta los decimales o usa Automático.",
            width=480,
        ).pack_configure(pady=(0, 10))
        self._table_wide = Wide(inside)
        self._table_wide.pack(fill="x")
        self._table = ctk.CTkFrame(self._table_wide.content, fg_color="transparent")
        self._table.pack(fill="x")
        controls = ctk.CTkFrame(inside, fg_color="transparent")
        controls.pack(fill="x", pady=(12, 0))
        self._table_previous = LinkButton(controls, "‹  Anterior", lambda: self._move_table(-1))
        self._table_previous.pack(side="left")
        self._table_next = LinkButton(controls, "Siguiente  ›", lambda: self._move_table(1))
        self._table_next.pack(side="right")
        self._table_count = self._label(controls, "")
        self._table_count.pack(side="left", expand=True, padx=12)
        self._show_table()

    def _choose_table_format(self, selected: str) -> None:
        self._table_format = selected
        if selected == "Decimal":
            self._decimal_controls.pack(side="left")
        else:
            self._decimal_controls.pack_forget()
        self._show_table()

    def _choose_table_decimals(self, decimals: int) -> None:
        self._table_decimals = decimals
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
            rows.append((str(step.index), *(bisection_text(
                v, decimals=self._table_decimals if self._table_format == "Decimal" else None,
            ) for v in (
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
        self._table_wide.refresh()


class RegulaFalsiPage(BisectionPage):
    """Usa la secante para estimar c y conserva la misma pantalla de intervalos."""

    _glyph = "RF"
    _title = "Regula Falsi"
    _subtitle = "Aproxima una raíz por el cruce de la secante con el eje x."
    _initial_inputs = ("x^3 - 4.23603x^2 - 2.73620x - 13.09037", "4.95", "5.5", "0.01")
    _example_data = {
        "Ejercicio de la guía": (*_initial_inputs, "Error relativo (%)"),
        "Raíz de 2": ("x^2 - 2", "1", "2", "0.0001", "Residuo |f(c)|"),
        "Potencia décima": ("x^10 - 1", "0", "1.3", "0.0001", "Residuo |f(c)|"),
    }
    _criteria = {
        "Error relativo (%)": BisectionCriterion.RELATIVE,
        "Residuo |f(c)|": BisectionCriterion.RESIDUAL,
    }
    _criterion_help = (
        "c es el cruce de la secante con el eje x. Se conserva el intervalo con cambio de signo.\n"
        "Relativo: |(c − c anterior)/c| × 100 < E. En este criterio, 1 significa 1 %.\n"
        "Residuo: |f(c)| < E. Un cambio relativo pequeño puede ocurrir aunque el residuo siga siendo grande."
    )
    _step_caption = "cruce de la secante y cambio de signo"
    _estimate_formula = "b − f(b)(a − b) / (f(a) − f(b))"
    _solve = staticmethod(regula_falsi)
