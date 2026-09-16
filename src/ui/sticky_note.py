"""Widget di una singola nota adesiva (post-it) frameless e trascinabile."""
from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSizeGrip,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.storage import NoteData

COLORS = ["#FFF59D", "#A5D6A7", "#90CAF9", "#F48FB1", "#FFCC80", "#CE93D8"]


class StickyNote(QWidget):
    """Post-it flottante sempre in primo piano, senza bordi di sistema."""

    closed = pyqtSignal(str)  # emesso con l'id della nota quando viene chiusa
    changed = pyqtSignal()  # emesso quando testo/posizione/colore cambiano

    def __init__(self, data: NoteData):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.data = data
        self._drag_offset: QPoint | None = None
        self._build_ui()
        self.apply_color(data.color)
        self.move(data.x, data.y)
        self.resize(data.width, data.height)

    def _build_ui(self) -> None:
        self.setWindowTitle("StickyPy - Nota")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        top_bar = QHBoxLayout()
        color_btn = QPushButton("\U0001F3A8")
        color_btn.setFixedSize(22, 22)
        color_btn.setToolTip("Cambia colore")
        color_btn.clicked.connect(self._cycle_color)
        top_bar.addWidget(color_btn)
        top_bar.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setToolTip("Chiudi nota")
        close_btn.clicked.connect(self._on_close)
        top_bar.addWidget(close_btn)
        layout.addLayout(top_bar)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.data.text)
        self.text_edit.setFrameStyle(0)
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit)

        grip = QSizeGrip(self)
        layout.addWidget(grip, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

    def apply_color(self, hex_color: str) -> None:
        self.data.color = hex_color
        color = QColor(hex_color)
        self.setStyleSheet(
            f"QWidget {{ background-color: {color.name()}; }}"
            "QTextEdit { background: transparent; border: none; font-size: 13px; }"
            "QPushButton { background: transparent; border: none; }"
            "QPushButton:hover { background: rgba(0,0,0,30); border-radius: 4px; }"
        )

    def _cycle_color(self) -> None:
        current_index = COLORS.index(self.data.color) if self.data.color in COLORS else -1
        next_color = COLORS[(current_index + 1) % len(COLORS)]
        self.apply_color(next_color)
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
