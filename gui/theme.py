"""
The look of the window: colours, type and the light/dark switch.

Every colour is a `(light, dark)` pair, which is what CustomTkinter reads
directly. Writing them that way is what makes the theme toggle a single call:
no widget is rebuilt and no colour is recomputed, the toolkit simply reads the
other half of every pair it was already given.

The two exceptions are the shapes drawn by hand — the brackets around a matrix
sit on a canvas, which knows nothing about pairs. They ask `resolve` for the
half that is showing and repaint themselves when `on_change` fires.

Fonts cannot exist before a window does, so `load_fonts` runs once the
application has started and `font` hands them out from then on.
"""

from collections.abc import Callable
from tkinter import font as tk_font

import customtkinter as ctk

Color = str | tuple[str, str]

# ----- Colours, each one (light, dark) -----

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

# ----- Shapes -----

CARD_RADIUS = 26
PILL_RADIUS = 22
FIELD_RADIUS = 10
NAV_RADIUS = 12

# The first family that is actually installed wins; the last is the fallback.
SANS_FAMILIES = ("Inter", "SF Pro Text", "Adwaita Sans", "Cantarell", "Segoe UI", "DejaVu Sans")
MONO_FAMILIES = ("JetBrains Mono", "Fira Code", "SF Mono", "DejaVu Sans Mono", "Courier")

_fonts: dict[str, ctk.CTkFont] = {}
_listeners: list[Callable[[], None]] = []

def load_fonts() -> None:
    """Build every font once, which can only happen after a window exists."""
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
    })

def font(name: str) -> ctk.CTkFont:
    """One of the fonts `load_fonts` built."""
    if not _fonts:
        raise RuntimeError("load_fonts() has to run once the window exists.")
    return _fonts[name]

def set_dark(dark: bool) -> None:
    """Switch the whole window over, and let the hand-drawn parts know."""
    ctk.set_appearance_mode("dark" if dark else "light")
    for listener in _listeners:
        listener()

def is_dark() -> bool:
    return ctk.get_appearance_mode() == "Dark"

def resolve(color: Color) -> str:
    """The half of a (light, dark) pair that is showing right now."""
    if isinstance(color, str):
        return color
    return color[1] if is_dark() else color[0]

def on_change(listener: Callable[[], None]) -> None:
    """Call this back whenever the theme is switched."""
    _listeners.append(listener)

def off_change(listener: Callable[[], None]) -> None:
    """Stop calling a listener back, once the widget it repainted is gone."""
    if listener in _listeners:
        _listeners.remove(listener)

def _first_installed(candidates: tuple[str, ...], installed: set[str]) -> str:
    """The first family the system actually has, or the last one as a fallback."""
    for family in candidates:
        if family in installed:
            return family
    return candidates[-1]
