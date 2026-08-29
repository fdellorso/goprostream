# OctoPrint Classic Webcam — Snapshot & Timelapse

> Documento tecnico su come Classic Webcam gestisce lo snapshot e il timelapse.

---

## Come funziona Classic Webcam

Classic Webcam è il plugin integrato in OctoPrint 1.9.0+ per gestire webcam.
Supporta tre tipi di sorgente:

| Tipo | URL | Uso |
|------|-----|-----|
| **Stream** | `http://...m3u8` | Video live nella sidebar |
| **Snapshot** | `http://...jpg` | Foto singola per timelapse |
| **WebRTC** | `webrtc://...` | Video live (bassa latenza) |

### Flusso dati Snapshot

```
OctoPrint Server (Python)
    │
    │  GET {snapshot_url}
    │
    ▼
Webcam Device (GoPro/OUYA)
    │
    │  Restituisce JPEG
    │
    ▼
OctoPrint Server
    │
    │  Salva su disk (cartella timelapse)
    │
    ▼
Dopo il print: FFmpeg unisce le JPEG → timelapse.mp4
```

### Sorgente Python (Classic Webcam)

```python
def take_webcam_snapshot(self, _):
    snapshot_url = self._get_snapshot_url()
    
    # Configura auth (basic/digest/bearer)
    # ...
    
    # Richiesta HTTP GET all'snapshot URL
    r = requests.get(snapshot_url, **params)
    r.raise_for_status()
    
    # Restituisce il contenuto (immagine JPEG)
    return r.iter_content(chunk_size=1024)
```

---

## Il problema con la GoPro

La GoPro Hero 4 **non** ha un endpoint HTTP che restituisce un frame JPEG dallo stream UDP.

### Endpoint GoPro disponibili

| Endpoint | Funzione | Restituisce |
|----------|----------|-------------|
| `/gp/gpControl/status` | Status camera | JSON |
| `/gp/gpControl/command/shutter?p=1` | Scatto foto | Salva su SD |
| `/gp/gpControl/execute?p1=gpStream...` | Start/stop stream | JSON |

**Nessuno** di questi restituisce un'immagine JPEG come risposta HTTP.

### Perché non funziona

1. La GoPro manda video UDP (porta 8554) — non HTTP
2. Il comando `shutter` salva la foto sulla SD card — non la restituisce via HTTP
3. Non esiste un endpoint `/snapshot` sulla GoPro

---

## Soluzioni possibili

### Opzione 1: Lasciare vuoto lo snapshot URL

**Pro:**
- Nessuna modifica necessaria
- Lo stream funziona comunque

**Contro:**
- Nessun timelapse
- Nessuna foto dalla dashboard

**Quando usarla:** Se non serve il timelapse.

### Opzione 2: Endpoint snapshot sull'OUYA

Creare un microservizio Python sull'OUYA che:

```
GET /snapshot
    │
    │  FFmpeg cattura 1 frame dallo stream UDP
    │  ffmpeg -i udp://10.5.5.9:8554 -vframes 1 -f image2 -
    │
    ▼
Restituisce JPEG
```

**Pro:**
- Timelapse funzionante
- Foto dalla dashboard

**Contro:**
- Richiede sviluppo
- Latenza (FFmpeg deve decodificare 1 frame)
- Complessità aggiuntiva

**Quando usarla:** Se serve il timelapse.

### Opzione 3: Foto dirette dalla GoPro

Usare l'API della GoPro per scattare foto e scaricarle via HTTP.

**Pro:**
- Qualità originale
- Nessun bisogno di FFmpeg

**Contro:**
- Foto salvate sulla SD card (non via HTTP)
- Richiede download separato
- Non è uno snapshot dallo stream live

**Quando usarla:** Per foto manuali, non per timelapse.

---

## Configurazione attuale

| Campo | Valore | Note |
|-------|--------|------|
| **Stream URL** | `http://ouya.fritz.box:8080/hls/gopro.m3u8` | ✅ Funzionante |
| **Snapshot URL** | *(vuoto)* | ⏸️ Non configurato |

### Note su HTTPS

Se OctoPrint è servito su HTTPS, lo snapshot URL deve essere HTTPS (mixed content blocking).

```
❌ http://ouya:8080/snapshot  (da pagina HTTPS)
✅ https://ouya:443/snapshot  (stesso protocollo)
```

---

## TODO futuri

- [ ] Valutare se serve il timelapse
- [ ] Se sì, implementare endpoint snapshot sull'OUYA
- [ ] Testare con FFmpeg per cattura frame
- [ ] Documentare la configurazione timelapse

---

## Riferimenti

- [Sorgente Classic Webcam](https://github.com/OctoPrint/OctoPrint/tree/dev/src/octoprint/plugins/classicwebcam)
- [OctoPrint Webcam Docs](https://docs.octoprint.org/en/master/features/webcam.html)
- [GoPro Hero 4 API](../docs/references/hero4-commands.md)
