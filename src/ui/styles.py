"""Palette e fogli di stile (QSS) centralizzati, tema chiaro/scuro."""
from __future__ import annotations

from typing import NamedTuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication

FONT = '"Segoe UI", "Noto Sans", "Helvetica Neue", sans-serif'


class Swatch(NamedTuple):
    body: str
    header: str
    text: str
    hover: str


class NoteColor(NamedTuple):
    label: str
    light: Swatch
    dark: Swatch


_LT, _DT = "#1B1B1B", "#F2F2F2"
_HL, _HD = "rgba(0,0,0,28)", "rgba(255,255,255,40)"

# Testo/sfondo: contrasto >= 4.5:1 (WCAG AA) in tutte le combinazioni.
NOTE_COLORS: dict[str, NoteColor] = {
    "yellow": NoteColor("Giallo", Swatch("#FFF7D1", "#FFEC8B", _LT, _HL), Swatch("#4F4620", "#3F3818", _DT, _HD)),
    "green": NoteColor("Verde", Swatch("#E3F6D8", "#C5EBB0", _LT, _HL), Swatch("#2F4F35", "#243D29", _DT, _HD)),
    "pink": NoteColor("Rosa", Swatch("#FFE3EF", "#FFC4DC", _LT, _HL), Swatch("#5A3045", "#47243A", _DT, _HD)),
    "purple": NoteColor("Viola", Swatch("#EEE3FF", "#D8C3FF", _LT, _HL), Swatch("#46365F", "#362A4B", _DT, _HD)),
    "blue": NoteColor("Blu", Swatch("#D9F0FF", "#B2DFFF", _LT, _HL), Swatch("#2A4860", "#20384B", _DT, _HD)),
    "gray": NoteColor("Grigio", Swatch("#EBEBEB", "#D4D4D4", _LT, _HL), Swatch("#484848", "#383838", _DT, _HD)),
    "charcoal": NoteColor("Antracite", Swatch("#595959", "#454545", _DT, _HD), Swatch("#2B2B2B", "#1E1E1E", _DT, _HD)),
}


def swatch_for(color_name: str, dark: bool) -> Swatch:
    entry = NOTE_COLORS.get(color_name, NOTE_COLORS["yellow"])
    return entry.dark if dark else entry.light


def color_icon(hex_color: str, checked: bool) -> QIcon:
    """Pallino colorato per il menu colori (con segno di spunta se attivo)."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(hex_color))
    painter.setPen(QColor("#6E6E6E"))
    painter.drawEllipse(1, 1, 14, 14)
    if checked:
        painter.setPen(QColor("#1B1B1B"))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "✓")
    painter.end()
    return QIcon(pixmap)


def is_dark_theme(theme: str) -> bool:
    if theme == "dark":
        return True
    if theme == "light":
        return False
    scheme = QApplication.styleHints().colorScheme()
    return scheme == Qt.ColorScheme.Dark


def note_qss(s: Swatch) -> str:
    return f"""
QWidget#note {{ background: transparent; }}
QWidget#noteFrame {{ background: {s.body}; border: 1px solid {s.header}; border-radius: 8px; }}
QWidget#noteHeader {{ background: {s.header}; border-top-left-radius: 7px; border-top-right-radius: 7px; }}
QWidget#noteToolbar {{ background: {s.body}; border-top: 1px solid {s.header};
    border-bottom-left-radius: 7px; border-bottom-right-radius: 7px; }}
QTextEdit {{ background: {s.body}; color: {s.text}; border: none; padding: 8px;
    font-family: {FONT}; font-size: 15px; selection-background-color: #0F6CBD; selection-color: #FFFFFF; }}
QToolButton {{ background: transparent; color: {s.text}; border: none; border-radius: 4px;
    min-width: 28px; min-height: 28px; font-family: {FONT}; font-size: 15px; }}
QToolButton:hover {{ background: {s.hover}; }}
QToolButton:checked {{ background: {s.hover}; }}
QToolButton:focus {{ border: 1px solid {s.text}; }}
QMenu {{ background: {s.body}; color: {s.text}; border: 1px solid {s.header}; padding: 4px; }}
QMenu::item {{ padding: 4px 24px 4px 12px; }}
QMenu::item:selected {{ background: {s.header}; }}
QMenu::separator {{ height: 1px; background: {s.header}; margin: 4px 0; }}
"""


def app_qss(dark: bool) -> str:
    bg, fg, card, border, accent = (
        ("#202020", "#F2F2F2", "#2B2B2B", "#4A4A4A", "#60CDFF")
        if dark
        else ("#F3F3F3", "#1B1B1B", "#FFFFFF", "#C8C8C8", "#0F6CBD")
    )
    btn_fg = "#1B1B1B" if dark else "#FFFFFF"
    return f"""
QMainWindow, QDialog, QMessageBox {{ background: {bg}; color: {fg}; font-family: {FONT}; font-size: 14px; }}
QMainWindow QLabel, QDialog QLabel, QMessageBox QLabel, QCheckBox {{ color: {fg}; background: transparent; }}
QLabel#listTitle {{ font-size: 20px; font-weight: 600; }}
QMenuBar {{ background: {bg}; color: {fg}; }}
QMenuBar::item:selected, QMenu::item:selected {{ background: {border}; }}
QMenu {{ background: {card}; color: {fg}; border: 1px solid {border}; padding: 4px; }}
QMenu::item {{ padding: 4px 24px; }}
QMenu::separator {{ height: 1px; background: {border}; margin: 4px 0; }}
QLineEdit, QComboBox, QTextBrowser {{ background: {card}; color: {fg}; border: 1px solid {border};
    border-radius: 4px; padding: 4px 8px; }}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {accent}; }}
QComboBox QAbstractItemView {{ background: {card}; color: {fg}; selection-background-color: {accent};
    selection-color: {btn_fg}; }}
QListWidget {{ background: transparent; border: none; outline: none; }}
QListWidget::item {{ padding: 4px 0; }}
QListWidget::item:selected {{ background: transparent; border: 2px solid {accent}; border-radius: 6px; }}
QToolButton, QPushButton {{ background: {card}; color: {fg}; border: 1px solid {border};
    border-radius: 4px; min-width: 32px; min-height: 32px; padding: 0 8px; font-size: 16px; }}
QToolButton:hover, QPushButton:hover {{ border: 1px solid {accent}; }}
QToolButton:focus, QPushButton:focus {{ border: 2px solid {accent}; }}
QToolButton#addButton {{ background: {accent}; color: {btn_fg}; border: none; font-weight: 600; }}
"""
