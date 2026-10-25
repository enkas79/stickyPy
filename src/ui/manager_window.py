"""Elenco note (come la home di Sticky Notes): ricerca, nuova nota, impostazioni, menu Aiuto."""
from __future__ import annotations

import time
from html import escape
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.core import autostart
from src.core.settings import AppSettings
from src.core.storage import html_to_plain
from src.core.updater import UpdateChecker, get_current_version
from src.ui import styles
from src.ui.guide_dialog import GuideDialog
from src.ui.settings_dialog import SettingsDialog

APP_AUTHOR = "enkas79"
PREVIEW_CHARS = 120


class ManagerWindow(QMainWindow):
    def __init__(
        self,
        new_note_callback,
        quit_callback,
        get_notes_callback,
        toggle_autostart_callback,
        open_note_callback,
        delete_note_callback,
        settings: AppSettings,
        settings_changed_callback,
    ):
        super().__init__()
        self._new_note_callback = new_note_callback
        self._quit_callback = quit_callback
        self._get_notes_callback = get_notes_callback  # -> dict[str, NoteData]
        self._toggle_autostart_callback = toggle_autostart_callback
        self._open_note_callback = open_note_callback
        self._delete_note_callback = delete_note_callback
        self._settings = settings
        self._settings_changed_callback = settings_changed_callback
        self._update_checker: UpdateChecker | None = None
        self._dark = False

        self.setWindowTitle("Sticky Notes")
        self.resize(380, 520)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        top = QHBoxLayout()
        title = QLabel("Sticky Notes")
        title.setObjectName("listTitle")
        top.addWidget(title, 1)
        settings_btn = QToolButton()
        settings_btn.setText("⚙")
        settings_btn.setToolTip("Impostazioni")
        settings_btn.setAccessibleName("Impostazioni")
        settings_btn.clicked.connect(self._open_settings)
        add_btn = QToolButton()
        add_btn.setObjectName("addButton")
        add_btn.setText("+")
        add_btn.setToolTip("Nuova nota (Ctrl+N)")
        add_btn.setAccessibleName("Nuova nota")
        add_btn.clicked.connect(self._new_note_callback)
        top.addWidget(settings_btn)
        top.addWidget(add_btn)
        layout.addLayout(top)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Cerca")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.refresh)
        layout.addWidget(self.search_edit)

        self.notes_list = QListWidget()
        self.notes_list.setSpacing(0)
        self.notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.notes_list.customContextMenuRequested.connect(self._list_menu)
        self.notes_list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self.notes_list)

        self.setCentralWidget(central)
        self._build_menu()

    # --- elenco ---
    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        self.refresh()

    def showEvent(self, event) -> None:
        self.refresh()
        super().showEvent(event)

    def refresh(self, *_args) -> None:
        query = self.search_edit.text().strip().lower()
        selected = self._current_id()
        self.notes_list.clear()
        notes = sorted(self._get_notes_callback().values(), key=lambda n: n.modified, reverse=True)
        for note in notes:
            plain = html_to_plain(note.text).strip()
            if query and query not in plain.lower():
                continue
            preview = " ".join(plain.split())[:PREVIEW_CHARS] or "Nota vuota"
            stamp = time.strftime("%d/%m/%Y %H:%M", time.localtime(note.modified))
            swatch = styles.swatch_for(note.color, self._dark)
            card = QLabel(f"{escape(preview)}<br><small>{stamp}</small>")
            card.setWordWrap(True)
            card.setStyleSheet(
                f"background: {swatch.body}; color: {swatch.text}; border-radius: 4px; padding: 8px;"
            )
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 80))
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            self.notes_list.addItem(item)
            self.notes_list.setItemWidget(item, card)
            if note.id == selected:
                self.notes_list.setCurrentItem(item)

    def _current_id(self) -> str | None:
        item = self.notes_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        self._open_note_callback(item.data(Qt.ItemDataRole.UserRole))

    def _list_menu(self, pos) -> None:
        item = self.notes_list.itemAt(pos)
        if item is None:
            return
        note_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.addAction("Apri nota").triggered.connect(lambda: self._open_note_callback(note_id))
        menu.addAction("Elimina nota").triggered.connect(lambda: self._delete_note_callback(note_id))
        menu.exec(self.notes_list.viewport().mapToGlobal(pos))

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._settings, self)
        if dialog.exec():
            dialog.apply_to(self._settings)
            self._settings_changed_callback()

    # --- menu ---
    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        new_note_action = QAction("&Nuova nota", self)
        new_note_action.triggered.connect(self._new_note_callback)
        file_menu.addAction(new_note_action)

        self.autostart_action = QAction("Avvia con il PC", self)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(autostart.is_enabled())
        self.autostart_action.toggled.connect(self._toggle_autostart_callback)
        file_menu.addAction(self.autostart_action)

        settings_action = QAction("&Impostazioni...", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        export_action = QAction("&Esporta note in .txt...", self)
        export_action.triggered.connect(self._export_notes)
        file_menu.addAction(export_action)

        file_menu.addSeparator()
        quit_action = QAction("&Esci", self)
        quit_action.triggered.connect(self._quit_callback)
        file_menu.addAction(quit_action)

        help_menu = menu_bar.addMenu("&Aiuto")
        about_action = QAction("&Informazioni", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        update_action = QAction("Controlla &aggiornamenti", self)
        update_action.triggered.connect(self._check_updates)
        help_menu.addAction(update_action)
        guide_action = QAction("&Guida", self)
        guide_action.triggered.connect(self._show_guide)
        help_menu.addAction(guide_action)

    def _export_notes(self) -> None:
        notes = self._get_notes_callback()
        if not notes:
            QMessageBox.information(self, "Esporta note", "Non ci sono note da esportare.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Esporta note in .txt", "stickypy_note.txt", "File di testo (*.txt)"
        )
        if not file_path:
            return
        blocks = [html_to_plain(n.text) + "\n" for n in sorted(notes.values(), key=lambda n: n.modified)]
        try:
            Path(file_path).write_text("\n---\n".join(blocks), encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Esporta note", f"Impossibile salvare il file:\n{exc}")
            return
        QMessageBox.information(self, "Esporta note", "Note esportate correttamente.")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "Informazioni su StickyPy",
            f"<h3>StickyPy</h3><p>Versione: {get_current_version()}</p>"
            f"<p>Autore: {APP_AUTHOR}</p>"
            "<p>Clone di Microsoft Sticky Notes per tutti i sistemi.</p>",
        )

    def _show_guide(self) -> None:
        GuideDialog(self).exec()

    def _check_updates(self) -> None:
        self._update_checker = UpdateChecker()
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.up_to_date.connect(self._on_up_to_date)
        self._update_checker.check_failed.connect(self._on_update_failed)
        self._update_checker.start()

    def _on_update_available(self, version: str, url: str, changelog: str) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("Aggiornamento disponibile")
        box.setText(f"È disponibile la versione {version}.\nVuoi aprire la pagina di download?")
        box.setDetailedText(changelog or "Nessuna nota di rilascio disponibile.")
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if box.exec() == QMessageBox.StandardButton.Yes:
            import webbrowser

            webbrowser.open(url)

    def _on_up_to_date(self) -> None:
        QMessageBox.information(self, "Aggiornamenti", "Stai già usando l'ultima versione disponibile.")

    def _on_update_failed(self, error: str) -> None:
        QMessageBox.warning(self, "Aggiornamenti", f"Controllo aggiornamenti non riuscito:\n{error}")

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
