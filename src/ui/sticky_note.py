"""Widget di una singola nota adesiva (post-it) frameless e trascinabile."""
from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QTextCursor, QWheelEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizeGrip,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.storage import NoteData

COLORS = ["#FFF59D", "#A5D6A7", "#90CAF9", "#F48FB1", "#FFCC80", "#CE93D8"]
OPACITIES = [1.0, 0.85, 0.7, 0.55]
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 32
CHECKBOX_UNCHECKED = "[ ]"
CHECKBOX_CHECKED = "[x]"


class ChecklistTextEdit(QTextEdit):
    """QTextEdit che permette di spuntare voci "[ ] ..." con un click e
    di regolare la dimensione del testo con Ctrl+rotellina."""

    font_size_requested = pyqtSignal(int)  # delta (+1/-1)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._toggle_checkbox_at(event.pos()):
            return
        super().mousePressEvent(event)

    def _toggle_checkbox_at(self, pos) -> bool:
        cursor = self.cursorForPosition(pos)
        block = cursor.block()
        text = block.text()
        stripped = text.lstrip()
        leading_ws = len(text) - len(stripped)
        marker = stripped[:3]
        if marker not in (CHECKBOX_UNCHECKED, CHECKBOX_CHECKED):
            return False
        if not (leading_ws <= cursor.positionInBlock() <= leading_ws + len(marker)):
            return False
        new_marker = CHECKBOX_CHECKED if marker == CHECKBOX_UNCHECKED else CHECKBOX_UNCHECKED
        toggle_cursor = QTextCursor(block)
        toggle_cursor.setPosition(block.position() + leading_ws)
        toggle_cursor.setPosition(block.position() + leading_ws + len(marker), QTextCursor.MoveMode.KeepAnchor)
        toggle_cursor.insertText(new_marker)
        return True

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = 1 if event.angleDelta().y() > 0 else -1
            self.font_size_requested.emit(delta)
            event.accept()
        else:
            super().wheelEvent(event)


class DragHandle(QLabel):
    """Maniglia con icona a croce per spostare la nota trascinandola."""

    def __init__(self, target: QWidget, parent=None):
        super().__init__("✥", parent)
        self._target = target
        self._drag_offset: QPoint | None = None
        self.setFixedSize(22, 22)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setToolTip("Trascina per spostare la nota")

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self._target.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._target.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class StickyNote(QWidget):
    """Post-it senza bordi di sistema, che resta sul desktop senza coprire le altre finestre."""

    closed = pyqtSignal(str)  # emesso con l'id della nota quando viene chiusa
    changed = pyqtSignal()  # emesso quando testo/posizione/colore cambiano

    def __init__(self, data: NoteData):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool,
        )
        self.data = data
        self._drag_offset: QPoint | None = None
        self._build_ui()
        self.apply_color(data.color)
        self._apply_font_size()
        self.setWindowOpacity(data.opacity)
        self.move(data.x, data.y)
        self.resize(data.width, data.height)

    def _build_ui(self) -> None:
        self.setWindowTitle(self.data.title)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        top_bar = QHBoxLayout()
        drag_handle = DragHandle(self)
        top_bar.addWidget(drag_handle)

        color_btn = QPushButton("\U0001F3A8")
        color_btn.setFixedSize(22, 22)
        color_btn.setToolTip("Cambia colore")
        color_btn.clicked.connect(self._cycle_color)
        top_bar.addWidget(color_btn)

        opacity_btn = QPushButton("◐")
        opacity_btn.setFixedSize(22, 22)
        opacity_btn.setToolTip("Cambia trasparenza (Ctrl+rotellina sul testo: dimensione carattere)")
        opacity_btn.clicked.connect(self._cycle_opacity)
        top_bar.addWidget(opacity_btn)

        self.title_edit = QLineEdit(self.data.title)
        self.title_edit.setToolTip("Rinomina la nota (es. per raggruppare un macro-argomento)")
        self.title_edit.setFrame(False)
        self.title_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_edit.editingFinished.connect(self._on_title_changed)
        self.title_edit.returnPressed.connect(lambda: self.text_edit.setFocus())
        top_bar.addWidget(self.title_edit, 1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setToolTip("Chiudi nota")
        close_btn.clicked.connect(self._on_close)
        top_bar.addWidget(close_btn)
        layout.addLayout(top_bar)

        self.text_edit = ChecklistTextEdit()
        self.text_edit.setPlainText(self.data.text)
        self.text_edit.setFrameStyle(0)
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.text_edit.font_size_requested.connect(self._adjust_font_size)
        layout.addWidget(self.text_edit)

        grip = QSizeGrip(self)
        layout.addWidget(grip, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

    def apply_color(self, hex_color: str) -> None:
        self.data.color = hex_color
        color = QColor(hex_color)
        self.setStyleSheet(
            f"QWidget {{ background-color: {color.name()}; }}"
            "QTextEdit { background: transparent; border: none; }"
            "QPushButton { background: transparent; border: none; }"
            "QPushButton:hover { background: rgba(0,0,0,30); border-radius: 4px; }"
            "QLineEdit { background: transparent; border: none; font-weight: bold; font-size: 12px; }"
            "QLineEdit:focus { background: rgba(255,255,255,90); border-radius: 3px; }"
            "QLabel { background: transparent; border-radius: 4px; }"
            "QLabel:hover { background: rgba(0,0,0,30); }"
        )

    def _cycle_color(self) -> None:
        current_index = COLORS.index(self.data.color) if self.data.color in COLORS else -1
        next_color = COLORS[(current_index + 1) % len(COLORS)]
        self.apply_color(next_color)
        self.changed.emit()

    def _cycle_opacity(self) -> None:
        current_index = OPACITIES.index(self.data.opacity) if self.data.opacity in OPACITIES else 0
        new_opacity = OPACITIES[(current_index + 1) % len(OPACITIES)]
        self.data.opacity = new_opacity
        self.setWindowOpacity(new_opacity)
        self.changed.emit()

    def _apply_font_size(self) -> None:
        font = self.text_edit.font()
        font.setPointSize(self.data.font_size)
        self.text_edit.setFont(font)

    def _adjust_font_size(self, delta: int) -> None:
        self.data.font_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, self.data.font_size + delta))
        self._apply_font_size()
        self.changed.emit()

    def _on_title_changed(self) -> None:
        self.data.title = self.title_edit.text().strip() or "StickyPy"
        self.title_edit.setText(self.data.title)
        self.setWindowTitle(self.data.title)
        self.changed.emit()

    def _on_text_changed(self) -> None:
        self.data.text = self.text_edit.toPlainText()
        self.changed.emit()

    def _on_close(self) -> None:
        self.close()

    def closeEvent(self, event) -> None:  # noqa: N802 - override Qt
        self.closed.emit(self.data.id)
        super().closeEvent(event)

    def moveEvent(self, event) -> None:  # noqa: N802 - override Qt
        self.data.x = self.x()
        self.data.y = self.y()
        self.changed.emit()
        super().moveEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802 - override Qt
        self.data.width = self.width()
        self.data.height = self.height()
        self.changed.emit()
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)
