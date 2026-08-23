# GoPro Streaming - Ciclo di Vita e Architettura

> Documento generato dall'analisi del sistema
> Data: 2024

---

## 1. Architettura del Sistema

### Componenti

| Componente | Tipo | Ruolo |
|------------|------|-------|
| GoPro Hero 4 | Hardware | Sorgente video, manda flusso UDP |
| goprostream.py | Python (container) | Bridge UDP → RTMP |
| FFmpeg | Processo esterno | Convertitore video |
| Nginx-RTMP | Container | Server HLS/DASH |
| OctoPrint | Server (LXC) | Client, mostra video al browser |
| Dashboard | Web UI | Controllo remoto GoPro |

### Flusso dati (quando attivo)

```
GoPro ──UDP:8554──► FFmpeg ──RTMP:1935──► Nginx-RTMP ──HLS:8080──► OctoPrint/Browser
```

### Gerarchia processi

```
Container Python (goprostream)
│
├── Processo Principale (goprostream.py)
│   │
│   ├── Processo: KeepAlive (multiprocessing.Process)
│   │   └── Manda _GPHD_:0:0:2:0.000000\n ogni 2.5s alla GoPro
│   │
│   └── Processo: FFmpeg (subprocess.Popen)
│       └── Converte UDP → RTMP
│
└── Container Nginx-RTMP
    └── Nginx worker
        └── Genera segmenti HLS in /mnt/hls/
```

---

## 2. Stati del Sistema

### Stato A: DOPO accensione, PRIMA di restart stream

```
┌──────────┐      ┌──────────────┐      ┌──────────┐      ┌─────────────────┐
│  GOPRO   │      │ GOSTREAM.PY  │      │  FFMPEG  │      │   NGINX-RTMP    │
│  HERO4   │      │  (Python)    │      │          │      │                 │
└────┬─────┘      └──────┬───────┘      └────┬─────┘      └────────┬────────┘
     │                   │                   │                     │
     │   UDP:8554        │                   │                     │
     │   ════════════════╪═══════════════════╪═══════════════════ │
     │   NULLA!          │                   │   NULLA!            │
     │   La GoPro non    │                   │   FFmpeg non        │
     │   manda dati      │                   │   riceve nulla      │
     │                   │                   │                     │
     │   KeepAlive       │                   │                     │
     │ ◄─────────────────┼─┐                 │                     │
     │   _GPHD_...       │ │ Ogni 2.5s       │                     │
     │   (solo WiFi)     │ │                 │                     │
     │                   │ │                 │                     │
     │                   │ │                 │   RTMP:1935         │
     │                   │ │                 │   ══════════════════│═══
     │                   │ │                 │   NULLA!            │
     │                   │ │                 │                     │
     │                   │ │                 │   HLS:8080          │
     │                   │ │                 │   /mnt/hls/         │
     │                   │ │                 │   ══════════════════│═══
     │                   │ │                 │   VUOTA!            │
     │                   │ │                 │                     │
     │                   │ │                 │      ┌──────────────┴────────┐
     │                   │ │                 │      │                       │
     │                   │ │                 │      │   /hls/gopro.m3u8     │
     │                   │ │                 │      │   NON ESISTE o VUOTO  │
     │                   │ │                 │      │                       │
     │                   │ │                 │      └───────────┬───────────┘
     │                   │ │                 │                  │
     │                   │ │                 │                  ▼
     │                   │ │                 │      ┌─────────────────────────┐
     │                   │ │                 │      │      OCTOPRINT /        │
     │                   │ │                 │      │       BROWSER           │
     │                   │ │                 │      │                         │
     │                   │ │                 │      │  "Non ce collegamento   │
     │                   │ │                 │      │   con la gopro"         │
     │                   │ │                 │      └─────────────────────────┘
```

| Applicazione | Stato | Cosa sta facendo |
|--------------|-------|------------------|
| GoPro | 🟡 Accesa, WiFi OK | **NON sta mandando video UDP** (attesa comando) |
| KeepAlive | 🟢 Attivo | Manda `_GPHD_...` per mantenere WiFi vivo |
| FFmpeg | 🟡 Running | **In ascolto** su UDP:8554, non riceve nulla |
| Nginx-RTMP | 🟡 Running | **In ascolto** su RTMP:1935, non riceve nulla |
| /mnt/hls/ | 🔴 Vuota | Nessun segmento generato |
| OctoPrint | 🔴 Errore | "Non ce collegamento con la gopro" |

---

### Stato B: DOPO restart stream

