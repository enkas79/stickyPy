"""Persistenza delle note su disco (JSON in AppData/config utente)."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PyQt6.QtCore import QStandardPaths

APP_NAME = "StickyPy"
NOTES_FILENAME = "notes.json"


def get_data_dir() -> Path:
    """Restituisce (creandola se serve) la cartella dati dell'app."""
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    data_dir = Path(base) if base else Path.home() / f".{APP_NAME.lower()}"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_notes_path() -> Path:
    return get_data_dir() / NOTES_FILENAME


@dataclass
class NoteData:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    x: int = 100
    y: int = 100
    width: int = 220
    height: int = 220
    color: str = "#FFF59D"
    title: str = "StickyPy"
    opacity: float = 1.0
    font_size: int = 13


def load_notes() -> list[NoteData]:
    path = get_notes_path()
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [NoteData(**item) for item in raw]


def save_notes(notes: list[NoteData]) -> None:
    path = get_notes_path()
    payload = [asdict(note) for note in notes]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
