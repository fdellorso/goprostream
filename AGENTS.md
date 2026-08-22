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
│   ├── setup-octoprint.md
│   ├── references/             # API GoPro Hero 4
│   ├── handoff/
│   └── plans/
├── .pi/                        # Risorse pi-coding-agent
│   ├── skills/
│   ├── extensions/
│   └── prompts/
├── .env.example                # Template configurazione
└── AGENTS.md                   # Questo file
```

### Riferimenti (Le Nostre Skill)

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
