"""Comunicación entre Qt y el editor MathLive local."""

from PySide6.QtCore import QObject, Signal, Slot

from ..math_notation import to_latex


class EditorBridge(QObject):
    """Recibe la expresión y la altura del campo de MathLive."""

    expression_changed = Signal(str)
    field_resized = Signal(int)
    initialized = Signal()

    def __init__(self, kind: str, parent: QObject) -> None:
        super().__init__(parent)
        self.kind = kind

    @Slot(str)
    def changed(self, value: str) -> None:
        self.expression_changed.emit(value)

    @Slot(str, result=str)
    def latexForPaste(self, text: str) -> str:
        try:
            return to_latex(text, self.kind, paste=True)
        except ValueError:
            # MathLive también permite pegar fragmentos que aún no son una función completa.
            return ""

    @Slot(int)
    def viewHeight(self, height: int) -> None:
        self.field_resized.emit(height)

    @Slot()
    def ready(self) -> None:
        self.initialized.emit()
