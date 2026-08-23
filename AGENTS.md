# GoPro Streaming Server

## Project Overview

Questo progetto è un **bridge di streaming video** tra una GoPro Hero 4 Black e OctoPrint.

### Componenti Principali

| File | Ruolo |
|------|-------|
| `python/goprostream.py` | Bridge streaming: riceve UDP dalla GoPro, converte in RTMP verso Nginx |
| `python/goprophoto.py` | Scatto foto remoto e download dalla GoPro |
| `python/gopro_api.py` | API server (bottle) per dashboard — ATTUALMENTE NON USATO, proxy diretto nginx |
| `docker/docker-compose.yml` | Stack Podman: nginx-rtmp + goprostream |
| `docker/nginx.conf` | Configurazione Nginx-RTMP (porta 1935 RTMP, 8080 HTTP) |
| `docker/Dockerfile.python` | Immagine Python con FFmpeg |
| `player/` | Player web offline (hls.js, video.js, dashboard) |

### Hardware

- **GoPro Hero 4 Black** — Crea rete WiFi Direct (`10.5.5.9`), flusso UDP su porta `8554`
- **OUYA (ARMv7l, Tegra 3)** — Si collega alla GoPro, esegue FFmpeg + Nginx-RTMP
- **Proxmox LXC** — Server OctoPrint, legge lo stream HLS dalla porta 8080 dell'OUYA

### Network

```
GoPro ←WiFi Direct→ OUYA ←HTTP HLS→ OctoPrint (LXC su Proxmox)

Browser → nginx (/api/) → GoPro (10.5.5.9) [proxy diretto]
```

### Comandi Utili

```bash
# Setup iniziale
./scripts/setup.sh

# Connetti WiFi GoPro
./scripts/wifi-connect.sh

# Avvia streaming
./scripts/start.sh

# Ferma streaming
./scripts/stop.sh

# Verifica status
podman-compose -f docker/docker-compose.yml ps
curl -s http://localhost:8080/hls/gopro.m3u8

# Type check Python
npx pyright

# Test API GoPro
curl http://localhost:8080/api/status
curl http://localhost:8080/api/cmd/command/system/locate?p=1
```

### Comandi Pi (custom)

| Comando | Descrizione |
|---------|-------------|
| `/status` | Stato Git, Podman, FFmpeg, GoPro, Pyright |
| `/debug` | Diagnostica completa con emoji (GoPro, FFmpeg, Container, RTMP, HLS, Pyright) |
| `/stream` | Avvia stack streaming (podman-compose up -d) |
| `/commit <tipo>: <desc>` | Git commit con formato strutturato |
| `/handoff [note]` | Genera snapshot sessione in docs/handoff/ |
| `python_typecheck` | Tool: esegue pyright su tutto o un file specifico |

### Regole operative

- **Verifica GoPro attiva**: `curl -s http://10.5.5.9/gp/gpControl/status` (NON usare ping)
- **Comandi sudo**: Chiedere all'utente di eseguire e incollare l'output
- **Skills**: Non mischiare contenuti tra skill diverse

### TODO

- [x] Aggiungere comando per avviare streaming UDP: `/execute?p1=gpStream&a1=proto_v2&c1=restart`
- [ ] **BUG**: Container goprostream va in crash dopo un po' — da investigare
  - Sintomi: FFmpeg si ferma, logs mostrano attività fino all'ultimo avvio
  - Workaround: `podman-compose restart goprostream`
  - Causa probabile: FFmpeg crash o GoPro chiude la connessione UDP

### Struttura

