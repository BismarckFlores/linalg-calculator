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
from .pages.bisection import BisectionPage
from .pages.determinant import DeterminantPage
from .pages.echelon import EchelonPage
from .pages.gauss import GaussPage
from .pages.inverse import InversePage
from .pages.lu import LUPage
from .pages.operations import OperationsPage
from .pages.roman import RomanPage
from .pages.vectors import VectorsPage
from .widgets import WHEEL_STEP, Card, GlyphBadge, Wide, PageHeader, SectionTitle, LinkButton

@dataclass(frozen=True)
class Module:
    """Una fila del menu de la izquierda."""

    key: str
    glyph: str
    name: str
    description: str = ""

@dataclass(frozen=True)
class Group:
    """Un titulo del menu lateral, y las paginas que van debajo de el."""

    name: str
    modules: tuple[Module, ...]

# El menu, por lo que se quiere hacer y dentro de cada grupo por prioridad:
# primero la pagina que resuelve un sistema, que es lo que mas se pide y con lo
# que abre la ventana, y despues sus herramientas. Matrices va de lo basico (las
# operaciones) a lo que se calcula con ellas: la inversa, la factorizacion LU y
# el determinante, que lee la diagonal de esa factorizacion. Gauss y Gauss-Jordan
# comparten fila, porque son dos ajustes de un mismo metodo y la eleccion entre
# ellos va dentro de la pagina. Vectores tiene una sola pagina, pero conserva su
# titulo para que una segunda tenga donde aterrizar.
GROUPS = (
    Group("Sistemas Lineales", (
        Module("gauss", "▦", "Eliminación Gaussiana", "Resuelve sistemas con Gauss o Gauss-Jordan, clasifica sus soluciones y comprueba el resultado."),
        Module("echelon", "▧", "Formas Escalonadas", "Comprueba las propiedades de una matriz escalonada, reduce por filas y localiza sus pivotes."),
    )),
    Group("Matrices", (
        Module("operations", "⊞", "Operaciones Matriciales", "Suma, resta y multiplica matrices; calcula productos por escalares y transpuestas."),
        Module("inverse", "⁻¹", "Matriz Inversa", "Calcula la inversa mediante Gauss-Jordan, verifica los productos y resuelve Ax = b."),
        Module("lu", "LU", "Factorización LU", "Descompone una matriz en factores triangulares y resuelve sistemas por sustitución."),
        Module("determinant", "|A|", "Determinante", "Calcula determinantes por cofactores o factorización LU y consulta el procedimiento."),
    )),
    Group("Vectores", (
        Module("vectors", "↗", "Operaciones Vectoriales", "Suma y resta vectores, multiplica por escalares y estudia combinaciones lineales."),
    )),
    Group("Sistemas Numéricos", (
        Module("bases", "⇄", "Conversiones", "Convierte números entre decimal y otras bases, incluyendo la representación romana."),
        Module("roman", "Ⅻ", "Aritmética Romana", "Suma, resta y multiplica números romanos con el desarrollo de cada operación."),
    )),
    Group("Métodos Numéricos", (
        Module("bisection", "½", "Método de Bisección", "Grafica una función y aproxima una raíz con intervalos, pasos y tabla de iteraciones."),
    )),
)

# Todas las herramientas, en el orden en que el menu las dibuja.
MODULES = tuple(module for group in GROUPS for module in group.modules)
HOME = Module("home", "⌂", "Inicio")

SIDEBAR_WIDTH = 268

def scrolls_itself(widget: Any) -> bool:
    """Si lo que hay bajo el puntero tiene desplazamiento propio que hacer."""
    while widget is not None:
        if isinstance(widget, tkinter.Text) and widget.yview() != (0.0, 1.0):
            return True
        widget = getattr(widget, "master", None)
    return False

