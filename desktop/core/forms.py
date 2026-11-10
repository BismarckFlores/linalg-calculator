"""Formularios, resultados y recorridos compartidos."""

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QBoxLayout, QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from .math_input import MathInput
from .widgets import ResultTable, SegmentedControl, Stepper, action, card, label, link, page_header


def text_input(name: str, value: str, *, multiline: bool = False) -> QWidget:
    widget = QPlainTextEdit(value) if multiline else QLineEdit(value)
    widget.setAccessibleName(name)
    if multiline:
        widget.setFixedHeight(110)
    return widget


class FieldRow(QWidget):
    """Campos alineados arriba en columnas que se apilan si falta ancho."""

    def __init__(self, fields: tuple[QWidget, ...]) -> None:
        super().__init__()
        self.fields = fields
        if all(field.maximumWidth() < 1000 for field in fields):
            self.setMaximumWidth(sum(field.maximumWidth() for field in fields) + 20 * (len(fields) - 1))
        row = QVBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        for field in fields:
            row.addWidget(field, 1, Qt.AlignmentFlag.AlignTop)

    def minimumSizeHint(self) -> QSize:
        width = max(field.minimumSizeHint().width() for field in self.fields)
        return QSize(width, super().minimumSizeHint().height())

    def resizeEvent(self, event) -> None:
        row = self.layout()
        fields = [field for field in self.fields if not field.isHidden()]
        spacing = 20
        widths = [max(field.minimumWidth(), field.minimumSizeHint().width()) for field in fields]
        equal_columns = not all(field.maximumWidth() < 1000 for field in fields)
        required = max(widths, default=0) * len(fields) if equal_columns else sum(widths)
        horizontal = required + max(0, len(fields) - 1) * spacing <= event.size().width()
        row.setDirection(QBoxLayout.Direction.LeftToRight if horizontal else QBoxLayout.Direction.TopToBottom)
        row.setSpacing(spacing if horizontal else 12)
        super().resizeEvent(event)


@dataclass(frozen=True)
class Result:
    text: str
    steps: tuple[str, ...] = ()
    headers: tuple[str, ...] = ()
    rows: tuple[tuple, ...] = ()
    sections: tuple[str, ...] = ()
    title: str = ""
    badge: str = ""


