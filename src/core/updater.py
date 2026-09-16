"""Controllo aggiornamenti in background tramite GitHub Releases API."""
from __future__ import annotations

import sys
from pathlib import Path

import requests
from PyQt6.QtCore import QThread, pyqtSignal

GITHUB_REPO = "enkas79/stickypy"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_current_version() -> str:
    # In un eseguibile PyInstaller, version.txt viene copiato nella cartella
    # temporanea di estrazione (sys._MEIPASS) tramite --add-data.
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent.parent))
    version_file = base_dir / "version.txt"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"


def _version_tuple(version: str) -> tuple[int, ...]:
    cleaned = version.lstrip("vV")
    parts = []
    for part in cleaned.split("."):
        digits = "".join(c for c in part if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


class UpdateChecker(QThread):
    """Esegue la verifica di nuove release senza bloccare la GUI."""

    update_available = pyqtSignal(str, str, str)  # nuova_versione, url, changelog
    up_to_date = pyqtSignal()
    check_failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            response = requests.get(RELEASES_API, timeout=10)
            response.raise_for_status()
            data = response.json()
            latest_version = str(data.get("tag_name", "")).strip()
            current_version = get_current_version()
            if latest_version and _version_tuple(latest_version) > _version_tuple(current_version):
                url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
                changelog = data.get("body", "")
                self.update_available.emit(latest_version, url, changelog)
            else:
                self.up_to_date.emit()
        except requests.RequestException as exc:
            self.check_failed.emit(str(exc))
