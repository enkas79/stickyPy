"""Test per il modulo di persistenza delle note."""
from src.core.storage import NoteData, load_notes, save_notes


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("src.core.storage.get_data_dir", lambda: tmp_path)

    original = [NoteData(text="Comprare il latte", x=10, y=20, color="#A5D6A7")]
    save_notes(original)

    loaded = load_notes()
    assert len(loaded) == 1
    assert loaded[0].text == "Comprare il latte"
    assert loaded[0].x == 10
    assert loaded[0].color == "#A5D6A7"


def test_load_notes_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("src.core.storage.get_data_dir", lambda: tmp_path)
    assert load_notes() == []


def test_load_notes_corrupted_file_is_backed_up_not_lost(tmp_path, monkeypatch):
    monkeypatch.setattr("src.core.storage.get_data_dir", lambda: tmp_path)
    from src.core.storage import get_notes_path

    notes_path = get_notes_path()
    notes_path.write_text('{"non e\' json valido"', encoding="utf-8")

    assert load_notes() == []
    assert not notes_path.exists()  # spostato, non cancellato
    backups = list(tmp_path.glob("notes.corrotto-*.json"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == '{"non e\' json valido"'


def test_save_notes_does_not_leave_tmp_file(tmp_path, monkeypatch):
    monkeypatch.setattr("src.core.storage.get_data_dir", lambda: tmp_path)
    save_notes([NoteData(text="prova")])
    assert list(tmp_path.glob("*.tmp")) == []
