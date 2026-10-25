"""Impostazioni utente persistenti (tema e conferma eliminazione)."""
from __future__ import annotations

from PyQt6.QtCore import QSettings

THEMES = ("system", "light", "dark")


class AppSettings:
    def __init__(self) -> None:
        self._qs = QSettings("StickyPy", "StickyPy")

    @property
    def theme(self) -> str:
        value = str(self._qs.value("theme", "system"))
        return value if value in THEMES else "system"

    @theme.setter
    def theme(self, value: str) -> None:
        self._qs.setValue("theme", value if value in THEMES else "system")

    @property
    def confirm_delete(self) -> bool:
        return str(self._qs.value("confirm_delete", "true")).lower() == "true"

    @confirm_delete.setter
    def confirm_delete(self, value: bool) -> None:
        self._qs.setValue("confirm_delete", "true" if value else "false")
