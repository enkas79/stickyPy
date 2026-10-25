"""Entry point di StickyPy: note adesive per il desktop."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QKeySequence,
    QPainter,
    QPixmap,
    QShortcut,
)
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from src.core import autostart
from src.core.settings import AppSettings
from src.core.storage import NoteData, is_empty, load_notes, save_notes
from src.ui import styles
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


SAVE_DEBOUNCE_MS = 800


class StickyPyApp:
    """Orchestratore dell'app: system tray, finestra di gestione, note attive."""

    def __init__(self, app: QApplication):
        self.app = app
        self.settings = AppSettings()
        self.all_data: dict[str, NoteData] = {}  # tutte le note (aperte e solo in elenco)
        self.notes: dict[str, StickyNote] = {}  # finestre delle note aperte
        self._quitting = False

        # Debounce: raggruppa le modifiche ravvicinate in un solo salvataggio
        self._save_timer = QTimer(app)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(SAVE_DEBOUNCE_MS)
        self._save_timer.timeout.connect(self._persist_notes)

        self.manager_window = ManagerWindow(
            new_note_callback=self.create_new_note,
            quit_callback=self.quit,
            get_notes_callback=lambda: self.all_data,
            toggle_autostart_callback=self.set_autostart,
            open_note_callback=self.open_note,
            delete_note_callback=self.delete_note,
            settings=self.settings,
            settings_changed_callback=self.apply_theme,
        )

        self.tray_icon = QSystemTrayIcon(_build_tray_icon(), app)
        self.tray_icon.setToolTip("StickyPy")
        self._build_tray_menu()
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

        self._new_note_shortcut = QShortcut(QKeySequence("Ctrl+N"), self.manager_window)
        self._new_note_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._new_note_shortcut.activated.connect(self.create_new_note)

        app.aboutToQuit.connect(self._on_session_end)
        app.commitDataRequest.connect(self._on_session_end)  # spegnimento/logoff: non perdere le note aperte

        self.apply_theme()
        self._load_existing_notes()

    def _build_tray_menu(self) -> None:
        menu = QMenu()

        new_note_action = QAction("Nuova nota", menu)
        new_note_action.triggered.connect(self.create_new_note)
        menu.addAction(new_note_action)

        manage_action = QAction("Gestione note", menu)
        manage_action.triggered.connect(self._show_manager)
        menu.addAction(manage_action)

        raise_all_action = QAction("Porta tutte in primo piano", menu)
        raise_all_action.triggered.connect(self.raise_all_notes)
        menu.addAction(raise_all_action)

        menu.addSeparator()

        self.tray_autostart_action = QAction("Avvia con il PC", menu)
        self.tray_autostart_action.setCheckable(True)
        self.tray_autostart_action.setChecked(autostart.is_enabled())
        self.tray_autostart_action.toggled.connect(self.set_autostart)
        menu.addAction(self.tray_autostart_action)

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

    def set_autostart(self, checked: bool) -> None:
        try:
            if checked:
                autostart.enable()
            else:
                autostart.disable()
        except OSError as exc:
            QMessageBox.warning(
                self.manager_window, "Avvio automatico", f"Impossibile aggiornare l'avvio automatico:\n{exc}"
            )
            checked = autostart.is_enabled()
        self._sync_autostart_actions(checked)

    def _sync_autostart_actions(self, checked: bool) -> None:
        for action in (self.manager_window.autostart_action, self.tray_autostart_action):
            if action.isChecked() != checked:
                action.blockSignals(True)
                action.setChecked(checked)
                action.blockSignals(False)

    def raise_all_notes(self) -> None:
        for note in self.notes.values():
            note.show()
            note.raise_()
            note.activateWindow()

    def apply_theme(self) -> None:
        dark = styles.is_dark_theme(self.settings.theme)
        self.app.setStyleSheet(styles.app_qss(dark))
        self.manager_window.set_dark(dark)
        for note in self.notes.values():
            note.refresh_style(dark)

    def _load_existing_notes(self) -> None:
        for data in load_notes():
            self.all_data[data.id] = data
            if data.is_open:
                self._create_note_widget(data)

    def create_new_note(self) -> None:
        data = NoteData()
        offset = 32 * (len(self.notes) % 8)
        data.x += offset
        data.y += offset
        self.all_data[data.id] = data
        self._create_note_widget(data)
        self._persist_notes()

    def open_note(self, note_id: str) -> None:
        data = self.all_data.get(note_id)
        if data is None:
            return
        note = self.notes.get(note_id)
        if note is None:
            data.is_open = True
            note = self._create_note_widget(data)
            self._persist_notes()
        note.show()
        note.raise_()
        note.activateWindow()

    def delete_note(self, note_id: str) -> None:
        if note_id not in self.all_data:
            return
        if self.settings.confirm_delete:
            answer = QMessageBox.question(
                self.manager_window,
                "Elimina nota",
                "Eliminare questa nota? L'operazione non si può annullare.",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        del self.all_data[note_id]
        note = self.notes.pop(note_id, None)
        if note is not None:
            note.close()
        self._persist_notes()

    def _create_note_widget(self, data: NoteData) -> StickyNote:
        note = StickyNote(data, dark=styles.is_dark_theme(self.settings.theme))
        note.closed.connect(self._on_note_closed)
        note.changed.connect(self._schedule_save)
        note.new_requested.connect(self.create_new_note)
        note.list_requested.connect(self._show_manager)
        note.delete_requested.connect(self.delete_note)
        note.show()
        self.notes[data.id] = note
        return note

    def _on_note_closed(self, note_id: str) -> None:
        if self._quitting or note_id not in self.notes:
            return
        del self.notes[note_id]
        data = self.all_data[note_id]
        if is_empty(data):  # come Sticky Notes: una nota vuota chiusa sparisce
            del self.all_data[note_id]
        else:
            data.is_open = False
        self._persist_notes()

    def _schedule_save(self) -> None:
        self._save_timer.start()

    def _persist_notes(self) -> None:
        self._save_timer.stop()
        save_notes(list(self.all_data.values()))
        if self.manager_window.isVisible():
            self.manager_window.refresh()

    def _on_session_end(self) -> None:
        self._quitting = True
        self._persist_notes()

    def quit(self) -> None:
        self._quitting = True
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

    if not sticky_app.all_data:
        sticky_app.create_new_note()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
