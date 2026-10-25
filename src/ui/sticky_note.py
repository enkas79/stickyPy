"""Finestra di una singola nota, sul modello di Microsoft Sticky Notes."""
from __future__ import annotations

import base64
import time

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, Qt, pyqtSignal
from PyQt6.QtGui import (
    QFont,
    QImage,
    QKeySequence,
    QShortcut,
    QTextCharFormat,
    QTextListFormat,
)
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMenu,
    QSizeGrip,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.core.storage import COLOR_NAMES, NoteData, html_to_plain
from src.ui import styles

IMAGE_FILTER = "Immagini (*.png *.jpg *.jpeg *.bmp *.gif)"


class NoteTextEdit(QTextEdit):
    """Editor rich-text: incolla solo testo semplice e supporta le immagini."""

    def canInsertFromMimeData(self, source) -> bool:
        return source.hasText() or source.hasImage()

    def insertFromMimeData(self, source) -> None:
        if source.hasImage():
            self.insert_image(source.imageData())
        else:
            self.insertPlainText(source.text())

    def insert_image(self, image: QImage) -> None:
        if not isinstance(image, QImage) or image.isNull():
            return
        max_width = max(self.viewport().width() - 24, 64)
        if image.width() > max_width:
            image = image.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        encoded = base64.b64encode(bytes(data)).decode("ascii")
        self.insertHtml(f'<img src="data:image/png;base64,{encoded}" width="{image.width()}"/>')


class DragHeader(QWidget):
    """Barra superiore: trascinandola si sposta la nota."""

    def __init__(self) -> None:
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # sfondo da QSS

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()
        super().mousePressEvent(event)


def _tool_button(text: str, tooltip: str, checkable: bool = False) -> QToolButton:
    button = QToolButton()
    button.setText(text)
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip)
    button.setCheckable(checkable)
    button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    return button


