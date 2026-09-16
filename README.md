# StickyPy

Note adesive per il desktop, scritte in Python con PyQt6.

## Avvio
```
pip install -r requirements.txt
python src/main.py
```

## Test
```
pytest
```

## Funzionalità
- Post-it flottanti, trascinabili (maniglia dedicata), ridimensionabili e colorabili.
- Titolo modificabile per nota (utile per raggruppare macro-argomenti).
- Trasparenza regolabile e dimensione del testo (Ctrl+rotellina).
- Voci di lista `[ ]`/`[x]` spuntabili con un click.
- Ctrl+N per una nuova nota da qualsiasi punto dell'app.
- Finestra "Gestione note" con elenco delle note aperte (doppio click per portarle in primo piano).
- "Porta tutte in primo piano" dal menu del tray.
- Esportazione di tutte le note in un file .txt di backup.
- Salvataggio automatico di posizione, dimensione e contenuto.
- Icona nella system tray per creare note e accedere alla gestione.
- Avvio automatico con il sistema operativo (Windows/Linux/macOS).
- Controllo aggiornamenti da GitHub Releases.

## Build installer
Il workflow `.github/workflows/build-installers.yml` si attiva a ogni modifica di
`version.txt` su `main` e pubblica una GitHub Release con:
- `StickyPy-Setup-<versione>.exe` (Windows, via NSIS)
- `StickyPy-<versione>.dmg` (macOS)
- `stickypy_<versione>_amd64.deb` (Linux)
