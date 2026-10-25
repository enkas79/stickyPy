"""Persistenza delle note su disco (JSON in AppData/config utente)."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from PyQt6.QtCore import QStandardPaths
from PyQt6.QtGui import QTextDocument

APP_NAME = "StickyPy"
NOTES_FILENAME = "notes.json"
COLOR_NAMES = ("yellow", "green", "pink", "purple", "blue", "gray", "charcoal")
DEFAULT_COLOR = "yellow"


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
    width: int = 300
    height: int = 320
    color: str = DEFAULT_COLOR
    is_open: bool = True  # nota aperta sul desktop (False = solo nell'elenco)
    modified: float = field(default_factory=time.time)


def html_to_plain(text: str) -> str:
    """Testo semplice di una nota (HTML Qt o testo legacy senza markup)."""
    document = QTextDocument()
    if "<html" in text.lower():
        document.setHtml(text)
    else:
        document.setPlainText(text)
    return document.toPlainText()


def is_empty(note: NoteData) -> bool:
    return not html_to_plain(note.text).strip() and "<img" not in note.text


def load_notes() -> list[NoteData]:
    path = get_notes_path()
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        known = {f.name for f in fields(NoteData)}
        notes = [NoteData(**{k: v for k, v in item.items() if k in known}) for item in raw]
        for note in notes:  # colori delle versioni precedenti (hex) -> giallo
            if note.color not in COLOR_NAMES:
                note.color = DEFAULT_COLOR
        return notes
    except (json.JSONDecodeError, OSError, TypeError, AttributeError):
        # File corrotto (es. scrittura interrotta da uno spegnimento improvviso):
        # lo mettiamo da parte invece di lasciarlo sovrascrivere e perdere i dati.
        backup_path = path.with_name(f"{path.stem}.corrotto-{int(time.time())}{path.suffix}")
        try:
            path.replace(backup_path)
        except OSError:
            pass
        return []


def save_notes(notes: list[NoteData]) -> None:
    """Scrittura atomica: evita di lasciare notes.json a metà se l'app
    viene interrotta bruscamente (es. spegnimento del PC) durante il salvataggio."""
    path = get_notes_path()
    payload = [asdict(note) for note in notes]
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp_path, path)