```
┌──────────┐      ┌──────────────┐      ┌──────────┐      ┌─────────────────┐
│  GOPRO   │      │ GOSTREAM.PY  │      │  FFMPEG  │      │   NGINX-RTMP    │
│  HERO4   │      │  (Python)    │      │          │      │                 │
└────┬─────┘      └──────┬───────┘      └────┬─────┘      └────────┬────────┘
     │                   │                   │                     │
     │   UDP:8554        │                   │                     │
     │ ◄─────────────────┼───────────────────┤                     │
     │   Video stream    │                   │                     │
     │   (ORA MANDA!)    │                   │                     │
     │                   │                   │   RTMP:1935         │
     │                   │                   │ ───────────────────►│
     │                   │                   │   (ORA RICEVE!)     │
     │                   │                   │                     │
     │   KeepAlive       │                   │   HLS:8080          │
     │ ◄─────────────────┼─┐                 │   /mnt/hls/*.ts     │
     │   _GPHD_...       │ │                 │   (ORA GENERA!)     │
     │                   │ │                 │                     │
     │                   │ │                 │      ┌──────────────┴────────┐
     │                   │ │                 │      │                       │
     │                   │ │                 │      │   /hls/gopro.m3u8     │
     │                   │ │                 │      │   POPOLATO!           │
     │                   │ │                 │      │                       │
     │                   │ │                 │      └───────────┬───────────┘
     │                   │ │                 │                  │
     │                   │ │                 │                  ▼
     │                   │ │                 │      ┌─────────────────────────┐
     │                   │ │                 │      │      OCTOPRINT /        │
     │                   │ │                 │      │       BROWSER           │
     │                   │ │                 │      │                         │
     │                   │ │                 │      │  "Collegamento attivo"  │
     │                   │ │                 │      │  Video visibile! ✅     │
     │                   │ │                 │      └─────────────────────────┘
```

| Applicazione | Stato | Cosa sta facendo |
|--------------|-------|------------------|
| GoPro | 🟢 Streaming | **Manda video UDP** sulla porta 8554 |
| KeepAlive | 🟢 Attivo | Manda `_GPHD_...` ogni 2.5s |
| FFmpeg | 🟢 Riceve | Riceve UDP, converte, manda RTMP |
| Nginx-RTMP | 🟢 Genera | Riceve RTMP, genera segmenti HLS |
| /mnt/hls/ | 🟢 Popolata | Segmenti .ts e .m3u8 aggiornati |
| OctoPrint | 🟢 Funzionante | Video visibile nel player |

---

## 3. Sequenza Temporale

```
T0: Accensione GoPro
    └── WiFi connesso (10.5.5.9)
    └── Nessun flusso UDP attivo

T1: goprostream.py avvia
    └── Crea oggetto GoProCamera.GoPro()
    └── Avvia processo KeepAlive
    └── Avvia processo FFmpeg (in ascolto UDP:8554)
    └── FFmpeg non riceve nulla

T2: KeepAlive attivo
    └── Manda pacchetti UDP ogni 2.5s
    └── WiFi rimane vivo
    └── GoPro NON streamma (attesa comando)

T3: Utente accede alla Dashboard
    └── Apre tab "Commands"
    └── Vede pulsante "▶ Avvia Stream"

T4: Utente clicca "▶ Avvia Stream"
    └── Dashboard invia: /execute?p1=gpStream&a1=proto_v2&c1=restart
    └── Nginx fa proxy verso GoPro (10.5.5.9)
    └── GoPro riceve comando

T5: GoPro inizia a streammare
    └── Inizia a mandare pacchetti UDP sulla porta 8554
    └── Flusso video MPEG-TS

T6: FFmpeg riceve dati
    └── Decodifica MPEG-TS
    └── Ricodifica in FLV
    └── Invia a Nginx via RTMP (porta 1935)

T7: Nginx genera HLS
    └── Riceve flusso RTMP
    └── Genera segmenti .ts in /mnt/hls/
    └── Aggiorna playlist .m3u8

T8: OctoPrint/Browser legge lo stream
    └── Richiede /hls/gopro.m3u8
    └── Riceve segmenti .ts
    └── Video visibile! ✅
```

---

## 4. Il Problema Attuale

### Spreco di risorse (Stato A)

```
┌─────────────────────────────────────────────────────────────┐
│  TUTTI ATTIVI MA BLOCCATI IN ATTESA DEI DATI               │
│                                                             │
│  GoPro     : accesa, non streamma (attesa comando)          │
│  FFmpeg    : running, non riceve nulla (in ascolto)         │
│  Nginx     : running, non riceve nulla (in ascolto)         │
│  KeepAlive : attivo, mantiene WiFi vivo                     │
│                                                             │
│  CONSUMATORE: OctoPrint non vede nulla                      │
└─────────────────────────────────────────────────────────────┘
```

### Flusso di controllo manuale attuale

