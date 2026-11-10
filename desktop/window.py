"""Ventana Qt y catálogo de herramientas."""

from collections.abc import Callable
from itertools import groupby
import os
import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtQuick import QQuickWindow
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QMainWindow,
    QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from .core.assets import ASSETS
from .core.handlers.theme import ThemeSelector
from .core.math_input import MathInput
from .core.widgets import GlassFrame, Workspace, badge, card, label, link, page_header, stylesheet
from .tools.numerical_methods.core.bracket_page import RootBracketPage
from .tools.registry import TOOLS

APP_ICON = ASSETS / "icon.svg"


class Catalog(QWidget):
    def __init__(self, select: Callable[[str], None]) -> None:
        super().__init__()
        self._grids = []
        self._columns = 0
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(page_header("⌂", "Inicio", "Elige una herramienta para comenzar."))
        for name, group in groupby(TOOLS, key=lambda tool: tool.section):
            tools = tuple(group)
            layout.addSpacing(10)
            section = QHBoxLayout()
            section.addWidget(label(name, "heading"), 1)
            count = len(tools)
            section.addWidget(label("1 herramienta" if count == 1 else f"{count} herramientas", "count"))
            layout.addLayout(section)
            grid = QGridLayout()
            grid.setSpacing(10)
            tiles = []
            for tool in tools:
                tile, content = card()
                heading = QHBoxLayout()
                heading.setSpacing(10)
                heading.addWidget(badge(tool.glyph))
                heading.addWidget(label(tool.title, "heading"), 1)
                content.addLayout(heading)
                content.addWidget(label(tool.detail, "muted"))
                open_page = link("Abrir  →")
                open_page.setAccessibleName(f"Abrir {tool.title}")
                open_page.clicked.connect(lambda checked=False, key=tool.key: select(key))
                content.addWidget(open_page, alignment=Qt.AlignmentFlag.AlignRight)
                tiles.append(tile)
                grid.addWidget(tile, len(tiles) - 1, 0)
            self._grids.append((grid, tiles))
            layout.addLayout(grid)
        layout.addStretch()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        columns = 2 if self.width() - self.layout().contentsMargins().left() - self.layout().contentsMargins().right() >= 720 else 1
        if columns == self._columns:
            return
        self._columns = columns
        for grid, tiles in self._grids:
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, int(columns == 2 and len(tiles) > 1))
            for index, tile in enumerate(tiles):
                grid.removeWidget(tile)
                row, column = divmod(index, columns)
                grid.addWidget(tile, row, column, 1, columns if len(tiles) == 1 else 1)


class CalculatorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowIcon(QIcon(str(APP_ICON)))
        self.setWindowTitle("Calculadora de Álgebra Lineal")
        self.resize(1180, 800)
        self.setMinimumSize(960, 640)
        self._tools = {tool.key: tool for tool in TOOLS}
        self.pages: dict[str, QWidget] = {}
        self._scroll: dict[str, QScrollArea] = {}
        self._nav: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)

        surface = Workspace()
        self.workspace = surface
        layout = QHBoxLayout(surface)
        layout.setContentsMargins(20, 20, 16, 20)
        layout.setSpacing(26)
        layout.addWidget(self._sidebar())
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(surface)
        self._add_page("home", Catalog(self.select))
        self.select("home")
        self._apply_theme(self.theme_button.dark)
        self.theme_button.theme_changed.connect(self._apply_theme)

    def _sidebar(self) -> QFrame:
        sidebar = GlassFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(268)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(9, 22, 13, 14)
        layout.setSpacing(10)
        brand = QHBoxLayout()
        brand.setSpacing(10)
        icon = label("")
        icon.setFixedSize(30, 30)
        icon.setPixmap(self.windowIcon().pixmap(QSize(30, 30), self.devicePixelRatioF()))
        brand.addWidget(icon)
        identity = QVBoxLayout()
        identity.setSpacing(7)
        identity.addWidget(label("Álgebra Lineal", "brand"))
        identity.addWidget(label("MTM0120 · UAM", "course"))
        brand.addLayout(identity, 1)
        self.theme_button = ThemeSelector()
        brand.addWidget(self.theme_button)
        layout.addLayout(brand)
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedHeight(2)
        layout.addSpacing(12)
        layout.addWidget(separator)
        scroll = QScrollArea()
        scroll.viewport().setObjectName("sidebarViewport")
        scroll.setWidgetResizable(True)
        rows = QWidget()
        rows.setObjectName("sidebarContent")
        links = QVBoxLayout(rows)
        links.setContentsMargins(0, 0, 0, 0)
        links.setSpacing(2)
        links.addWidget(self._navigation("home", "⌂", "Inicio"))
        previous_section = None
        for tool in TOOLS:
            if tool.section != previous_section:
                heading = label(tool.section.upper(), "group")
                heading.setContentsMargins(12, 20, 0, 10)
                links.addWidget(heading)
                previous_section = tool.section
            links.addWidget(self._navigation(tool.key, tool.glyph, tool.title))
        links.addStretch()
        scroll.setWidget(rows)
        self._nav_scroll = scroll
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

    def _add_page(self, key: str, page: QWidget) -> None:
        scroll = QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scrollbar = scroll.verticalScrollBar()
        scrollbar.setEnabled(False)
        scrollbar.rangeChanged.connect(lambda low, high: scrollbar.setEnabled(high > low))
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
            page = self._tools[key].create()
            self._apply_page_theme(page)
            self._add_page(key, page)
        self._nav[key].setChecked(True)
        self._nav_scroll.ensureWidgetVisible(self._nav[key], 0, 8)
        self.stack.setCurrentWidget(self._scroll[key])

    def _apply_theme(self, dark: bool) -> None:
        self._dark = dark
        self.workspace.dark = dark
        self.setStyleSheet(stylesheet(dark))
        for page in self.pages.values():
            self._apply_page_theme(page)

    def _apply_page_theme(self, page: QWidget) -> None:
        for field in page.findChildren(MathInput):
            field.set_dark(self._dark)
        if isinstance(page, RootBracketPage):
            page.set_dark(self._dark)


def run() -> None:
    # Todas las vistas matemáticas cargan el mismo editor local.
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--process-per-site")
    app = QApplication(sys.argv)
    app.setApplicationName("Calculadora de Álgebra Lineal")
    app.setDesktopFileName("linalg-calculator")
    app.setWindowIcon(QIcon(str(APP_ICON)))
    app.setStyle("Fusion")
    if sys.platform == "linux":
        # WebEngine cambia la superficie de la ventana si se activa OpenGL al abrir Bisección.
        QQuickWindow.setSceneGraphBackend("software")
    window = CalculatorWindow()
    window.show()
    sys.exit(app.exec())
