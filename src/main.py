"""Entry point di StickyPy: note adesive per il desktop."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.core.storage import NoteData, load_notes, save_notes
from src.ui.manager_window import ManagerWindow
from src.ui.sticky_note import StickyNote


def _build_tray_icon() -> QIcon:
    """Icona semplice generata a runtime (evita di dipendere da un file .ico esterno)."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor("#FFF59D"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("#BFAF4A"))
    painter.drawRect(0, 0, 63, 63)
    painter.end()
    return QIcon(pixmap)


class StickyPyApp:
    """Orchestratore dell'app: system tray, finestra di gestione, note attive."""

    def __init__(self, app: QApplication):
        self.app = app
        self.notes: dict[str, StickyNote] = {}

        self.manager_window = ManagerWindow(
            new_note_callback=self.create_new_note,
            quit_callback=self.quit,
        )

        self.tray_icon = QSystemTrayIcon(_build_tray_icon(), app)
        self.tray_icon.setToolTip("StickyPy")
        self._build_tray_menu()
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

        self._load_existing_notes()

    def _build_tray_menu(self) -> None:
        menu = QMenu()

        new_note_action = QAction("Nuova nota", menu)
        new_note_action.triggered.connect(self.create_new_note)
        menu.addAction(new_note_action)

        manage_action = QAction("Gestione note", menu)
        manage_action.triggered.connect(self._show_manager)
        menu.addAction(manage_action)

        menu.addSeparator()

        quit_action = QAction("Esci", menu)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_manager()

    def _show_manager(self) -> None:
        self.manager_window.show()
        self.manager_window.raise_()
        self.manager_window.activateWindow()

    def _load_existing_notes(self) -> None:
        for data in load_notes():
            self._create_note_widget(data)

    def create_new_note(self) -> None:
        data = NoteData()
        self._create_note_widget(data)
        self._persist_notes()

    def _create_note_widget(self, data: NoteData) -> None:
        note = StickyNote(data)
        note.closed.connect(self._on_note_closed)
        note.changed.connect(self._persist_notes)
        note.show()
        self.notes[data.id] = note

    def _on_note_closed(self, note_id: str) -> None:
        self.notes.pop(note_id, None)
        self._persist_notes()

    def _persist_notes(self) -> None:
        save_notes([note.data for note in self.notes.values()])

    def quit(self) -> None:
        self._persist_notes()
        self.tray_icon.hide()
        self.app.quit()


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("StickyPy")

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray non disponibile su questo sistema.")

    sticky_app = StickyPyApp(app)

    if not sticky_app.notes:
        sticky_app.create_new_note()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
