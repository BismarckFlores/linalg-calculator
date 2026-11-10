"""Estilos y piezas Qt compartidas por las pantallas de prueba."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ui import theme_tokens as theme


def card() -> tuple[QFrame, QVBoxLayout]:
    panel = QFrame()
    panel.setObjectName("card")
    panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(24, 22, 24, 22)
    layout.setSpacing(10)
    return panel, layout


def label(text: str, style: str = "") -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(style)
    widget.setWordWrap(True)
    return widget


def action(text: str) -> QPushButton:
    button = QPushButton(f"{text}  →")
    button.setObjectName("action")
    return button


def link(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("link")
    return button


def badge(glyph: str, size: int = 32, style: str = "glyph") -> QLabel:
    icon = label(glyph, style)
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon.setFixedSize(size, size)
    return icon


def page_header(glyph: str, title: str, subtitle: str) -> QWidget:
    header = QWidget()
    layout = QVBoxLayout(header)
    layout.setContentsMargins(0, 0, 0, 10)
    layout.setSpacing(10)
    row = QHBoxLayout()
    row.setSpacing(12)
    row.addWidget(badge(glyph, 36))
    row.addWidget(label(title, "title"), 1)
    layout.addLayout(row)
    layout.addWidget(label(subtitle, "muted"))
    return header


def pill_group() -> tuple[QFrame, QHBoxLayout]:
    panel = QFrame()
    panel.setObjectName("pills")
    row = QHBoxLayout(panel)
    row.setContentsMargins(3, 3, 3, 3)
    row.setSpacing(2)
    return panel, row


def stylesheet(dark: bool) -> str:
    mode = int(dark)
    installed = set(QFontDatabase.families())
    colors = {
        "surface": theme.BACKGROUND[mode], "card": theme.CARD[mode], "line": theme.BORDER[mode],
        "text": theme.INK[mode], "muted": theme.MUTED[mode], "faint": theme.FAINT[mode],
        "field": theme.FIELD[mode], "hover": theme.FIELD_HOVER[mode],
        "blue": theme.ACCENT, "blueHover": theme.ACCENT_HOVER, "danger": theme.RED,
        "soft": theme.ACCENT_SOFT[mode], "onSoft": theme.ON_ACCENT_SOFT[mode],
        "onAccent": theme.ON_ACCENT, "rule": theme.RULE[mode],
        "cardRadius": theme.CARD_RADIUS, "pillRadius": min(theme.PILL_RADIUS, 16),
        "fieldRadius": theme.FIELD_RADIUS, "navRadius": theme.NAV_RADIUS,
        "sans": next((name for name in theme.SANS_FAMILIES if name in installed), "sans-serif"),
        "mono": next((name for name in theme.MONO_FAMILIES if name in installed), "monospace"),
    }
    return """
    QWidget { color: %(text)s; font-family: "%(sans)s"; font-size: 13px; }
    QMainWindow, QWidget#workArea, QWidget#pageViewport, QWidget#pageContent {
        background: %(surface)s;
    }
    QWidget#sidebarViewport, QWidget#sidebarContent { background: %(card)s; }
    QScrollArea { background: transparent; border: none; }
    QScrollBar:vertical {
        width: 10px; background: %(field)s; border-radius: 5px; margin: 0;
    }
    QScrollBar::handle:vertical {
        min-height: 30px; background: %(rule)s; border-radius: 5px;
    }
    QScrollBar:vertical:disabled, QScrollBar::handle:vertical:disabled { background: transparent; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
    QFrame#card, QFrame#sidebar {
        background: %(card)s; border: 1px solid %(line)s; border-radius: %(cardRadius)dpx;
    }
    QFrame#separator { background: %(line)s; }
    QLabel#title { font-size: 21px; font-weight: 600; }
    QLabel#answer { color: %(blue)s; font-size: 15px; font-weight: 700; }
    QLabel#heading { font-size: 15px; font-weight: 600; }
    QLabel#brand { font-size: 14px; font-weight: 600; }
    QLabel#muted, QLabel#caption { color: %(muted)s; }
    QLabel#caption { font-size: 12px; }
    QLabel#group, QLabel#course { color: %(faint)s; }
    QLabel#group, QLabel#count { font-size: 11px; font-weight: 700; }
    QLabel#count { color: %(muted)s; background: %(field)s; border-radius: 10px; padding: 6px 16px; }
    QLabel#glyph, QLabel#activeGlyph, QLabel#brandGlyph {
        background: %(soft)s; color: %(blue)s; border-radius: 10px;
        font-size: 15px; font-weight: 700;
    }
    QLabel#activeGlyph { background: %(onSoft)s; }
    QLabel#activeNavName { color: %(onAccent)s; }
    QLabel#brandGlyph { background: %(blue)s; color: %(onAccent)s; border-radius: 9px; }
    QLabel#inputError { color: %(danger)s; }
    QLineEdit, QPlainTextEdit, QTableWidget, QSpinBox {
        background: %(field)s; border: 1px solid %(line)s;
        border-radius: %(fieldRadius)dpx; padding: 9px;
        font-family: "%(mono)s"; selection-background-color: %(blue)s;
    }
    QLineEdit:focus, QPlainTextEdit:focus { border-color: %(blue)s; }
    QTableWidget { background: %(card)s; alternate-background-color: %(field)s; gridline-color: %(line)s; }
    QHeaderView::section {
        background: %(field)s; color: %(text)s; border: 1px solid %(line)s; padding: 5px;
    }
    QPushButton {
        background: %(field)s; border: none; border-radius: %(pillRadius)dpx;
        min-height: 16px; padding: 8px 16px; font-weight: 600;
    }
    QPushButton:hover { background: %(hover)s; }
    QPushButton:focus { border: 1px solid %(blue)s; }
    QPushButton#action {
        background: %(blue)s; color: %(onAccent)s; padding: 10px 20px;
    }
    QPushButton#action:hover { background: %(blueHover)s; }
    QPushButton#keyboardToggle:checked,
    QFrame#mathKeyboard QPushButton[mathRole="template"] {
        background: %(blue)s; color: %(onAccent)s;
    }
    QPushButton#keyboardToggle:checked:hover,
    QFrame#mathKeyboard QPushButton[mathRole="template"]:hover { background: %(blueHover)s; }
    QFrame#mathKeyboard {
        background: %(card)s; border: 1px solid %(line)s; border-radius: %(fieldRadius)dpx;
    }
    QFrame#mathKeyboard QPushButton { padding: 8px 4px; }
    QFrame#mathKeyboard QPushButton[mathRole="symbol"] { background: %(soft)s; }
    QFrame#mathKeyboard QPushButton[mathRole="symbol"]:hover { background: %(hover)s; }
    QFrame#mathKeyboard QPushButton:pressed { border: 1px solid %(blue)s; }
    QPushButton:disabled { color: %(muted)s; }
    QPushButton#link { background: transparent; color: %(blue)s; }
    QPushButton#link:hover { background: %(field)s; }
    QPushButton#themeSwitch { border-radius: 15px; padding: 0; font-weight: 400; }
    QPushButton#navigation {
        background: transparent; border-radius: %(navRadius)dpx; padding: 0;
    }
    QPushButton#navigation:hover { background: %(field)s; }
    QPushButton#navigation:checked { background: %(blue)s; }
    QFrame#pills { background: %(field)s; border-radius: 17px; }
    QFrame#pills QPushButton {
        background: transparent; border-radius: 14px; padding: 6px 14px; font-weight: 400;
    }
    QFrame#pills QPushButton:hover { background: %(hover)s; }
    QFrame#pills QPushButton:checked { background: %(card)s; }
    """ % colors
