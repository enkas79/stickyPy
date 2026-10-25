"""Impostazioni: tema e conferma prima di eliminare una nota."""
from __future__ import annotations

from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout

from src.core.settings import THEMES, AppSettings

THEME_LABELS = {"system": "Usa impostazioni di sistema", "light": "Chiaro", "dark": "Scuro"}


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Impostazioni")
        layout = QFormLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        self.theme_combo = QComboBox()
        for theme in THEMES:
            self.theme_combo.addItem(THEME_LABELS[theme], theme)
        self.theme_combo.setCurrentIndex(THEMES.index(settings.theme))
        self.confirm_check = QCheckBox("Conferma prima di eliminare")
        self.confirm_check.setChecked(settings.confirm_delete)
        layout.addRow("Tema", self.theme_combo)
        layout.addRow(self.confirm_check)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def apply_to(self, settings: AppSettings) -> None:
        settings.theme = self.theme_combo.currentData()
        settings.confirm_delete = self.confirm_check.isChecked()
