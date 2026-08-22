---
name: python
description: Sviluppo e gestione del codice Python del progetto (goprostream.py, goprophoto.py). Include dependency management con Pipfile, linting con pyright, e l'uso della libreria goprocam per il controllo della GoPro Hero 4.
---

# Python Skill

Sviluppo Python per il progetto goprostream.

## Dipendenze

Il progetto usa `Pipfile` per la gestione delle dipendenze.

```bash
# Installa dipendenze
pipenv install

# Installa dev dependencies
pipenv install --dev

# Esegui script
pipenv run python goprostream.py
pipenv run python goprophoto.py
```

### Dipendenze principali

- `goprocam` - Libreria per controllo GoPro via WiFi

## Type Checking con Pyright

Pyright è installato come dev dependency nel progetto.

```bash
# Esegui pyright sul progetto
npx pyright

# Output dettagliato
npx pyright --outputjson

# Verifica un singolo file
npx pyright goprostream.py
```

### Configurazione

Il file `pyrightconfig.json` nella root del progetto configura pyright per:
- Python 3.8+ (compatibile con Pipfile)
- Strict type checking
- Include paths: `.` (root del progetto)

### Warning comuni

- `reportMissingImports` - Dipendenza mancante (eseguire `pipenv install`)
- `reportUntypedFunction` - Funzione senza type hints
- `reportAttributeAccessError` - Attributo non esistente su un oggetto
- `reportCallIssue` - Parametri mancanti o errati in una chiamata

## Struttura del codice

```
goprostream.py    # Streaming bridge (UDP → RTMP)
goprophoto.py     # Scatto foto e download
Pipfile           # Dipendenze
Pipfile.lock      # Lock file
```

## Libreria goprocam - Note per Hero4

```python
from goprocam import GoProCamera, constants

# Connessione automatica
gopro = GoProCamera.GoPro()

# Indirizzo IP (default 10.5.5.9)
gopro.ip_addr

# Streaming
gopro.livestream("start")  # Avvia UDP stream
gopro.KeepAlive()          # Mantiene attivo il WiFi (ogni ~10s)

# Controllo
gopro.mode(constants.Mode.VideoMode)  # Imposta modalità video
gopro.take_photo(3)                   # Scatta foto
gopro.shoot_video(10)                 # Registra 10 secondi

# Power
gopro.power_off()  # Spegni GoPro
```

## Riferimenti GoPro (archiviati localmente)

Quando serve consultare i comandi API della GoPro Hero4, usa i file in `docs/references/`:

| File | Quando consultarli |
|------|-------------------|
| `docs/references/hero4-commands.md` | Tutti i comandi WiFi (video, photo, settings, protune) |
| `docs/references/hero4-livestreaming.md` | Parametri streaming UDP, FFmpeg, bitrate |
| `docs/references/hero4-status.md` | Significato campi JSON status |
| `docs/references/gopro-py-api.md` | API della libreria goprocam |
| `docs/references/goprowifihack.md` | Indice repository e link correlati |

> **Non cercare online** — il contenuto è già archiviato e ottimizzato per il nostro device.

## Note ambientali

- La GoPro si trova sulla rete `10.5.5.x` (WiFi Direct)
- Pyright verifica il codice durante lo sviluppo
- Il progetto gira su ARMv7l (OUYA con Tegra 3)
