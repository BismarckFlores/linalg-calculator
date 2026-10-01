"""
El aspecto de la ventana: colores, tipografia y el interruptor claro/oscuro.

Cada color es una pareja (claro, oscuro), que es justo lo que lee CustomTkinter.
Escribirlos asi es lo que hace que cambiar de tema sea una sola llamada: no se
reconstruye ningun elemento ni se recalcula ningun color, la libreria
simplemente lee la otra mitad de cada pareja que ya tenia.

Las dos excepciones son las formas dibujadas a mano: los corchetes que rodean
una matriz van sobre un lienzo, que no sabe nada de parejas. Esos le piden a
resolve la mitad que esta a la vista y se repintan cuando salta on_change.

Las tipografias no pueden existir antes que la ventana, asi que load_fonts se
ejecuta una vez que la aplicacion ha arrancado y font las reparte desde
entonces.
"""

from collections.abc import Callable
from tkinter import font as tk_font

import customtkinter as ctk

Color = str | tuple[str, str]

# ----- Colores, cada uno (claro, oscuro) -----

BACKGROUND: Color = ("#f5f5f7", "#121212")
CARD: Color = ("#ffffff", "#1c1c1e")
FIELD: Color = ("#f2f2f5", "#2c2c2e")
FIELD_HOVER: Color = ("#e6e6ea", "#3a3a3c")
BORDER: Color = ("#e2e2e6", "#2f2f31")
RULE: Color = ("#c7c7cc", "#48484a")
INK: Color = ("#1d1d1f", "#f5f5f7")
MUTED: Color = ("#6e6e73", "#aeaeb2")
FAINT: Color = ("#b0b0b6", "#5a5a5e")

ACCENT = "#0071e3"
ACCENT_HOVER = "#0077ed"
ACCENT_SOFT: Color = ("#e8f1fc", "#12283c")
ON_ACCENT = "#ffffff"

GREEN = "#34c759"
ORANGE = "#ff9500"
RED = "#ff3b30"
RED_SOFT: Color = ("#fff1ef", "#2b1614")

# ----- Formas -----

CARD_RADIUS = 26
PILL_RADIUS = 22
FIELD_RADIUS = 10
NAV_RADIUS = 12

# Gana la primera familia que este instalada de verdad; la ultima es el respaldo.
SANS_FAMILIES = ("Inter", "SF Pro Text", "Adwaita Sans", "Cantarell", "Segoe UI", "DejaVu Sans")
MONO_FAMILIES = ("JetBrains Mono", "Fira Code", "SF Mono", "DejaVu Sans Mono", "Courier")

_fonts: dict[str, ctk.CTkFont] = {}
_listeners: list[Callable[[], None]] = []

def load_fonts() -> None:
    """
    Construye todas las tipografias una sola vez, cosa que solo se puede hacer
    cuando ya existe una ventana.
    """
    installed = set(tk_font.families())
    sans = _first_installed(SANS_FAMILIES, installed)
    mono = _first_installed(MONO_FAMILIES, installed)

    _fonts.update({
        "title": ctk.CTkFont(family=sans, size=21, weight="bold"),
        "heading": ctk.CTkFont(family=sans, size=15, weight="bold"),
        "brand": ctk.CTkFont(family=sans, size=14, weight="bold"),
        "button": ctk.CTkFont(family=sans, size=13, weight="bold"),
        "body": ctk.CTkFont(family=sans, size=13),
        "small": ctk.CTkFont(family=sans, size=12),
        "label": ctk.CTkFont(family=sans, size=11, weight="bold"),
        "badge": ctk.CTkFont(family=sans, size=15, weight="bold"),
        "mono": ctk.CTkFont(family=mono, size=13),
        "mono_small": ctk.CTkFont(family=mono, size=12),
        "mono_tiny": ctk.CTkFont(family=mono, size=11),
    })

def font(name: str) -> ctk.CTkFont:
    """Una de las tipografias que construyo load_fonts."""
    if not _fonts:
        raise RuntimeError("load_fonts() has to run once the window exists.")
    return _fonts[name]

def set_dark(dark: bool) -> None:
    """Cambia el modo de toda la ventana, y avisa a las partes que se dibujan a mano."""
    ctk.set_appearance_mode("dark" if dark else "light")
    for listener in _listeners:
        listener()

def is_dark() -> bool:
    return ctk.get_appearance_mode() == "Dark"

def resolve(color: Color) -> str:
    """La mitad de la pareja (claro, oscuro) que se esta viendo ahora mismo."""
    if isinstance(color, str):
        return color
    return color[1] if is_dark() else color[0]

def on_change(listener: Callable[[], None]) -> None:
    """Vuelve a llamar a esto cada vez que se cambie de tema."""
    _listeners.append(listener)

def off_change(listener: Callable[[], None]) -> None:
    """Deja de avisar a un oyente, cuando el elemento que repintaba ya no existe."""
    if listener in _listeners:
        _listeners.remove(listener)

def _first_installed(candidates: tuple[str, ...], installed: set[str]) -> str:
    """La primera familia que el sistema tenga de verdad, o la ultima como respaldo."""
    for family in candidates:
        if family in installed:
            return family
    return candidates[-1]
