"""Preferencia de apariencia y seguimiento del esquema del sistema."""

from PySide6.QtCore import QSettings, QSize, Qt, Signal
from PySide6.QtGui import QActionGroup, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QPushButton, QWidgetAction

from ..assets import ASSETS
from ..widgets import label


THEMES = {"auto": "Automático", "light": "Claro", "dark": "Oscuro"}


class ThemeSelector(QPushButton):
    theme_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("themeSwitch")
        self.setFixedSize(54, 36)
        self.setIconSize(QSize(18, 18))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings = QSettings("linalg-calculator", "linalg-calculator")
        saved = self._settings.value("theme", "auto", type=str)
        self.mode = saved if saved in THEMES else "auto"
        self._style_hints = QApplication.styleHints()

        menu = QMenu(self)
        menu.setObjectName("themeMenu")
        menu.setMinimumWidth(178)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        heading = QWidgetAction(menu)
        heading.setDefaultWidget(label("Apariencia", "themeMenuTitle"))
        heading.setEnabled(False)
        menu.addAction(heading)
        choices = QActionGroup(menu)
        self.actions_by_mode = {}
        for mode, title in THEMES.items():
            icon = QIcon(str(ASSETS / f"theme-{mode}.svg"))
            action = menu.addAction(icon, title)
            action.setCheckable(True)
            choices.addAction(action)
            action.triggered.connect(lambda checked=False, value=mode: self.set_mode(value))
            self.actions_by_mode[mode] = action
        self.setMenu(menu)
        self._sync_button()
        self._style_hints.colorSchemeChanged.connect(self._system_theme_changed)

    @property
    def dark(self) -> bool:
        return self.mode == "dark" or (
            self.mode == "auto" and self._style_hints.colorScheme() == Qt.ColorScheme.Dark
        )

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self._settings.setValue("theme", mode)
        self._sync_button()
        self.theme_changed.emit(self.dark)

    def _sync_button(self) -> None:
        active = self.actions_by_mode[self.mode]
        active.setChecked(True)
        for key, action in self.actions_by_mode.items():
            title = THEMES[key]
            action.setText(f"{title}\t✓" if action is active else title)
        self.setIcon(active.icon())
        title = THEMES[self.mode]
        self.setAccessibleName(f"Tema: {title}")
        self.setToolTip(f"Tema: {title}")

    def _system_theme_changed(self) -> None:
        if self.mode == "auto":
            self.theme_changed.emit(self.dark)
