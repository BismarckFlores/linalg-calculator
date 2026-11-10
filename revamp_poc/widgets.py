"""Estilos y piezas Qt compartidas por las pantallas de prueba."""

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


def card() -> tuple[QFrame, QVBoxLayout]:
    panel = QFrame()
    panel.setObjectName("card")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    return panel, layout


def label(text: str, style: str = "") -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(style)
    widget.setWordWrap(True)
    return widget


def action(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("action")
    return button


def stylesheet(dark: bool) -> str:
    colors = {
        "surface": "#131923", "card": "#1c2432", "line": "#354155",
        "text": "#eef2fb", "muted": "#a9b5c7", "field": "#263144",
        "hover": "#2e3d54", "blue": "#1979dc", "danger": "#ffaca6",
    } if dark else {
        "surface": "#f4f6fa", "card": "#ffffff", "line": "#dce3ed",
        "text": "#172033", "muted": "#52627a", "field": "#f0f3f9",
        "hover": "#e2ebfa", "blue": "#0071e3", "danger": "#a62024",
    }
    return """
    QWidget { color: %(text)s; font-size: 14px; }
    QMainWindow, QWidget#workArea, QWidget#pageViewport, QWidget#pageContent {
        background: %(surface)s;
    }
    QWidget#sidebarViewport, QWidget#sidebarContent { background: %(card)s; }
    QScrollArea { background: transparent; border: none; }
    QScrollBar:vertical {
        width: 10px; background: %(field)s; border-radius: 5px; margin: 0;
    }
    QScrollBar::handle:vertical {
        min-height: 30px; background: %(line)s; border-radius: 5px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
    QFrame#card, QFrame#sidebar {
        background: %(card)s; border: 1px solid %(line)s; border-radius: 16px;
    }
    QLabel#title { font-size: 27px; font-weight: 700; }
    QLabel#heading { font-size: 17px; font-weight: 700; }
    QLabel#muted, QLabel#group { color: %(muted)s; }
    QLabel#group { font-size: 11px; font-weight: 700; }
    QLabel#inputError { color: %(danger)s; }
    QLineEdit, QPlainTextEdit, QTableWidget, QSpinBox {
        background: %(field)s; border: 1px solid %(line)s;
        border-radius: 8px; padding: 7px; selection-background-color: %(blue)s;
    }
    QHeaderView::section {
        background: %(field)s; color: %(text)s; border: 1px solid %(line)s; padding: 5px;
    }
    QPushButton {
        background: %(field)s; border: 1px solid %(line)s; border-radius: 9px;
        padding: 8px 12px; font-weight: 600;
    }
    QPushButton:hover { background: %(hover)s; }
    QPushButton:checked, QPushButton#action {
        background: %(blue)s; color: white; border-color: %(blue)s;
    }
    QPushButton:disabled { color: %(muted)s; background: %(field)s; border-color: %(line)s; }
    QPushButton#navigation { text-align: left; }
    """ % colors
