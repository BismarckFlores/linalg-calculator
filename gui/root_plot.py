"""Gráfica de funciones reales para los métodos con intervalo."""

import math
import sys
import tkinter
from typing import Any

import customtkinter as ctk

from core.real_function import RealFunction, sample_function
from core.root_bracket import BracketResult

from . import theme
from .widgets import LinkButton


class RootPlot(ctk.CTkFrame):
    """Lienzo con zoom y arrastre; no consulta puntos ni muestra valores al cursor."""

    def __init__(self, master: Any, result: BracketResult | None = None, *,
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
        self._points = sample_function(self._function, a, b)
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
            self._points = sample_function(self._function, x0, x1)
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
        plot = RootPlot(popup, self._result, function=self._function, expandable=False)
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
