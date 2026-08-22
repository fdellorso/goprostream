# GoPro Python API (goprocam) — Riferimento Completo

> **Source**: https://github.com/KonradIT/gopro-py-api
> **PyPI**: https://pypi.org/project/goprocam/
> **Autore**: Konrad Iturbe (@KonradIT)
> **Python**: 3.6+ (testato)
> **Platform**: Linux, Windows, Mac

## Descrizione

Libreria Python per controllare le telecamere GoPro via WiFi. Fornisce un'astrazione ad alto livello sopra le API HTTP gpControl. Copre Hero3 fino a Hero10. È la libreria che usiamo nel nostro progetto.

## Installazione

```bash
# Da PyPI (consigliato)
pip install goprocam

# Da git (instabile)
git clone https://github.com/KonradIT/gopro-py-api
cd gopro-py-api
python setup.py install
```

## Compatibilità

| Modello | Supporto | Modalità |
|---------|----------|----------|
| HERO3 / HERO3+ | ✅ | WiFi |
| HERO4 (Black/Silver/Session) | ✅ | WiFi — **La nostra** |
| HERO+ / HERO+ LCD | ✅ | WiFi |
| HERO5 (Black/Session) | ✅ | WiFi |
| HERO6 Black | ✅ | WiFi |
| HERO7 (Black/Silver/White) | ✅ | WiFi |
| Fusion 1 | ✅ | WiFi |
| MAX | ✅ | WiFi |
| HERO8 Black | ✅ | WiFi |
| HERO9 Black | ✅ | WiFi (limitato, richiede firmware vecchio per foto) |
| HERO10 Black | ✅ | WiFi + USB Ethernet (OpenGoPro v2) |

## Connessione

```python
from goprocam import GoProCamera, constants

# Connessione automatica (cerca su 10.5.5.9)
gopro = GoProCamera.GoPro()

# Connessione a IP specifico
gopro = GoProCamera.GoPro("10.5.5.9")
```

### Credenziali WiFi Default

| Parametro | Valore |
|-----------|--------|
| SSID | `GOPRO-BP-XXXX` (variabile) |
| Password | `goprohero` |
| IP Gateway | `10.5.5.9` |
| Subnet | `255.255.255.0` |

## API Complete

### Proprietà

```python
gopro.ip_addr          # IP della GoPro (default: 10.5.5.9)
gopro.model            # Modello rilevato
gopro.firmware_version # Versione firmware
```

### Controllo Scatto

```python
# Foto
gopro.take_photo(3)        # Scatta foto, attende 3 secondi

# Video
gopro.shoot_video(10)      # Registra 10 secondi

# Stop
gopro.stop住()             # Ferma registrazione/scatto
```

### Controllo Modalità

```python
# Imposta modalità primaria
gopro.mode(constants.Mode.VideoMode)
gopro.mode(constants.Mode.PhotoMode)
gopro.mode(constants.Mode.MultiShotMode)

# Imposta sottomodalità
gopro.mode(constants.Mode.VideoMode, constants.Mode.SubMode.Video.Video)
gopro.mode(constants.Mode.PhotoMode, constants.Mode.SubMode.Photo.Single)
gopro.mode(constants.Mode.MultiShotMode, constants.Mode.SubMode.MultiShot.Burst)
```

### Controllo Impostazioni

```python
# Leggi impostazione
status = gopro.readSettings()
settings = gopro.read_status()

# Imposta impostazione generica
gopro.gpControlSet(setting_id, value)

# Imposta risoluzione video
gopro.gpControlSet(constants.Video.RESOLUTION, constants.Video.Resolution.R720)

# Imposta frame rate
gopro.gpControlSet(constants.Video.FRAME_RATE, constants.Video.FrameRate.F60)

# Imposta FOV
gopro.gpControlSet(constants.Video.FOV, constants.Video.FOV.Wide)
```

### Streaming

```python
# Avvia streaming
gopro.livestream("start")

# Ferma streaming
gopro.livestream("stop")

# KeepAlive (obbligatorio ogni ~10 secondi per mantenere attivo il WiFi)
gopro.KeepAlive()
```

### Media

```python
# Scarica ultimo media
gopro.downloadLastMedia(gopro.take_photo(0))

# Scarica media specifico
gopro.downloadMedia("100GOPRO/GOPR0001.JPG")

# Lista media
media_list = gopro.getMediaList()
```

### Sistema

```python
# Spegni
gopro.power_off()

# Accendi (solo via WoL, non diretto)
# Usa gopro-ble-py per accensione via Bluetooth

# Locate (fa lampeggiare le LED)
gopro.locate("on")
gopro.locate("off")
```

## Struttura Pacchetto

```
goprocam/
├── GoProCamera.py    # Classe principale GoPro()
├── constants.py      # Costanti per tutti i valori
└── __init__.py
```

## Note per HERO4

- La HERO4 usa il protocollo **gpControl** (non OpenGoPro)
- Per lo streaming: `http://10.5.5.9/gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart`
- Il flusso UDP è disponibile su `udp://10.5.5.9:8554`
- Il file `constants.py` contiene tutte le costanti per Video, Photo, MultiShot settings
- Per la lista completa delle costanti, consultare il source code su GitHub

## BLE (Bluetooth)

Per accendere la GoPro da stato di sleep profondo:

```python
from goproble import GoProBLE

# Accensione via Bluetooth
ble = GoProBLE()
ble.power_on()
```

## Nota su USB (Hero9+)

Hero9 Black e Hero10 Black supportano anche USB Ethernet con API completa. Questo non si applica alla nostra Hero4.
