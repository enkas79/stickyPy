"""Test del debounce di salvataggio di StickyPyApp."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

import src.main as main_mod


@pytest.fixture
def sticky(monkeypatch):
    app = QApplication.instance() or QApplication([])
    saved = []
    monkeypatch.setattr(main_mod, "save_notes", lambda notes: saved.append(len(notes)))
    monkeypatch.setattr(main_mod, "load_notes", list)
    monkeypatch.setattr(main_mod.autostart, "is_enabled", lambda: False)
    s = main_mod.StickyPyApp(app)
    s.saved = saved
    yield s
    s.tray_icon.hide()


def test_modifiche_ravvicinate_un_solo_salvataggio(sticky):
    sticky.create_new_note()
    sticky.saved.clear()
    note = next(iter(sticky.notes.values()))
    for _ in range(10):
        note.changed.emit()
    assert sticky.saved == []
    assert sticky._save_timer.isActive()
    sticky._save_timer.timeout.emit()
    assert sticky.saved == [1]
    assert not sticky._save_timer.isActive()


def test_quit_salva_modifiche_pendenti(sticky):
    sticky.create_new_note()
    sticky.saved.clear()
    next(iter(sticky.notes.values())).changed.emit()
    sticky.quit()
    assert sticky.saved == [1]