```
┌──────────────┐
│   UTENTE     │
│   (click)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  DASHBOARD   │────►│   GOPRO      │────►│   FFMPEG     │
│  /api/cmd    │     │  (restart)   │     │  (riceve)    │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  OCTOPRINT   │◄────│   NGINX      │
                     │  (guarda)    │     │  (genera)    │
                     └──────────────┘     └──────────────┘
```

---

## 5. Soluzioni Possibili (On-Demand Streaming)

### Obiettivo
Avviare lo streaming solo quando qualcuno lo richiede, non sempre.

### Opzione 1: Dashboard avvia lo stream quando aperta

```
Browser apre Dashboard
    │
    └── JavaScript: $(document).ready()
            │
            └── fetch('/execute?p1=gpStream&a1=proto_v2&c1=restart')
                    │
                    └── GoPro inizia a streammare
```

| Pro | Contro |
|-----|--------|
| ✅ Semplice | ❌ Stream parte anche se non guardi |
| ✅ Nessuna modifica backend | ❌ Non è truly on-demand |

---

### Opzione 2: OctoPrint avvia lo stream (webhook)

```
OctoPrint (Camera Settings)
    │
    └── "Avvia Webcam" → POST /api/stream/start
            │
            └── goprostream.py avvia FFmpeg + GoPro stream
```

| Pro | Contro |
|-----|--------|
| ✅ Integrato con OctoPrint | ❌ Richiede plugin OctoPrint |
| ✅ On-demand | ❌ Complesso |

---

### Opzione 3: Endpoint proxy in goprostream.py

```
OctoPrint URL: http://OUYA:8081/api/stream/proxy
    │
    └── GET /api/stream/proxy
            │
            ├── Stream attivo? → 302 Redirect a /hls/gopro.m3u8
            │
            └── Stream fermo? → Avvia GoPro + FFmpeg → Aspetta 3s → 302
```

| Pro | Contro |
|-----|--------|
| ✅ Truly on-demand | ❌ Aggiunge endpoint |
| ✅ Nessuna modifica OctoPrint | ❌ Delay al primo accesso |
| ✅ Logica centralizzata | |

---

### Opzione 4: Nginx on_play con script

```nginx
application live {
    live on;
    on_play http://127.0.0.1:8081/api/stream/notify;
    on_play_done http://127.0.0.1:8081/api/stream/stop;
}
```

| Pro | Contro |
|-----|--------|
| ✅ Nativ Nginx | ❌ on_play scatta DOPO l'avvio |
| ✅ Nessuna modifica Python | ❌ Non è preventivo |

---

### Opzione 5: goprostream.py monitora /stat di Nginx

```python
def _monitor_worker():
    while True:
        stat = requests.get("http://localhost:8080/stat")
        viewers = parse_viewers_count(stat)
        
        if viewers > 0 and not stream.is_active:
            stream.start_go_pro_stream()
        elif viewers == 0 and stream.is_active:
            stream.stop_go_pro_stream()
        
        time.sleep(10)
```

| Pro | Contro |
|-----|--------|
| ✅ Monitora traffico reale | ❌ Delay 10s |
| ✅ Logica in Python | ❌ Polling |

---

## 6. Riepilogo Stati

| Stato | GoPro | FFmpeg | Nginx | /mnt/hls/ | OctoPrint |
|-------|-------|--------|-------|-----------|-----------|
| A: After accensione | 🟡 Attessa | 🟡 Ascolto | 🟡 Ascolto | 🔴 Vuota | 🔴 Errore |
| B: After restart | 🟢 Streamma | 🟢 Converte | 🟢 Genera | 🟢 Popolata | 🟢 OK |
| C: On-demand (goal) | 🔴 Off | 🔴 Off | 🟡 Ascolto | 🔴 Vuota | 🟡 Attesa |

---

## 7. Note Tecniche

### Comando restart stream GoPro

```
HTTP GET: http://10.5.5.9/gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart
```

### KeepAlive packet

```
Payload: _GPHD_:0:0:2:0.000000\n
Dest: UDP 10.5.5.9:8554
Interval: 2.5 secondi (nativo libreria)
```

### Endpoint Nginx-RTMP

| Endpoint | Porta | Funzione |
|----------|-------|----------|
| RTMP | 1935 | Ingresso flusso da FFmpeg |
| HLS | 8080 | Output segmenti .ts/.m3u8 |
| DASH | 8080 | Output .mpd |
| Stat | 8080/stat | Statistiche stream attivi |

---

## 8. TODO

- [ ] Definire soluzione on-demand
- [ ] Implementare meccanismo di auto-restart stream
- [ ] Testare integrazione con OctoPrint
- [ ] Documentare flusso completo dopo implementazione
