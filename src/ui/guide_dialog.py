"""Finestra di guida all'uso dell'applicazione."""
from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

GUIDE_HTML = """
<h2>Guida rapida a StickyPy</h2>
<ul>
<li><b>Nuova nota</b>: crea un post-it dal menu File o dall'icona nella system tray.</li>
<li><b>Sposta</b> una nota trascinandola dalla sua barra superiore.</li>
<li><b>Ridimensiona</b> trascinando l'angolo in basso a destra.</li>
<li>Il pulsante <b>tavolozza</b> cambia il colore della nota.</li>
<li>Il pulsante <b>X</b> chiude la nota (il contenuto resta salvato).</li>
<li>Tutte le note vengono salvate automaticamente e ripristinate al riavvio.</li>
<li>Dal menu <b>Aiuto</b> puoi controllare gli aggiornamenti disponibili.</li>
<li>Abilita l'<b>avvio automatico</b> dal menu File per far partire StickyPy con il PC.</li>
</ul>
"""


class GuideDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guida - StickyPy")
        self.resize(420, 380)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setHtml(GUIDE_HTML)
        layout.addWidget(browser)
