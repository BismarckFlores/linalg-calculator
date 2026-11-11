"""Estilos y componentes Qt compartidos."""

from functools import cache

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor, QFontDatabase, QIcon, QIntValidator, QLinearGradient, QPainter, QPainterPath, QPalette, QPen, QPixmap,
    QRadialGradient,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QCheckBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ui import theme_tokens as theme

from .number_display import scientific_notation

from .assets import ASSETS

WORKSPACE_TEXTURE = ASSETS / "workspace-texture.svg"
PAGE_ILLUSTRATIONS = {
    "⌂": "home", "▦": "gauss", "▧": "echelon", "⊞": "operations", "⁻¹": "inverse",
    "LU": "lu", "|A|": "determinant", "↗": "vectors", "⇄": "bases", "Ⅻ": "roman",
    "½": "bisection", "RF": "regula-falsi", "∫": "calculus", "NR": "newton-raphson",
}


@cache
def _workspace_texture(dark: bool, blurred: bool) -> QPixmap:
    tile = QPixmap(str(WORKSPACE_TEXTURE))
    if tile.isNull():
        return tile
    if not dark:
        with QPainter(tile) as painter:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(tile.rect(), QColor("#395984"))
    if not blurred:
        return tile
    smooth = Qt.TransformationMode.SmoothTransformation
    aspect = Qt.AspectRatioMode.IgnoreAspectRatio
    # Filtra la textura una sola vez, sin capturar ni desenfocar controles.
    factor = 3 if dark else 2
    reduced = tile.scaled(tile.width() // factor, tile.height() // factor, aspect, smooth)
    return reduced.scaled(tile.size(), aspect, smooth)


def _paint_workspace(painter: QPainter, rect: QRect, dark: bool, *, blurred: bool = False) -> None:
    radius = max(rect.width() * 0.85, rect.height())
    light = QRadialGradient(rect.width() * 0.13, 0, radius)
    light.setColorAt(0, QColor("#234eae" if dark else "#f9fbff"))
    light.setColorAt(0.42, QColor("#1b2f6b" if dark else "#ccdeff"))
    light.setColorAt(1, QColor(theme.BACKGROUND[1] if dark else "#a5bdf4"))
    painter.fillRect(rect, light)
    painter.drawTiledPixmap(rect, _workspace_texture(dark, blurred))


class Workspace(QWidget):
    dark = False

    def paintEvent(self, event) -> None:
        _paint_workspace(QPainter(self), self.rect(), self.dark)


class GlassFrame(QFrame):
    def paintEvent(self, event) -> None:
        window = self.window()
        workspace = window.findChild(Workspace)
        if workspace is None:
            super().paintEvent(event)
            return

        origin = self.mapTo(window, QPoint()) - workspace.mapTo(window, QPoint())
        mode = int(workspace.dark)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        outline = QPainterPath()
        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        outline.addRoundedRect(bounds, theme.CARD_RADIUS, theme.CARD_RADIUS)
        painter.setClipPath(outline)
        painter.translate(-origin)
        _paint_workspace(painter, workspace.rect(), workspace.dark, blurred=True)
        painter.translate(origin)
        tint = QColor(theme.CARD[mode])
        tint.setAlphaF(0.75)
        painter.fillRect(self.rect(), tint)
        painter.setClipping(False)
        painter.setPen(QPen(QColor(theme.BORDER[mode]), 1))
        painter.drawPath(outline)


def card() -> tuple[QFrame, QVBoxLayout]:
    panel = GlassFrame()
    panel.setObjectName("card")
    panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(24, 22, 24, 22)
    layout.setSpacing(10)
    return panel, layout


class ResultTable(QTableWidget):
    def __init__(self) -> None:
        super().__init__()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setMinimumHeight(230)

    def fill(self, headers, rows, *, decimals: int | None = None) -> None:
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                display = "—" if value is None else str(value)
                if isinstance(value, float):
                    display = f"{value:.10g}" if decimals is None else f"{value:.{decimals}f}"
                item = QTableWidgetItem(scientific_notation(display) if isinstance(value, float) else display)
                if value is not None:
                    item.setToolTip(scientific_notation(str(value)) if isinstance(value, float) else str(value))
                self.setItem(i, j, item)


def label(text: str, style: str = "") -> QLabel:
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
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


@cache
def _navigation_pixmap(key: str, scale: float, color: str) -> QPixmap:
    icon = QIcon(str(ASSETS / "navigation" / f"{key}.svg"))
    pixmap = icon.pixmap(QSize(24, 24), scale)
    if not pixmap.isNull():
        with QPainter(pixmap) as painter:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(QRectF(QPointF(), pixmap.deviceIndependentSize()), QColor(color))
    return pixmap


class NavigationIcon(QLabel):
    def __init__(self, key: str) -> None:
        super().__init__()
        self.setObjectName("navigationIcon")
        self.setFixedSize(34, 34)
        self._key = key

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        color = self.palette().color(QPalette.ColorRole.WindowText)
        pixmap = _navigation_pixmap(self._key, self.devicePixelRatioF(), color.name())
        with QPainter(self) as painter:
            painter.drawPixmap(QPoint(5, 5), pixmap)


class PageBanner(QWidget):
    def __init__(self, glyph: str, shortcut: QPushButton | None = None) -> None:
        super().__init__()
        self._shortcut = shortcut
        self.setObjectName("shortcutBanner" if shortcut is not None else "pageBanner")
        height = 140 if glyph == "⌂" else 112
        self.setMinimumHeight(134 if shortcut is not None else height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        illustration = PAGE_ILLUSTRATIONS.get(glyph, "home")
        self._svg = QSvgRenderer(str(ASSETS / "banners" / f"{illustration}.svg"), self)
        self.art_area = QWidget(self)
        self.art_area.setMaximumWidth(180 if shortcut is not None else 300)
        if shortcut is not None:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event) -> None:
        if (
            self._shortcut is not None and event.button() == Qt.MouseButton.LeftButton
            and self.rect().contains(event.position().toPoint())
        ):
            self._shortcut.click()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:
        workspace = self.window().findChild(Workspace)
        dark = workspace is not None and workspace.dark
        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        outline = QPainterPath()
        outline.addRoundedRect(bounds, 22, 22)
        art = QRectF(self.art_area.geometry())
        transition = art.left() / self.width()
        gradient = QLinearGradient(bounds.topLeft(), bounds.topRight())
        gradient.setColorAt(0, QColor("#15233d" if dark else "#f9fcff"))
        gradient.setColorAt(transition, QColor("#202f5c" if dark else "#e9f1ff"))
        if self._shortcut is not None and not dark:
            gradient.setColorAt(transition + (1 - transition) * 0.4, QColor("#7898da"))
        gradient.setColorAt(1, QColor("#294c9f" if dark else "#3663c7"))

        with QPainter(self) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillPath(outline, gradient)
            painter.setClipPath(outline)
            painter.setPen(QColor(220, 234, 255, 42))
            for radius in (65, 95, 125):
                painter.drawEllipse(bounds.topRight(), radius, radius)
            art.adjust(4, 0, -4, 0)
            size = self._svg.viewBoxF().size()
            size.scale(art.size(), Qt.AspectRatioMode.KeepAspectRatio)
            target = QRectF(art.topLeft(), size)
            target.moveCenter(art.center())
            self._svg.render(painter, target)
            painter.setClipping(False)
            painter.setPen(QColor("#36558b" if dark else "#b2c7ef"))
            painter.drawPath(outline)


def page_header(glyph: str, title: str, subtitle: str, *, shortcut: QPushButton | None = None) -> QWidget:
    header = PageBanner(glyph, shortcut)
    layout = QHBoxLayout(header)
    layout.setContentsMargins(22, 12, 16, 12)
    layout.setSpacing(12)
    copy = QVBoxLayout()
    copy.setSpacing(7)
    copy.addStretch()
    if glyph == "⌂":
        copy.addWidget(label("MTM0120 · UNIVERSIDAD AMERICANA", "bannerKicker"))
    heading = label(title, "title")
    row = QHBoxLayout()
    row.setSpacing(10)
    icon = NavigationIcon(PAGE_ILLUSTRATIONS.get(glyph, "home").replace("-", "_"))
    icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    row.addWidget(icon)
    row.addWidget(heading, 1)
    copy.addLayout(row)
    copy.addWidget(label(subtitle, "muted"))
    if shortcut is not None:
        copy.addWidget(shortcut, alignment=Qt.AlignmentFlag.AlignLeft)
    copy.addStretch()
    layout.addLayout(copy, 3)
    layout.addWidget(header.art_area, 2)
    return header


class SegmentedControl(QFrame):
    currentIndexChanged = Signal(int)
    activated = Signal(int)

    def __init__(self, *values: str, selected: int = 0) -> None:
        super().__init__()
        self.setObjectName("pills")
        row = QHBoxLayout(self)
        row.setContentsMargins(3, 3, 3, 3)
        row.setSpacing(2)
        self._group = QButtonGroup(self)
        for index, value in enumerate(values):
            button = QPushButton(value, checkable=True)
            self._group.addButton(button, index)
            row.addWidget(button)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setCurrentIndex(selected)
        self._group.idToggled.connect(self._changed)
        self._group.idClicked.connect(self.activated)

    def _changed(self, index: int, selected: bool) -> None:
        if selected:
            self.currentIndexChanged.emit(index)

    def currentIndex(self) -> int:
        return self._group.checkedId()

    def currentText(self) -> str:
        button = self._group.checkedButton()
        return button.text() if button is not None else ""

    def setCurrentIndex(self, index: int) -> None:
        if index == -1:
            checked = self._group.checkedButton()
            if checked is not None:
                self._group.setExclusive(False)
                checked.setChecked(False)
                self._group.setExclusive(True)
            return
        button = self._group.button(index)
        if button is not None:
            button.setChecked(True)


class Stepper(QFrame):
    valueChanged = Signal(int)

    def __init__(self, name: str, low: int, high: int, value: int, *, editable: bool = False) -> None:
        super().__init__()
        self.setObjectName("stepper")
        row = QHBoxLayout(self)
        row.setContentsMargins(3, 2, 3, 2)
        row.setSpacing(0)
        self._value = value
        self.setAccessibleName(name)
        self._readout = QLineEdit() if editable else label("", "stepValue")
        self._readout.setAccessibleName(name)
        self._readout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if isinstance(self._readout, QLineEdit):
            self._validator = QIntValidator(self)
            self._readout.setValidator(self._validator)
            self._readout.editingFinished.connect(self._commit)
        self._less, self._more = QPushButton("−"), QPushButton("+")
        for button, verb, step in ((self._less, "Reducir", self.stepDown), (self._more, "Aumentar", self.stepUp)):
            button.setAccessibleName(f"{verb} {name.lower()}")
            button.setAutoRepeat(True)
            button.clicked.connect(step)
        for widget in (self._less, self._readout, self._more):
            row.addWidget(widget)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setRange(low, high)

    def _commit(self) -> None:
        text = self._readout.text()
        self.setValue(int(text) if text.isdecimal() else self.value())

    def _refresh(self) -> None:
        self._readout.setText(str(self._value))
        size = self._high if isinstance(self._readout, QLineEdit) else self._value
        self._readout.setFixedWidth(max(24, 12 + 7 * len(str(size))))
        self._less.setEnabled(self.value() > self._low)
        self._more.setEnabled(self.value() < self._high)

    def setRange(self, low: int, high: int) -> None:
        self._low, self._high = low, high
        if isinstance(self._readout, QLineEdit):
            self._validator.setRange(low, high)
        self.setValue(self._value)

    def value(self) -> int:
        return self._value

    def setValue(self, value: int) -> None:
        previous = self._value
        self._value = max(self._low, min(self._high, value))
        self._refresh()
        if self._value != previous:
            self.valueChanged.emit(self._value)

    def stepDown(self) -> None:
        self.setValue(self.value() - 1)

    def stepUp(self) -> None:
        self.setValue(self.value() + 1)


class Toggle(QCheckBox):
    """Interruptor horizontal con el comportamiento de un control Qt."""

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("toggle")

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = self.height() / 2
        active = self.isChecked() and self.isEnabled()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.ACCENT if active else "#95a1ad"))
        painter.drawRoundedRect(QRectF(0, y - 6, 33, 12), 6, 6)
        painter.setBrush(QColor(theme.ON_ACCENT if active else "#575a5d"))
        painter.drawEllipse(QRectF(16 if active else 0, y - 9, 18, 18))


