"""Tabla paginada y formato numérico para métodos de búsqueda de raíces."""

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from desktop.core.widgets import ResultTable, SegmentedControl, Stepper, label


class IterationTable(QWidget):
    PAGE_SIZE = 15

    def __init__(self, headers: tuple[str, ...]) -> None:
        super().__init__()
        self._headers = headers
        self._rows: list[tuple] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("Tabla de iteraciones", "heading"))
        controls = QHBoxLayout()
        self.format = SegmentedControl("Automático", "Decimal")
        self.format.setAccessibleName("Formato numérico")
        self.decimals = Stepper("Decimales", 0, 17, 5)
        self.page = Stepper("Página de la tabla", 1, 1, 1)
        for widget in (self.format, self.decimals, label("Página", "caption"), self.page):
            controls.addWidget(widget)
        controls.addStretch()
        self.decimals.hide()
        layout.addLayout(controls)
        self.table = ResultTable()
        layout.addWidget(self.table)
        self.format.currentIndexChanged.connect(self._fill)
        self.decimals.valueChanged.connect(self._fill)
        self.page.valueChanged.connect(self._fill)

    def set_rows(self, rows: list[tuple], *, headers: tuple[str, ...] | None = None) -> None:
        if headers is not None:
            self._headers = headers
        self._rows = rows
        self.page.setRange(1, max(1, (len(rows) + self.PAGE_SIZE - 1) // self.PAGE_SIZE))
        self.page.setValue(1)
        self._fill()

    def select_iteration(self, index: int) -> None:
        if 1 <= index <= len(self._rows):
            page, row = divmod(index - 1, self.PAGE_SIZE)
            self.page.setValue(page + 1)
            self.table.selectRow(row)

    def _fill(self) -> None:
        decimal = self.format.currentIndex() == 1
        self.decimals.setVisible(decimal)
        offset = (self.page.value() - 1) * self.PAGE_SIZE
        self.table.fill(
            self._headers, self._rows[offset:offset + self.PAGE_SIZE],
            decimals=self.decimals.value() if decimal else None,
        )
