"""
The window itself: what there is on the left, the open one on the right.

The sidebar lists what works. A program that has not been written has no row,
the same way this repository has no module for it: a list of things that do
nothing is a plan, and a plan does not belong in a menu. Pages are built the
first time they are opened and kept afterwards, so coming back to one finds the
matrix that was typed into it still there.

Run it from the root of the repository, the same way as the terminal version:

    python -m gui
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import customtkinter as ctk

from . import theme
from .pages.gauss import GaussPage
from .pages.operations import OperationsPage
from .widgets import Card

@dataclass(frozen=True)
class Module:
    """One row of the sidebar."""

    key: str
    glyph: str
    name: str

# The arithmetic comes first because everything else is written in terms of it.
# Gauss and Gauss-Jordan share one row: they are two settings of one method, and
# the choice between them belongs inside the page, not in the menu.
MODULES = (
    Module("operations", "⊞", "Operaciones Matriciales"),
    Module("gauss", "▦", "Eliminación Gaussiana"),
)

SIDEBAR_WIDTH = 268

class NavRow(ctk.CTkFrame):
    """
    One clickable row of the sidebar.

    A button would have been shorter, but a button holds one label and this row
    holds two, the glyph and the name, which have to change colour apart. So it
    is a frame that listens for a click on itself and on every child, because a
    click landing on the text is still a click on the row.
    """

    def __init__(self, master: Any, module: Module, select: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent", corner_radius=theme.NAV_RADIUS)
        self._module = module
        self._active = False

        self._glyph = ctk.CTkLabel(
            self, text=module.glyph, width=18, font=theme.font("body"), text_color=theme.ACCENT
        )
        self._glyph.pack(side="left", padx=(12, 8), pady=8)
        self._name = ctk.CTkLabel(
            self, text=module.name, anchor="w", font=theme.font("body"), text_color=theme.INK
        )
        self._name.pack(side="left", fill="x", expand=True, padx=(0, 12))

        for widget in (self, self._glyph, self._name):
            widget.bind("<Button-1>", lambda _event: select(module.key))
            widget.bind("<Enter>", lambda _event: self._hover(True))
            widget.bind("<Leave>", lambda _event: self._hover(False))
            widget.configure(cursor="hand2")

    def set_active(self, active: bool) -> None:
        self._active = active
        self.configure(fg_color=theme.ACCENT if active else "transparent")
        self._glyph.configure(text_color=theme.ON_ACCENT if active else theme.ACCENT)
        self._name.configure(text_color=theme.ON_ACCENT if active else theme.INK)

    def _hover(self, inside: bool) -> None:
        if self._active:
            return
        self.configure(fg_color=theme.FIELD if inside else "transparent")

class Application(ctk.CTk):
    """The window: a sidebar, a scrolling page, and one theme switch."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("light")
        theme.load_fonts()

        self.title("Álgebra Lineal · MTM0120")
        self.geometry("1180x800")
        self.minsize(960, 640)
        self.configure(fg_color=theme.BACKGROUND)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._rows: dict[str, NavRow] = {}
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._open: str | None = None

        self._build_sidebar()
        self._container = ctk.CTkScrollableFrame(self, fg_color=theme.BACKGROUND)
        self._container.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=20)
        self._container.grid_columnconfigure(0, weight=1)

        self.select(MODULES[0].key)

    # ----- The sidebar -----

    def _build_sidebar(self) -> None:
        sidebar = Card(self, width=SIDEBAR_WIDTH)
        sidebar.grid(row=0, column=0, sticky="nsw", padx=20, pady=20)
        sidebar.pack_propagate(False)

        identity = ctk.CTkFrame(sidebar, fg_color="transparent")
        identity.pack(fill="x", padx=14, pady=(16, 14))

        ctk.CTkLabel(
            identity,
            text="∑",
            width=30,
            height=30,
            corner_radius=9,
            fg_color=theme.ACCENT,
            text_color=theme.ON_ACCENT,
            font=theme.font("badge"),
        ).pack(side="left", padx=(0, 10))

        names = ctk.CTkFrame(identity, fg_color="transparent")
        names.pack(side="left")
        ctk.CTkLabel(
            names, text="Álgebra Lineal", font=theme.font("brand"), text_color=theme.INK
        ).pack(anchor="w")
        ctk.CTkLabel(
            names, text="MTM0120 · UAM", font=theme.font("small"), text_color=theme.FAINT
        ).pack(anchor="w")

        self._switch = ctk.CTkButton(
            identity,
            text="◐",
            width=30,
            height=30,
            corner_radius=15,
            fg_color=theme.FIELD,
            hover_color=theme.FIELD_HOVER,
            text_color=theme.INK,
            font=theme.font("body"),
            command=self._toggle_theme,
        )
        self._switch.pack(side="right")

        ctk.CTkFrame(sidebar, height=2, fg_color=theme.BORDER, corner_radius=0).pack(
            fill="x", padx=14
        )

        navigation = ctk.CTkFrame(sidebar, fg_color="transparent")
        navigation.pack(fill="both", expand=True, padx=10, pady=10)
        for module in MODULES:
            row = NavRow(navigation, module, self.select)
            row.pack(fill="x", pady=1)
            self._rows[module.key] = row

    def _toggle_theme(self) -> None:
        dark = not theme.is_dark()
        theme.set_dark(dark)
        self._switch.configure(text="◑" if dark else "◐")

    # ----- Opening a page -----

    def select(self, key: str) -> None:
        """Show the page of one module, building it the first time it is asked for."""
        if key == self._open:
            return
        if self._open is not None:
            self._pages[self._open].pack_forget()
            self._rows[self._open].set_active(False)

        if key not in self._pages:
            self._pages[key] = self._build_page(key)
        self._pages[key].pack(fill="x", padx=20, pady=(4, 40))
        self._rows[key].set_active(True)
        self._open = key

    def _build_page(self, key: str) -> ctk.CTkFrame:
        if key == "operations":
            return OperationsPage(self._container)
        if key == "gauss":
            return GaussPage(self._container)
        raise KeyError(f"No page is registered for {key!r}.")

def main() -> None:
    """Open the window and hand control over to it."""
    Application().mainloop()
