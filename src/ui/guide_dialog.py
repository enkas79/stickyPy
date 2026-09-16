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
<li>Il pulsante <b>◐</b> cicla la trasparenza della nota.</li>
<li><b>Ctrl+rotellina</b> sul testo cambia la dimensione del carattere.</li>
<li>Scrivi <code>[ ] voce</code> per creare una voce di lista: un click sulla
casella la spunta in <code>[x] voce</code>. In alternativa, tasto destro su
una riga per <b>inserire</b> o <b>spuntare/togliere spunta</b> dal menu,
senza doverla selezionare.</li>
<li>Il pulsante <b>X</b> chiude la nota (il contenuto resta salvato).</li>
<li>Tutte le note vengono salvate automaticamente e ripristinate al riavvio.</li>
<li><b>Ctrl+N</b> crea una nuova nota da qualsiasi punto dell'app.</li>
<li>Dal menu <b>Aiuto</b> puoi controllare gli aggiornamenti disponibili.</li>
<li>Abilita l'<b>avvio automatico</b> dal menu File per far partire StickyPy con il PC.</li>
<li>Dalla finestra <b>Gestione note</b> vedi l'elenco di tutte le note aperte:
doppio click per portarne una in primo piano, oppure usa "Porta tutte in
primo piano" dal menu del tray.</li>
<li>Dal menu File puoi <b>esportare tutte le note in un file .txt</b> come backup.</li>
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