```
├── python/                     # Codice Python
│   ├── goprostream.py          # Bridge streaming
│   ├── goprophoto.py           # Scatto foto
│   ├── Pipfile                 # Dipendenze
│   └── pyrightconfig.json      # Type checker
├── docker/                     # Infrastruttura container
│   ├── docker-compose.yml      # Stack Podman
│   ├── Dockerfile.python       # Immagine Python
│   └── nginx.conf              # Configurazione Nginx
├── player/                     # Player web offline
│   ├── dashboard.html          # Dashboard monitoraggio
│   ├── hlsjs.html              # Player hls.js
│   ├── videojs.html            # Player Video.js
│   ├── js/                     # Librerie JS locali
│   └── css/                    # CSS locali
├── scripts/                    # Script di gestione
│   ├── setup.sh                # Setup iniziale
│   ├── start.sh                # Avvio streaming
│   ├── stop.sh                 # Ferma container
│   └── wifi-connect.sh         # Connessione WiFi GoPro
├── docs/                       # Documentazione
│   ├── architecture.md
│   ├── context.md
│   ├── streaming-lifecycle.md   # Ciclo vita streaming (stati, flussi, soluzioni)
│   ├── setup-octoprint.md
│   ├── references/             # API GoPro Hero 4
│   ├── handoff/
│   └── plans/
├── .pi/                        # Risorse pi-coding-agent
│   ├── skills/                 # ffmpeg-streaming, podman, python
│   ├── extensions/             # project-commands.ts, python-lsp.ts
│   ├── prompts/                # debug-stream, new-feature, review-stream
│   └── settings.json
├── .env.example                # Template configurazione
└── AGENTS.md                   # Questo file
```

### Documentazione

| File | Contenuto |
|------|----------|
| `docs/architecture.md` | Architettura completa del sistema, scelte architetturali, sicurezza |
| `docs/streaming-lifecycle.md` | Ciclo di vita streaming: stati, sequenza temporale, soluzioni on-demand |
| `docs/setup-octoprint.md` | Setup OctoPrint con Classic Webcam |
| `docs/handoff/` | Snapshot delle sessioni di sviluppo |

### Riferimenti GoPro (Le Nostre Skill)

La cartella `docs/references/` contiene la documentazione GoPro Hero 4 archiviata localmente.
**Consultare PRIMA questi file** prima di cercare online.

| File | Contenuto |
|------|----------|
| `docs/references/hero4-commands.md` | TUTTI i comandi WiFi (video, photo, protune, sistema) |
| `docs/references/hero4-livestreaming.md` | Streaming UDP, FFmpeg, bitrate |
| `docs/references/hero4-status.md` | Campi JSON status |
| `docs/references/gopro-py-api.md` | Libreria goprocam |
| `docs/references/hero4-pairing.md` | **Pairing senza app** (fondamentale!) |
| `docs/references/goprowifihack.md` | Indice repository |

### Note Sviluppo

- Pyright è configurato per Python 3.11+ con type checking standard
- Il progetto gira su ARMv7l (OUYA) — attenzione a dipendenze native
- Podman-compose per i container (rootless, compatibile)
- OctoPrint usa Classic Webcam (non Iframe) per visualizzare lo stream HLS
- Il container Python usa `network_mode: host` per raggiungere la GoPro

### Streaming Lifecycle

Lo streaming UDP parte solo quando l'utente lo richiede dalla dashboard (pulsante "Avvia Stream").
Prima di quel comando, FFmpeg è in ascolto ma non riceve nulla dalla GoPro.

- **Stato A (after accensione)**: GoPro accesa, FFmpeg in ascolto, nessun flusso UDP
- **Stato B (after restart)**: GoPro streamma, FFmpeg converte, Nginx genera HLS
- **Soluzione on-demand**: Documentata in `docs/streaming-lifecycle.md`

### Dashboard

La dashboard (`player/dashboard.html`) è la UI principale per:
- Monitorare lo stato dello stream (HLS, RTMP, GoPro WiFi)
- Controllare la GoPro (tutti i comandi WiFi)
- Avviare/fermare lo streaming

Le pagine player (`videojs.html`, `hlsjs.html`) hanno header armonizzata con la dashboard.
Il check HLS usa `xhr.status === 200` per verificare lo stato reale dello stream.
