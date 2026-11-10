"""Ventana Qt con el catálogo y una herramienta de muestra por sección."""

from collections.abc import Callable
from dataclasses import dataclass
import sys

from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QMainWindow,
    QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from .bisection import BisectionPage
from .examples import bases_page, determinant_page, gauss_page, vectors_page
from .widgets import action, card, label, stylesheet


@dataclass(frozen=True)
class Demo:
    key: str
    section: str
    title: str
    detail: str
    create: Callable[[], QWidget]


DEMOS = (
    Demo("gauss", "Sistemas lineales", "Eliminación Gaussiana",
         "Resuelve un sistema escrito por ecuaciones y verifica la solución.", gauss_page),
    Demo("determinant", "Matrices", "Determinante 2 × 2",
         "Edita una matriz y consulta el cálculo por cofactores.", determinant_page),
    Demo("vectors", "Vectores", "Suma de vectores",
         "Suma dos vectores y revisa el resultado por componente.", vectors_page),
    Demo("bases", "Sistemas numéricos", "Decimal a binario",
         "Convierte un entero y revisa las divisiones sucesivas.", bases_page),
    Demo("bisection", "Métodos numéricos", "Método de Bisección",
         "Escribe con el editor matemático, grafica y aproxima una raíz.", BisectionPage),
)


class PreviewWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Álgebra Lineal · Vista previa")
        self.resize(1180, 800)
        self.setMinimumSize(900, 620)
        self._dark = False
        self._demos = {demo.key: demo for demo in DEMOS}
        self.pages: dict[str, QWidget] = {}
        self._scroll: dict[str, QScrollArea] = {}
        self._nav: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)

        surface = QWidget()
        surface.setObjectName("workArea")
        layout = QHBoxLayout(surface)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)
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
        sidebar.setFixedWidth(248)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(13, 14, 13, 14)
        layout.setSpacing(9)
        brand = QHBoxLayout()
        brand.addWidget(label("∑   Álgebra Lineal", "heading"), 1)
        self.theme_button = QPushButton("◐")
        self.theme_button.setAccessibleName("Cambiar tema")
        self.theme_button.clicked.connect(self._toggle_theme)
        brand.addWidget(self.theme_button)
        layout.addLayout(brand)
        layout.addWidget(label("MTM0120 · Vista previa", "muted"))
        scroll = QScrollArea()
        scroll.viewport().setObjectName("sidebarViewport")
        scroll.setWidgetResizable(True)
        rows = QWidget()
        rows.setObjectName("sidebarContent")
        links = QVBoxLayout(rows)
        links.setContentsMargins(0, 6, 0, 0)
        links.setSpacing(5)
        links.addWidget(self._navigation("home", "⌂   Inicio"))
        for demo in DEMOS:
            heading = label(demo.section.upper(), "group")
            heading.setContentsMargins(4, 9, 0, 0)
            links.addWidget(heading)
            links.addWidget(self._navigation(demo.key, demo.title))
        links.addStretch()
        scroll.setWidget(rows)
        layout.addWidget(scroll)
        return sidebar

    def _navigation(self, key: str, title: str) -> QPushButton:
        button = QPushButton(title, checkable=True)
        button.setObjectName("navigation")
        button.clicked.connect(lambda: self.select(key))
        self._group.addButton(button)
        self._nav[key] = button
        return button

    def _home(self) -> QWidget:
        home = QWidget()
        layout = QVBoxLayout(home)
        layout.setSpacing(16)
        layout.addWidget(label("Inicio", "title"))
        layout.addWidget(label("Vista previa de la calculadora de escritorio. Prueba una herramienta por sección.", "muted"))
        grid = QGridLayout()
        grid.setSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        for index, demo in enumerate(DEMOS):
            tile, content = card()
            content.addWidget(label(demo.section.upper(), "group"))
            content.addWidget(label(demo.title, "heading"))
            content.addWidget(label(demo.detail, "muted"))
            content.addStretch()
            open_page = action("Abrir  →")
            open_page.clicked.connect(lambda checked=False, key=demo.key: self.select(key))
            content.addWidget(open_page)
            grid.addWidget(tile, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch()
        return home

    def _add_page(self, key: str, page: QWidget) -> None:
        scroll = QScrollArea()
        scroll.viewport().setObjectName("pageViewport")
        page.setObjectName("pageContent")
        page.layout().setContentsMargins(10, 8, 10, 16)
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
