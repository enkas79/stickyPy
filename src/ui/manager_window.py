"""Finestra principale di gestione: barra dei menu, note, aggiornamenti, avvio automatico."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget

from src.core import autostart
from src.core.updater import UpdateChecker, get_current_version
from src.ui.guide_dialog import GuideDialog

APP_AUTHOR = "enkas79"


class ManagerWindow(QMainWindow):
    """Finestra principale con QMenuBar, richiesta dalle linee guida del progetto."""

    def __init__(self, new_note_callback, quit_callback):
        super().__init__()
        self._new_note_callback = new_note_callback
        self._quit_callback = quit_callback
        self._update_checker: UpdateChecker | None = None

        self.setWindowTitle("StickyPy - Gestione note")
        self.resize(380, 200)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("StickyPy tiene le tue note sempre sul desktop."))
        layout.addWidget(QLabel(f"Versione corrente: {get_current_version()}"))
        self.setCentralWidget(central)

        self._build_menu()

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")

        new_note_action = QAction("&Nuova nota", self)
        new_note_action.triggered.connect(self._new_note_callback)
        file_menu.addAction(new_note_action)

        self.autostart_action = QAction("Avvia con il PC", self)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(autostart.is_enabled())
        self.autostart_action.toggled.connect(self._on_autostart_toggled)
        file_menu.addAction(self.autostart_action)

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

    def _on_autostart_toggled(self, checked: bool) -> None:
        try:
            if checked:
                autostart.enable()
            else:
                autostart.disable()
        except OSError as exc:
            QMessageBox.warning(self, "Avvio automatico", f"Impossibile aggiornare l'avvio automatico:\n{exc}")

    def _show_about(self) -> None:
        version = get_current_version()
        QMessageBox.about(
            self,
            "Informazioni su StickyPy",
            f"<h3>StickyPy</h3>"
            f"<p>Versione: {version}</p>"
            f"<p>Autore: {APP_AUTHOR}</p>"
            "<p>Note adesive per il desktop, sempre a portata di mano.</p>",
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

    def closeEvent(self, event) -> None:  # noqa: N802 - override Qt
        event.ignore()
        self.hide()
