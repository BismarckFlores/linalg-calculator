"""Estilos y componentes Qt compartidos."""

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFontDatabase, QIntValidator, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QCheckBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ui import theme_tokens as theme


def card() -> tuple[QFrame, QVBoxLayout]:
    panel = QFrame()
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
                item = QTableWidgetItem(display)
                if value is not None:
                    item.setToolTip(str(value))
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
    QLabel#fieldTitle { font-size: 11px; color: %(muted)s; font-weight: 700; }
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
    QLabel#advice { background: %(field)s; border-radius: 14px; padding: 12px 16px; }
    QLabel#stepTitle { background: %(field)s; border-radius: 12px; padding: 13px 16px; }
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
    QPushButton#themeSwitch { border-radius: 15px; padding: 0; font-weight: 400; }
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