def interface_fonts() -> tuple[str, str]:
    installed = set(QFontDatabase.families())
    sans = next((name for name in theme.SANS_FAMILIES if name in installed), "sans-serif")
    mono = next((name for name in theme.MONO_FAMILIES if name in installed), "monospace")
    return sans, mono


def stylesheet(dark: bool) -> str:
    mode = int(dark)
    sans, mono = interface_fonts()
    colors = {
        "surface": theme.BACKGROUND[mode], "card": theme.CARD[mode], "line": theme.BORDER[mode],
        "text": theme.INK[mode], "muted": theme.MUTED[mode], "faint": theme.FAINT[mode],
        "bannerMuted": "#c3d4f4" if dark else "#384e77",
        "navIcon": "#9bbdff" if dark else "#235db9",
        "navIconSurface": "#223556" if dark else "#e7f0ff",
        "field": theme.FIELD[mode], "hover": theme.FIELD_HOVER[mode],
        "blue": theme.ACCENT, "blueHover": theme.ACCENT_HOVER, "danger": theme.RED,
        "soft": theme.ACCENT_SOFT[mode],
        "onAccent": theme.ON_ACCENT, "rule": theme.RULE[mode],
        "pillRadius": min(theme.PILL_RADIUS, 16),
        "fieldRadius": theme.FIELD_RADIUS, "navRadius": theme.NAV_RADIUS,
        "assets": ASSETS.as_posix(),
        "sans": sans,
        "mono": mono,
    }
    return """
    QWidget { color: %(text)s; font-family: "%(sans)s"; font-size: 13px; }
    QMainWindow {
        background: %(surface)s;
    }
    QWidget#pageViewport, QWidget#pageContent { background: transparent; }
    QWidget#sidebarViewport, QWidget#sidebarContent { background: transparent; }
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
    QFrame#separator { background: %(line)s; }
    QLabel#title { font-size: 21px; font-weight: 600; }
    QWidget#pageBanner QLabel#title { font-size: 24px; font-weight: 700; }
    QWidget#shortcutBanner QLabel#title { font-size: 17px; font-weight: 700; }
    QWidget#pageBanner QLabel#muted, QWidget#shortcutBanner QLabel#muted { color: %(bannerMuted)s; }
    QWidget#shortcutBanner QPushButton#link { color: %(navIcon)s; padding: 4px 8px; }
    QLabel#bannerKicker { color: %(bannerMuted)s; font-size: 10px; font-weight: 700; }
    QLabel#answer { color: %(blue)s; font-size: 15px; font-weight: 700; }
    QLabel#heading { font-size: 15px; font-weight: 600; }
    QLabel#brand { font-size: 14px; font-weight: 600; }
    QLabel#muted, QLabel#caption { color: %(muted)s; }
    QLabel#caption { font-size: 12px; }
    QLabel#fieldTitle { font-size: 11px; color: %(muted)s; font-weight: 700; }
    QLabel#group, QLabel#course { color: %(faint)s; }
    QLabel#group, QLabel#count { font-size: 11px; font-weight: 700; }
    QLabel#count { color: %(muted)s; background: %(field)s; border-radius: 10px; padding: 6px 16px; }
    QLabel#navigationIcon, QLabel#activeNavigationIcon { border-radius: 10px; }
    QLabel#navigationIcon { background: %(navIconSurface)s; color: %(navIcon)s; }
    QLabel#activeNavigationIcon { background: #eaf2ff; color: #164eab; }
    QLabel#activeNavName { color: %(onAccent)s; }
    QLabel#inputError { color: %(danger)s; }
    QLabel#advice { background: %(field)s; border-radius: 14px; padding: 12px 16px; }
    QLabel#resultFallback { font-family: "%(mono)s"; }
    QLineEdit, QPlainTextEdit, QTableWidget {
        background: %(field)s; border: 1px solid %(line)s;
        border-radius: %(fieldRadius)dpx; padding: 9px;
        font-family: "%(mono)s"; selection-background-color: %(blue)s;
    }
    QLineEdit:focus, QPlainTextEdit:focus { border-color: %(blue)s; }
    QCheckBox::indicator {
        width: 14px; height: 14px; border-radius: 3px;
        background: %(field)s; border: 1px solid %(line)s;
    }
    QCheckBox::indicator:checked { background: %(blue)s; border-color: %(blue)s; }
    QCheckBox#toggle { spacing: 9px; min-height: 24px; }
    QCheckBox#toggle::indicator, QCheckBox#toggle::indicator:checked {
        width: 33px; height: 18px; border: none; background: transparent;
    }
    QFrame#stepper { background: %(field)s; border: 1px solid %(line)s; border-radius: %(fieldRadius)dpx; }
    QFrame#stepper QLineEdit, QLabel#stepValue {
        background: transparent; border: none; padding: 0; font-size: 12px;
    }
    QFrame#stepper QPushButton { background: transparent; border-radius: 8px; padding: 0; min-width: 23px; min-height: 24px; }
    QFrame#stepper QPushButton:hover:enabled { background: %(hover)s; }
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
        min-width: 100px; min-height: 18px; border-radius: 18px;
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
    QPushButton#link:disabled { color: %(faint)s; }
    QPushButton#stepDot { background: transparent; color: %(blue)s; padding: 4px; min-width: 19px; }
    QPushButton#stepDot:hover { background: %(field)s; }
    QPushButton#themeSwitch {
        background: %(soft)s; border: 1px solid %(line)s; border-radius: 12px; padding: 0 14px 0 0;
    }
    QPushButton#themeSwitch:hover, QPushButton#themeSwitch:pressed { background: %(hover)s; }
    QPushButton#themeSwitch:focus, QPushButton#themeSwitch:pressed { border-color: %(blue)s; }
    QPushButton#themeSwitch::menu-indicator {
        image: url("%(assets)s/theme-chevron.svg");
        subcontrol-origin: border; subcontrol-position: center right;
        right: 7px; width: 12px; height: 12px;
    }
    QMenu#themeMenu {
        background: %(card)s; border: 1px solid %(line)s; border-radius: 15px; padding: 6px;
    }
    QLabel#themeMenuTitle { color: %(muted)s; font-size: 11px; font-weight: 700; padding: 7px 9px; }
    QMenu#themeMenu::item { padding: 8px 14px 8px 8px; border-radius: 8px; }
    QMenu#themeMenu::item:checked { background: %(soft)s; }
    QMenu#themeMenu::item:selected { background: %(hover)s; }
    QPushButton#navigation {
        background: transparent; border-radius: %(navRadius)dpx; padding: 0;
    }
    QPushButton#navigation:hover { background: %(field)s; }
    QPushButton#navigation:checked { background: %(blue)s; }
    QFrame#pills { background: %(field)s; border-radius: 17px; }
    QFrame#pills QPushButton {
        background: transparent; border-radius: 14px; padding: 6px 16px; font-weight: 400;
    }
    QFrame#pills QPushButton:hover { background: %(hover)s; }
    QFrame#pills QPushButton:checked { background: %(card)s; }
    """ % colors
