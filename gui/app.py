"""
La ventana en si: lo que hay a la izquierda, y lo abierto a la derecha.

El menu lateral lista lo que funciona. Un programa que no se ha escrito no tiene
fila, igual que este repositorio no tiene un modulo para el: una lista de cosas
que no hacen nada es un plan, y un plan no va en un menu. Las paginas se
construyen la primera vez que se abren y se conservan, asi que volver a una
encuentra todavia la matriz que se habia escrito en ella.

Se ejecuta desde la raiz del repositorio, igual que la version de terminal:

    python -m gui
"""

import tkinter
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import customtkinter as ctk

from . import theme
from .pages.bases import BasesPage
from .pages.echelon import EchelonPage
from .pages.gauss import GaussPage
from .pages.inverse import InversePage
from .pages.operations import OperationsPage
from .pages.roman import RomanPage
from .pages.vectors import VectorsPage
from .widgets import Card

@dataclass(frozen=True)
class Module:
    """Una fila del menu de la izquierda."""

    key: str
    glyph: str
    name: str

@dataclass(frozen=True)
class Group:
    """Un titulo del menu lateral, y las paginas que van debajo de el."""

    name: str
    modules: tuple[Module, ...]

# El menu, por los tres temas en que se ensena el curso, y dentro de cada uno
# en el orden en que se ensena: las operaciones con matrices antes de la
# eliminacion que se escribe con ellas, y leer la forma de una matriz despues
# de las dos, como la comprobacion que se hace al terminar. Gauss y
# Gauss-Jordan comparten fila, porque son dos ajustes de un mismo metodo y la
# eleccion entre ellos va dentro de la pagina.
#
# Vectores tiene hoy una sola pagina. Aun asi conserva su propio titulo: los
# tres temas se leen igual, y una segunda pagina de vectores tiene donde
# aterrizar.
GROUPS = (
    Group("Matrices", (
        Module("operations", "⊞", "Operaciones Matriciales"),
        Module("inverse", "⁻¹", "Matriz Inversa"),
        Module("gauss", "▦", "Eliminación Gaussiana"),
        Module("echelon", "▧", "Formas Escalonadas"),
    )),
    Group("Vectores", (
        Module("vectors", "↗", "Vectores en ℝⁿ"),
    )),
    Group("Sistemas Numéricos", (
        Module("bases", "⇄", "Conversiones"),
        Module("roman", "Ⅻ", "Números Romanos"),
    )),
)

# Todas las paginas, en el orden en que el menu las dibuja. La primera se abre.
MODULES = tuple(module for group in GROUPS for module in group.modules)

SIDEBAR_WIDTH = 268

# Cuanto mueve la pagina una muesca de la rueda, en unidades de 30 pixeles:
# unas tres lineas de texto, que es lo que hace todo lo demas en el escritorio.
WHEEL_STEP = 3

def scrolls_itself(widget: Any) -> bool:
    """Si lo que hay bajo el puntero tiene desplazamiento propio que hacer."""
    while widget is not None:
        if isinstance(widget, tkinter.Text) and widget.yview() != (0.0, 1.0):
            return True
        widget = getattr(widget, "master", None)
    return False

class NavRow(ctk.CTkFrame):
    """
    Una fila del menu sobre la que se puede pulsar.

    Un boton habria sido mas corto, pero un boton lleva una sola etiqueta y esta
    fila lleva dos, el simbolo y el nombre, que tienen que cambiar de color por
    separado. Asi que es un marco que escucha la pulsacion sobre si mismo y sobre
    cada hijo, porque una pulsacion sobre el texto sigue siendo sobre la fila.
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
    """La ventana: un menu, una pagina que se desplaza y un interruptor de tema."""

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

        self._wire_wheel()
        self.select(MODULES[0].key)

    # ----- La rueda del raton -----

    def _wire_wheel(self) -> None:
        """
        Hace que una muesca de la rueda desplace la pagina desde cualquier punto de
        la ventana.

        CustomTkinter ya asocia la rueda, pero solo responde sobre la zona que se
        desplaza y mueve treinta pixeles cada vez: dejar el puntero sobre el menu o
        sobre el cuadro de ecuaciones se comia la muesca, y una pagina larga pedia
        cuarenta. Esto sustituye esa asociacion en vez de sumarse a ella, para que
        nada se desplace dos veces.
        """
        for sequence in ("<Button-4>", "<Button-5>", "<MouseWheel>"):
            self.unbind_all(sequence)
            self.bind_all(sequence, self._wheel, add=True)

    def _wheel(self, event: Any) -> None:
        """Una muesca: baja la pagina, salvo que algo bajo el puntero la quiera."""
        if scrolls_itself(event.widget):
            return
        canvas = self._container._parent_canvas
        if canvas.yview() == (0.0, 1.0):
            return
        up = event.num == 4 or getattr(event, "delta", 0) > 0
        canvas.yview_scroll(-WHEEL_STEP if up else WHEEL_STEP, "units")

    # ----- El menu de la izquierda -----

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
        for index, group in enumerate(GROUPS):
            ctk.CTkLabel(
                navigation,
                text=group.name.upper(),
                font=theme.font("label"),
                text_color=theme.FAINT,
                anchor="w",
            ).pack(fill="x", padx=12, pady=(16 if index else 4, 6))
            for module in group.modules:
                row = NavRow(navigation, module, self.select)
                row.pack(fill="x", pady=1)
                self._rows[module.key] = row

    def _toggle_theme(self) -> None:
        dark = not theme.is_dark()
        theme.set_dark(dark)
        self._switch.configure(text="◑" if dark else "◐")

    # ----- Apertura de una pagina -----

    def select(self, key: str) -> None:
        """Muestra la pagina de un modulo, construyendola la primera vez que se pide."""
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

        # Una pagina se abre por su principio. Conservar el desplazamiento de la que
        # se acaba de dejar soltaria a alguien en mitad de otra que no ha leido.
        self.update_idletasks()
        self._container._parent_canvas.yview_moveto(0.0)

    def _build_page(self, key: str) -> ctk.CTkFrame:
        if key == "vectors":
            return VectorsPage(self._container)
        if key == "operations":
            return OperationsPage(self._container)
        if key == "inverse":
            return InversePage(self._container)
        if key == "echelon":
            return EchelonPage(self._container)
        if key == "gauss":
            return GaussPage(self._container)
        if key == "bases":
            return BasesPage(self._container)
        if key == "roman":
            return RomanPage(self._container)
        raise KeyError(f"No page is registered for {key!r}.")

def main() -> None:
    """Abre la ventana y le cede el control."""
    Application().mainloop()
