# StickyPy

Note adesive per il desktop, scritte in Python con PyQt6.

## Avvio
```
pip install -r requirements.txt
python src/main.py
```

## Test
```
pip install -r requirements-dev.txt
pytest
```

## Funzionalità
Clone di Microsoft Sticky Notes:
- Note frameless con barra superiore trascinabile, `+` per nuova nota, menu `⋯` (colori, elenco, elimina), chiusura.
- 7 colori (giallo, verde, rosa, viola, blu, grigio, antracite) e tema chiaro/scuro/sistema.
- Formattazione: grassetto, corsivo, sottolineato, barrato, elenco puntato, immagini (barra in basso e scorciatoie).
- Elenco note con ricerca, apertura ed eliminazione (con conferma opzionale); le note vuote chiuse vengono eliminate.
- Note aperte ripristinate al riavvio, salvataggio automatico.
- Icona nella system tray, avvio automatico con il sistema operativo (Windows/Linux/macOS).
- Controllo aggiornamenti da GitHub Releases, esportazione in .txt.

Non incluso: sincronizzazione con account Microsoft e "Insights" (link/date intelligenti).

## Build installer
Il workflow `.github/workflows/build-installers.yml` si attiva a ogni modifica di
`version.txt` su `main` e pubblica una GitHub Release con:
- `StickyPy-Setup-<versione>.exe` (Windows, via NSIS)
- `StickyPy-<versione>.dmg` (macOS)
- `stickypy_<versione>_amd64.deb` (Linux)
