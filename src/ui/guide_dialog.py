"""Finestra di guida all'uso dell'applicazione."""
from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

GUIDE_HTML = """
<h2>Guida rapida a StickyPy</h2>
<ul>
<li><b>+</b> (in alto a sinistra nella nota, o <b>Ctrl+N</b>): nuova nota.</li>
<li>Trascina la <b>barra superiore</b> per spostare la nota; l'angolo in basso a destra la ridimensiona.</li>
<li><b>&#8943;</b>: cambia colore (giallo, verde, rosa, viola, blu, grigio, antracite),
apre l'elenco note o elimina la nota (<b>Ctrl+D</b>).</li>
<li><b>&#10005;</b> (o <b>Ctrl+W</b>) chiude la nota: resta salvata nell'elenco. Una nota vuota chiusa viene eliminata.</li>
<li>Barra in basso: <b>grassetto</b> (Ctrl+B), <b>corsivo</b> (Ctrl+I), <b>sottolineato</b> (Ctrl+U),
<b>barrato</b> (Ctrl+T), <b>elenco puntato</b> (Ctrl+Maiusc+L), <b>immagine</b> (anche incollandola).</li>
<li><b>Elenco note</b> (clic sull'icona nella system tray): cerca, apri (doppio clic) o elimina (tasto destro).</li>
<li><b>Impostazioni</b> (ingranaggio): tema chiaro/scuro/di sistema e conferma prima di eliminare.</li>
<li>Le note aperte vengono ripristinate al riavvio; il salvataggio è automatico.</li>
<li>Abilita <b>Avvia con il PC</b> dal menu File o dal tray per l'avvio automatico all'accensione.</li>
<li>Dal menu <b>Aiuto</b> puoi controllare gli aggiornamenti.</li>
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