class StepView(QWidget):
    """Navega resultados ya calculados y permite desplegar el recorrido."""

    def __init__(self, caption: str = "Paso", *, title: str = "Paso a paso") -> None:
        super().__init__()
        self.steps: tuple[str, ...] = ()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        heading = QHBoxLayout()
        heading.addWidget(label(title, "heading"), 1)
        self.total = label("", "count")
        heading.addWidget(self.total)
        layout.addLayout(heading)
        self.step_title = label("", "stepTitle")
        layout.addWidget(self.step_title)
        self.output = MathInput("", "", "output")
        layout.addWidget(self.output)
        self.dots = QWidget()
        dot_row = QHBoxLayout(self.dots)
        dot_row.setContentsMargins(0, 0, 0, 0)
        dot_row.setSpacing(3)
        self.markers = []
        for index in range(1, 13):
            dot = QPushButton("○")
            dot.setObjectName("stepDot")
            dot.setAccessibleName(f"{caption} {index}")
            dot.clicked.connect(lambda checked=False, number=index: self.index.setValue(number))
            dot_row.addWidget(dot)
            self.markers.append(dot)
        layout.addWidget(self.dots, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.index = Stepper(caption, 1, 1, 1)
        layout.addWidget(self.index, alignment=Qt.AlignmentFlag.AlignHCenter)
        controls = QHBoxLayout()
        self.previous, self.next_step = link("‹  Anterior"), link("Siguiente  ›")
        self.all_steps = link("Ver todos los pasos ▾")
        self.all_steps.setCheckable(True)
        controls.addWidget(self.previous)
        controls.addStretch()
        controls.addWidget(self.all_steps)
        controls.addStretch()
        controls.addWidget(self.next_step)
        layout.addLayout(controls)
        self.previous.clicked.connect(self.index.stepDown)
        self.next_step.clicked.connect(self.index.stepUp)
        self.index.valueChanged.connect(self._show)
        self.all_steps.toggled.connect(self._show)

    def set_steps(self, steps: tuple[str, ...]) -> None:
        self.steps = steps
        self.index.setRange(1, max(1, len(steps)))
        self.index.setValue(1)
        self.setVisible(bool(steps))
        self._show()

    def _show(self) -> None:
        if not self.steps:
            return
        show_all = self.all_steps.isChecked()
        current, count = self.index.value(), len(self.steps)
        self.total.setText(f"{count} pasos" if show_all else f"{current} / {count}")
        self.previous.setVisible(not show_all)
        self.next_step.setVisible(not show_all)
        self.previous.setEnabled(not show_all and current > 1)
        self.next_step.setEnabled(not show_all and current < count)
        self.index.setEnabled(not show_all and count > 1)
        self.index.setVisible(not show_all and count > len(self.markers))
        self.dots.setVisible(not show_all and 1 < count <= len(self.markers))
        for index, dot in enumerate(self.markers, 1):
            dot.setVisible(index <= count)
            dot.setText("◉" if index == current else "○")
        self.all_steps.setText("Ver un paso ▴" if show_all else "Ver todos los pasos ▾")
        if show_all:
            self.step_title.hide()
            self.output.set_value("\n\n".join(
                f"Paso {i}\n{step}" for i, step in enumerate(self.steps, 1)
            ))
        else:
            step = self.steps[current - 1]
            title, separator, body = step.partition("\n")
            has_heading = body.startswith("[ ") and bool(separator)
            self.step_title.setVisible(has_heading)
            self.step_title.setText(title if has_heading else "")
            self.output.set_value(body if has_heading else step)


class ToolPage(QWidget):
    """Presenta un formulario, invalida resultados y conecta su cálculo."""

    def __init__(
        self, glyph: str, title: str, subtitle: str, fields: list[QWidget | tuple[QWidget, ...]],
        button: str, calculate: Callable[[], Result],
        *, above: tuple[QWidget, ...] = (), before: tuple[str, ...] = (),
        between: tuple[str, ...] = (), after: tuple[str, ...] = (),
        answer_title: str = "Resultado", walk_title: str = "Paso a paso",
    ) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        self.header = page_header(glyph, title, subtitle)
        layout.addWidget(self.header)
        for field in above:
            if isinstance(field, QLabel):
                layout.addWidget(field)
            else:
                layout.addWidget(field, alignment=Qt.AlignmentFlag.AlignLeft)
        panel, self.form = card()
        self.form.setSpacing(16)
        inputs = list(above)
        for field in fields:
            if isinstance(field, tuple):
                self.form.addWidget(FieldRow(field))
                inputs.extend(field)
            else:
                self.form.addWidget(field)
                inputs.append(field)
        submit = action(button)
        submit.clicked.connect(self._calculate)
        self.error = label("", "inputError")
        self.error.hide()
        self.form.addWidget(self.error)
        self.form.addWidget(submit, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(panel)
        self.result = QWidget()
        results = QVBoxLayout(self.result)
        results.setContentsMargins(0, 0, 0, 0)
        results.setSpacing(16)
        self._sections = []

        def add_section(heading: str) -> None:
            section, section_layout = card()
            section_layout.addWidget(label(heading, "heading"))
            editor = MathInput("", "", "output")
            section_layout.addWidget(editor)
            results.addWidget(section)
            self._sections.append((section, editor))

        for heading in before:
            add_section(heading)
        self.walk_card, walk_layout = card()
        self.walk = StepView(title=walk_title)
        walk_layout.addWidget(self.walk)
        results.addWidget(self.walk_card)
        for heading in between:
            add_section(heading)
        answer, result_layout = card()
        self.answer_title = answer_title
        heading = QHBoxLayout()
        self.result_title = label(answer_title, "heading")
        self.result_badge = label("", "count")
        self.result_badge.hide()
        heading.addWidget(self.result_title, 1)
        heading.addWidget(self.result_badge)
        result_layout.addLayout(heading)
        self.output = MathInput("", "", "output")
        result_layout.addWidget(self.output)
        results.addWidget(answer)
        for heading in after:
            add_section(heading)
        self.table_card, table_layout = card()
        table_layout.addWidget(label("Tabla", "heading"))
        self.table = ResultTable()
        table_layout.addWidget(self.table)
        results.addWidget(self.table_card)
        layout.addWidget(self.result)
        self.result.hide()
        layout.addStretch()
        self._solve = calculate

        for field in inputs:
            if isinstance(field, MathInput):
                field.changed.connect(self._clear)
            elif isinstance(field, SegmentedControl):
                field.currentIndexChanged.connect(self._clear)
            elif isinstance(field, (QCheckBox, Stepper)):
                signal = field.toggled if isinstance(field, QCheckBox) else field.valueChanged
                signal.connect(self._clear)
            elif isinstance(field, (QLineEdit, QPlainTextEdit)):
                field.textChanged.connect(self._clear)

    def _clear(self) -> None:
        self.result.hide()
        self.error.hide()

    def _calculate(self) -> None:
        self._clear()
        try:
            result = self._solve()
        except (TypeError, ValueError, ArithmeticError) as problem:
            self.error.setText(str(problem))
            self.error.show()
            return
        self.output.set_value(result.text)
        self.result_title.setText(result.title or self.answer_title)
        self.result_badge.setText(result.badge)
        self.result_badge.setVisible(bool(result.badge))
        for index, (panel, editor) in enumerate(self._sections):
            value = result.sections[index] if index < len(result.sections) else ""
            editor.set_value(value)
            panel.setVisible(bool(value))
        self.walk.set_steps(result.steps)
        self.walk_card.setVisible(bool(result.steps))
        self.table.fill(result.headers, result.rows)
        self.table_card.setVisible(bool(result.headers))
        self.result.show()
