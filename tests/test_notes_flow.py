"""Flusso note in stile Sticky Notes: chiusura, eliminazione, formattazione."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QMessageBox

import src.main as main_mod


@pytest.fixture
def sticky(monkeypatch):
    app = QApplication.instance() or QApplication([])
    saved = []
    monkeypatch.setattr(main_mod, "save_notes", lambda notes: saved.append([n.id for n in notes]))
    monkeypatch.setattr(main_mod, "load_notes", list)
    monkeypatch.setattr(main_mod.autostart, "is_enabled", lambda: False)
    s = main_mod.StickyPyApp(app)
    s.settings.confirm_delete = False
    s.saved = saved
    yield s
    s.tray_icon.hide()
    for note in list(s.notes.values()):
        note.close()


def test_chiudere_nota_vuota_la_elimina(sticky):
    sticky.create_new_note()
    note = next(iter(sticky.notes.values()))
    note.close()
    assert sticky.all_data == {} and sticky.notes == {}


def test_chiudere_nota_con_testo_la_tiene_nell_elenco(sticky):
    sticky.create_new_note()
    note = next(iter(sticky.notes.values()))
    note.text_edit.setPlainText("da ricordare")
    note.close()
    assert sticky.notes == {}
    (data,) = sticky.all_data.values()
    assert data.is_open is False
    sticky.open_note(data.id)
    assert data.id in sticky.notes and data.is_open


def test_elimina_nota_con_conferma(sticky, monkeypatch):
    sticky.create_new_note()
    note = next(iter(sticky.notes.values()))
    note.text_edit.setPlainText("x")
    sticky.settings.confirm_delete = True
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No)
    sticky.delete_note(note.data.id)
    assert note.data.id in sticky.all_data
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    sticky.delete_note(note.data.id)
    assert sticky.all_data == {} and sticky.notes == {}


def test_formattazione_e_elenco_puntato(sticky):
    sticky.create_new_note()
    note = next(iter(sticky.notes.values()))
    note.text_edit.setPlainText("riga")
    note.text_edit.selectAll()
    note.toggle_bold()
    note.toggle_strike()
    note.toggle_bullets()
    html = note.text_edit.toHtml()
    assert "font-weight" in html and "line-through" in html and "<ul" in html
    note.toggle_bullets()
    assert "<ul" not in note.text_edit.toHtml()


def test_colore_e_immagine(sticky):
    from PyQt6.QtGui import QImage

    sticky.create_new_note()
    note = next(iter(sticky.notes.values()))
    note.set_color("charcoal")
    assert note.data.color == "charcoal"
    note.text_edit.insert_image(QImage(40, 40, QImage.Format.Format_RGB32))
    assert "<img" in note.text_edit.toHtml()
    assert "<img" in note.data.text


def test_bordi_di_resize(sticky):
    from PyQt6.QtCore import QPoint, Qt

    sticky.create_new_note()
    note = next(iter(sticky.notes.values()))
    assert note._edges_at(QPoint(1, 100)) == Qt.Edge.LeftEdge
    assert note._edges_at(QPoint(note.width() - 1, note.height() - 1)) == Qt.Edge.RightEdge | Qt.Edge.BottomEdge
    assert not note._edges_at(QPoint(note.width() // 2, note.height() // 2))