class HomePage(ctk.CTkFrame):
    """El catalogo usa el mismo registro y navegacion que el menu lateral."""

    def __init__(self, master: Any, select: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        PageHeader(self, "⌂", "Inicio", "Elige una herramienta para comenzar.").pack(anchor="w", pady=(0, 18))
        self._shortcuts: dict[str, LinkButton] = {}
        self._sections = []
        self._columns = 0
        for group in GROUPS:
            count = len(group.modules)
            SectionTitle(self, group.name, f"{count} {'herramienta' if count == 1 else 'herramientas'}").pack(fill="x", pady=(16, 10))
            grid = ctk.CTkFrame(self, fg_color="transparent")
            grid.pack(fill="x")
            cards = []
            for module in group.modules:
                card = Card(grid)
                heading = ctk.CTkFrame(card, fg_color="transparent")
                heading.pack(fill="x", padx=20, pady=(20, 10))
                GlyphBadge(heading, module.glyph, size=32).pack(side="left", padx=(0, 10))
                ctk.CTkLabel(heading, text=module.name, font=theme.font("heading"), text_color=theme.INK).pack(side="left")
                description = ctk.CTkLabel(card, text=module.description, font=theme.font("body"),
                    text_color=theme.MUTED, justify="left", anchor="nw", wraplength=260)
                description.pack(fill="x", padx=20, pady=(0, 10))
                button = LinkButton(card, "Abrir  →", lambda key=module.key: select(key))
                button.pack(anchor="e", padx=14, pady=(0, 14))
                self._shortcuts[module.key] = button
                cards.append((card, description))
            self._sections.append((grid, cards))
        self.bind("<Configure>", self._layout)

    def _layout(self, event: Any) -> None:
        columns = 2 if event.width >= 720 else 1
        for grid, cards in self._sections:
            if columns != self._columns:
                grid.grid_columnconfigure(0, weight=1, uniform="home")
                grid.grid_columnconfigure(1, weight=1 if columns == 2 else 0, uniform="home" if columns == 2 else "")
                for index, (card, _description) in enumerate(cards):
                    card.grid(row=index // columns, column=index % columns, sticky="nsew",
                              padx=(0, 12) if columns == 2 and index % 2 == 0 else 0, pady=(0, 12))
            for _card, description in cards:
                description.configure(wraplength=max(200, event.width // columns - 64))
        self._columns = columns


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

        self._glyph = GlyphBadge(self, module.glyph, size=32)
        self._glyph.pack(side="left", padx=(8, 10), pady=4)
        self._name = ctk.CTkLabel(
            self, text=module.name, anchor="w", font=theme.font("body"), text_color=theme.INK
        )
        self._name.pack(side="left", fill="x", expand=True, padx=(0, 12))

        for widget in (self, *self._glyph.parts(), self._name):
            widget.bind("<Button-1>", lambda _event: select(module.key))
            widget.bind("<Enter>", lambda _event: self._hover(True))
            widget.bind("<Leave>", lambda _event: self._hover(False))
            widget.configure(cursor="hand2")

    def set_active(self, active: bool) -> None:
        self._active = active
        self.configure(fg_color=theme.ACCENT if active else "transparent")
        self._glyph.set_active(active)
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
        self.select(HOME.key)

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
        # CTk usa unidades de 1 px en Windows y 30 px en Linux. Nuestro
        # WHEEL_STEP cuenta unidades: fijarlas evita avances casi invisibles.
        for frame in (self._container, self._navigation):
            frame._parent_canvas.configure(yscrollincrement=30)
        for sequence in ("<Button-4>", "<Button-5>", "<MouseWheel>"):
            self.unbind_all(sequence)
            self.bind_all(sequence, self._wheel, add=True)
        # Con Shift la rueda va a los lados. Tk elige el enlace mas especifico, asi
        # que con Shift apretado solo suena este y no se desliza dos veces.
        for sequence in ("<Shift-Button-4>", "<Shift-Button-5>", "<Shift-MouseWheel>"):
            self.bind_all(sequence, self._sideways, add=True)

    def _sideways(self, event: Any) -> None:
        """Con Shift, una muesca mueve a lo ancho la franja que este bajo el puntero."""
        widget = event.widget
        while widget is not None:
            if isinstance(widget, Wide):
                right = event.num == 5 or getattr(event, "delta", 0) < 0
                widget.scroll(1 if right else -1)
                return
            widget = getattr(widget, "master", None)

    def _wheel(self, event: Any) -> None:
        """Una muesca: baja la pagina, salvo que algo bajo el puntero la quiera."""
        if scrolls_itself(event.widget):
            return
        widget = event.widget
        while widget is not None:
            if widget is self._navigation:
                canvas = self._navigation._parent_canvas
                if canvas.yview() != (0.0, 1.0):
                    up = event.num == 4 or getattr(event, "delta", 0) > 0
                    canvas.yview_scroll(-WHEEL_STEP if up else WHEEL_STEP, "units")
                    return
                break
            widget = getattr(widget, "master", None)
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

        navigation = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", corner_radius=0)
        navigation.pack(fill="both", expand=True, padx=10, pady=10)
        self._navigation = navigation
        navigation._parent_canvas.bind("<Configure>", lambda _event: self._show_nav_row(), add=True)
        home_row = NavRow(navigation, HOME, self.select)
        home_row.pack(fill="x", pady=(0, 10))
        self._rows[HOME.key] = home_row
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
        # Una ventana baja necesita desplazar el menu. La fila elegida debe
        # quedar a la vista tambien al seleccionar una pagina desde codigo.
        self._show_nav_row()
        self._container._parent_canvas.yview_moveto(0.0)

    def _show_nav_row(self) -> None:
        """Mantiene la seleccion a la vista cuando el menu necesita desplazarse."""
        if self._open is None:
            return
        canvas = self._navigation._parent_canvas
        height = max(self._navigation.winfo_height(), 1)
        row = self._rows[self._open]
        top = canvas.yview()[0] * height
        if row.winfo_y() < top:
            canvas.yview_moveto(row.winfo_y() / height)
        elif row.winfo_y() + row.winfo_height() > top + canvas.winfo_height():
            canvas.yview_moveto((row.winfo_y() + row.winfo_height() - canvas.winfo_height()) / height)

    def _build_page(self, key: str) -> ctk.CTkFrame:
        if key == HOME.key:
            return HomePage(self._container, self.select)
        if key == "bisection":
            return BisectionPage(self._container)
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
        if key == "determinant":
            return DeterminantPage(self._container)
        if key == "lu":
            return LUPage(self._container)
        raise KeyError(f"No hay ninguna página registrada para {key!r}.")

def main() -> None:
    """Abre la ventana y le cede el control."""
    Application().mainloop()