class StickyNote(QWidget):
    closed = pyqtSignal(str)  # id nota: chiusa dall'utente (resta nell'elenco)
    changed = pyqtSignal()  # testo/posizione/colore cambiati
    new_requested = pyqtSignal()
    list_requested = pyqtSignal()
    delete_requested = pyqtSignal(str)

    def __init__(self, data: NoteData, dark: bool = False):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.data = data
        self._dark = dark
        self.setObjectName("note")
        self.setMinimumSize(220, 180)
        self.setWindowTitle("Sticky Notes")
        self._build_ui()
        self._build_shortcuts()
        self.refresh_style()
        self.move(data.x, data.y)
        self.resize(data.width, data.height)

    # --- costruzione ---
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = DragHeader()
        self.header.setObjectName("noteHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(4, 4, 4, 4)
        add_btn = _tool_button("+", "Nuova nota (Ctrl+N)")
        add_btn.clicked.connect(self.new_requested)
        self.menu_btn = _tool_button("⋯", "Menu nota")
        self.menu_btn.clicked.connect(self._show_menu)
        close_btn = _tool_button("✕", "Chiudi nota (Ctrl+W)")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(add_btn)
        header_layout.addStretch(1)
        header_layout.addWidget(self.menu_btn)
        header_layout.addWidget(close_btn)
        root.addWidget(self.header)

        self.text_edit = NoteTextEdit()
        self.text_edit.setFrameStyle(0)
        if "<html" in self.data.text.lower():
            self.text_edit.setHtml(self.data.text)
        else:
            self.text_edit.setPlainText(self.data.text)
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.text_edit.currentCharFormatChanged.connect(self._sync_format_buttons)
        self.text_edit.cursorPositionChanged.connect(self._sync_format_buttons)
        root.addWidget(self.text_edit, 1)

        self.toolbar = QWidget()
        self.toolbar.setObjectName("noteToolbar")
        tool_layout = QHBoxLayout(self.toolbar)
        tool_layout.setContentsMargins(4, 4, 4, 4)
        self.bold_btn = _tool_button("B", "Grassetto (Ctrl+B)", True)
        self.italic_btn = _tool_button("I", "Corsivo (Ctrl+I)", True)
        self.underline_btn = _tool_button("U", "Sottolineato (Ctrl+U)", True)
        self.strike_btn = _tool_button("S", "Barrato (Ctrl+T)", True)
        self.bullet_btn = _tool_button("•≡", "Elenco puntato (Ctrl+Maiusc+L)", True)
        image_btn = _tool_button("🖼", "Inserisci immagine")
        for button, style in (
            (self.bold_btn, "bold"),
            (self.italic_btn, "italic"),
            (self.underline_btn, "underline"),
            (self.strike_btn, "strike"),
        ):
            font = button.font()
            font.setBold(style == "bold")
            font.setItalic(style == "italic")
            font.setUnderline(style == "underline")
            font.setStrikeOut(style == "strike")
            button.setFont(font)
        self.bold_btn.clicked.connect(self.toggle_bold)
        self.italic_btn.clicked.connect(self.toggle_italic)
        self.underline_btn.clicked.connect(self.toggle_underline)
        self.strike_btn.clicked.connect(self.toggle_strike)
        self.bullet_btn.clicked.connect(self.toggle_bullets)
        image_btn.clicked.connect(self.insert_image_from_file)
        for widget in (self.bold_btn, self.italic_btn, self.underline_btn, self.strike_btn, self.bullet_btn, image_btn):
            tool_layout.addWidget(widget)
        tool_layout.addStretch(1)
        tool_layout.addWidget(QSizeGrip(self), 0, Qt.AlignmentFlag.AlignBottom)
        root.addWidget(self.toolbar)

    def _build_shortcuts(self) -> None:
        # Ctrl+B/I/U sono già gestiti da QTextEdit; Ctrl+N è globale (main.py).
        for sequence, slot in (
            ("Ctrl+T", self.toggle_strike),
            ("Ctrl+Shift+L", self.toggle_bullets),
            ("Ctrl+D", lambda: self.delete_requested.emit(self.data.id)),
            ("Ctrl+W", self.close),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(slot)

    # --- stile ---
    def refresh_style(self, dark: bool | None = None) -> None:
        if dark is not None:
            self._dark = dark
        self.setStyleSheet(styles.note_qss(styles.swatch_for(self.data.color, self._dark)))

    def set_color(self, name: str) -> None:
        if name in COLOR_NAMES:
            self.data.color = name
            self.refresh_style()
            self.changed.emit()

    def _show_menu(self) -> None:
        menu = QMenu(self)
        for name in COLOR_NAMES:
            entry = styles.NOTE_COLORS[name]
            swatch = styles.swatch_for(name, self._dark)
            action = menu.addAction(styles.color_icon(swatch.body, name == self.data.color), entry.label)
            action.triggered.connect(lambda _=False, n=name: self.set_color(n))
        menu.addSeparator()
        menu.addAction("Elenco note").triggered.connect(self.list_requested)
        menu.addAction("Elimina nota").triggered.connect(lambda: self.delete_requested.emit(self.data.id))
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))

    # --- formattazione ---
    def _merge_format(self, **kwargs) -> None:
        fmt = QTextCharFormat()
        if "bold" in kwargs:
            fmt.setFontWeight(QFont.Weight.Bold if kwargs["bold"] else QFont.Weight.Normal)
        if "italic" in kwargs:
            fmt.setFontItalic(kwargs["italic"])
        if "underline" in kwargs:
            fmt.setFontUnderline(kwargs["underline"])
        if "strike" in kwargs:
            fmt.setFontStrikeOut(kwargs["strike"])
        self.text_edit.mergeCurrentCharFormat(fmt)
        self.text_edit.setFocus()

    def toggle_bold(self) -> None:
        self._merge_format(bold=self.text_edit.fontWeight() != QFont.Weight.Bold)

    def toggle_italic(self) -> None:
        self._merge_format(italic=not self.text_edit.fontItalic())

    def toggle_underline(self) -> None:
        self._merge_format(underline=not self.text_edit.fontUnderline())

    def toggle_strike(self) -> None:
        self._merge_format(strike=not self.text_edit.currentCharFormat().fontStrikeOut())

    def toggle_bullets(self) -> None:
        cursor = self.text_edit.textCursor()
        current_list = cursor.currentList()
        if current_list is not None:
            current_list.remove(cursor.block())
            block_format = cursor.blockFormat()
            block_format.setIndent(0)
            cursor.setBlockFormat(block_format)
        else:
            cursor.createList(QTextListFormat.Style.ListDisc)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.setFocus()
        self._sync_format_buttons()

    def insert_image_from_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Inserisci immagine", "", IMAGE_FILTER)
        if path:
            self.text_edit.insert_image(QImage(path))

    def _sync_format_buttons(self, *_args) -> None:
        fmt = self.text_edit.currentCharFormat()
        self.bold_btn.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.italic_btn.setChecked(fmt.fontItalic())
        self.underline_btn.setChecked(fmt.fontUnderline())
        self.strike_btn.setChecked(fmt.fontStrikeOut())
        self.bullet_btn.setChecked(self.text_edit.textCursor().currentList() is not None)

    # --- eventi / persistenza ---
    def plain_text(self) -> str:
        return html_to_plain(self.data.text)

    def _on_text_changed(self) -> None:
        self.data.text = self.text_edit.toHtml()
        self.data.modified = time.time()
        self.changed.emit()

    def closeEvent(self, event) -> None:
        self.closed.emit(self.data.id)
        super().closeEvent(event)

    def moveEvent(self, event) -> None:
        self.data.x, self.data.y = self.x(), self.y()
        self.changed.emit()
        super().moveEvent(event)

    def resizeEvent(self, event) -> None:
        self.data.width, self.data.height = self.width(), self.height()
        self.changed.emit()
        super().resizeEvent(event)
