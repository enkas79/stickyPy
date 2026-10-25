"""Test di updater: confronto versioni e UpdateChecker con requests mockato."""
import pytest

pytest.importorskip("PyQt6")

import requests

from src.core import updater
from src.core.updater import UpdateChecker, _version_tuple


@pytest.mark.parametrize(
    "a, b",
    [("v1.2.10", "1.2.9"), ("2.0.0", "1.99.99"), ("1.2.3", "1.2"), ("V1.0.1", "1.0.0")],
)
def test_version_tuple_ordine(a, b):
    assert _version_tuple(a) > _version_tuple(b)


def test_version_tuple_tollera_suffissi():
    assert _version_tuple("v1.2.3-beta") == (1, 2, 3)


class _Resp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def _run(monkeypatch, get, current="1.2.3"):
    monkeypatch.setattr(updater.requests, "get", get)
    monkeypatch.setattr(updater, "get_current_version", lambda: current)
    events = []
    checker = UpdateChecker()
    checker.update_available.connect(lambda *a: events.append(("update", *a)))
    checker.up_to_date.connect(lambda: events.append(("ok",)))
    checker.check_failed.connect(lambda m: events.append(("fail", m)))
    checker.run()  # sincrono: evita il thread nel test
    return events


def test_nuova_versione(monkeypatch):
    data = {"tag_name": "v1.3.0", "html_url": "http://x", "body": "novità"}
    assert _run(monkeypatch, lambda *a, **k: _Resp(data)) == [("update", "v1.3.0", "http://x", "novità")]


def test_gia_aggiornato(monkeypatch):
    assert _run(monkeypatch, lambda *a, **k: _Resp({"tag_name": "v1.2.3"})) == [("ok",)]


def test_tag_vuoto_non_segnala_aggiornamento(monkeypatch):
    assert _run(monkeypatch, lambda *a, **k: _Resp({})) == [("ok",)]


def test_errore_di_rete(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("offline")

    events = _run(monkeypatch, boom)
    assert events == [("fail", "offline")]
