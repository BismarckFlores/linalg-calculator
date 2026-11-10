"""Ventana Qt con el catálogo y una herramienta de muestra por sección."""

from collections.abc import Callable
from dataclasses import dataclass
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QHBoxLayout, QMainWindow,
    QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from .bisection import BisectionPage
from .examples import bases_page, determinant_page, gauss_page, vectors_page
from .widgets import badge, card, label, link, page_header, stylesheet


@dataclass(frozen=True)
class Demo:
    key: str
    section: str
    glyph: str
    title: str
    detail: str
    create: Callable[[], QWidget]


DEMOS = (
    Demo("gauss", "Sistemas Lineales", "▦", "Eliminación Gaussiana",
         "Resuelve un sistema escrito por ecuaciones y verifica la solución.", gauss_page),
    Demo("determinant", "Matrices", "|A|", "Determinante",
         "Edita una matriz y consulta el cálculo por cofactores.", determinant_page),
    Demo("vectors", "Vectores", "↗", "Operaciones Vectoriales",
         "Suma dos vectores y revisa el resultado por componente.", vectors_page),
    Demo("bases", "Sistemas Numéricos", "⇄", "Conversiones",
         "Convierte un entero y revisa las divisiones sucesivas.", bases_page),
    Demo("bisection", "Métodos Numéricos", "½", "Método de Bisección",
         "Escribe con el editor matemático, grafica y aproxima una raíz.", BisectionPage),
)


class PreviewWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Álgebra Lineal · Vista previa")
        self.resize(1180, 800)
        self.setMinimumSize(960, 640)
        self._dark = False
        self._demos = {demo.key: demo for demo in DEMOS}
        self.pages: dict[str, QWidget] = {}
        self._scroll: dict[str, QScrollArea] = {}
        self._nav: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)

        surface = QWidget()
        surface.setObjectName("workArea")
        layout = QHBoxLayout(surface)
        layout.setContentsMargins(20, 20, 16, 20)
        layout.setSpacing(26)
        layout.addWidget(self._sidebar())
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(surface)
        self._add_page("home", self._home())
        self.select("home")
        self._apply_theme()

    def _sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(268)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(13, 22, 13, 14)
        layout.setSpacing(10)
        brand = QHBoxLayout()
        brand.setSpacing(10)
        brand.addWidget(badge("∑", 30, "brandGlyph"))
        identity = QVBoxLayout()
        identity.setSpacing(7)
        identity.addWidget(label("Álgebra Lineal", "brand"))
        identity.addWidget(label("MTM0120 · UAM", "course"))
        brand.addLayout(identity, 1)
        self.theme_button = QPushButton("◐")
        self.theme_button.setObjectName("themeSwitch")
        self.theme_button.setFixedSize(42, 30)
        self.theme_button.setAccessibleName("Cambiar tema")
        self.theme_button.clicked.connect(self._toggle_theme)
        brand.addWidget(self.theme_button)
        layout.addLayout(brand)
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedHeight(2)
        layout.addSpacing(8)
        layout.addWidget(separator)
        scroll = QScrollArea()
        scroll.viewport().setObjectName("sidebarViewport")
        scroll.setWidgetResizable(True)
        rows = QWidget()
        rows.setObjectName("sidebarContent")
        links = QVBoxLayout(rows)
        links.setContentsMargins(0, 0, 0, 0)
        links.setSpacing(4)
        links.addWidget(self._navigation("home", "⌂", "Inicio"))
        for demo in DEMOS:
            heading = label(demo.section.upper(), "group")
            heading.setContentsMargins(8, 16, 0, 8)
            links.addWidget(heading)
            links.addWidget(self._navigation(demo.key, demo.glyph, demo.title))
        links.addStretch()
        scroll.setWidget(rows)
        layout.addWidget(scroll)
        return sidebar

    def _navigation(self, key: str, glyph: str, title: str) -> QPushButton:
        button = QPushButton(checkable=True)
        button.setObjectName("navigation")
        button.setAccessibleName(title)
        button.setFixedHeight(40)
        row = QHBoxLayout(button)
        row.setContentsMargins(8, 4, 12, 4)
        row.setSpacing(10)
        icon = badge(glyph)
        name = label(title, "navName")
        for widget in (icon, name):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(icon)
        row.addWidget(name, 1)

        def mark_active(active: bool) -> None:
            icon.setObjectName("activeGlyph" if active else "glyph")
            name.setObjectName("activeNavName" if active else "navName")
            for widget in (icon, name):
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()

        button.toggled.connect(mark_active)
        button.clicked.connect(lambda: self.select(key))
        self._group.addButton(button)
        self._nav[key] = button
        return button

    def _home(self) -> QWidget:
        home = QWidget()
        layout = QVBoxLayout(home)
        layout.setSpacing(10)
        layout.addWidget(page_header("⌂", "Inicio", "Elige una herramienta para comenzar."))
        for demo in DEMOS:
            layout.addSpacing(10)
            section = QHBoxLayout()
            section.addWidget(label(demo.section, "heading"), 1)
            section.addWidget(label("1 herramienta", "count"))
            layout.addLayout(section)
            tile, content = card()
            heading = QHBoxLayout()
            heading.setSpacing(10)
            heading.addWidget(badge(demo.glyph))
            heading.addWidget(label(demo.title, "heading"), 1)
            content.addLayout(heading)
            content.addWidget(label(demo.detail, "muted"))
            open_page = link("Abrir  →")
            open_page.clicked.connect(lambda checked=False, key=demo.key: self.select(key))
            content.addWidget(open_page, alignment=Qt.AlignmentFlag.AlignRight)
            layout.addWidget(tile)
        layout.addStretch()
        return home

    def _add_page(self, key: str, page: QWidget) -> None:
        scroll = QScrollArea()
        scroll.viewport().setObjectName("pageViewport")
        page.setObjectName("pageContent")
        page.layout().setContentsMargins(20, 10, 24, 16)
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        self.stack.addWidget(scroll)
        self.pages[key] = page
        self._scroll[key] = scroll

    def select(self, key: str) -> None:
        if key not in self.pages:
            page = self._demos[key].create()
            if isinstance(page, BisectionPage):
                page.set_dark(self._dark)
            self._add_page(key, page)
        self._nav[key].setChecked(True)
        self.stack.setCurrentWidget(self._scroll[key])

    def _toggle_theme(self) -> None:
        self._dark = not self._dark
        self.theme_button.setText("◑" if self._dark else "◐")
        self._apply_theme()

    def _apply_theme(self) -> None:
        self.setStyleSheet(stylesheet(self._dark))
        page = self.pages.get("bisection")
        if isinstance(page, BisectionPage):
            page.set_dark(self._dark)


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Álgebra Lineal · Vista previa")
    app.setStyle("Fusion")
    window = PreviewWindow()
    window.show()
    sys.exit(app.exec())
