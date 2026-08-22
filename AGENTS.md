# GoPro Streaming Server

## Project Overview

Questo progetto è un **bridge di streaming video** tra una GoPro Hero 4 Black e OctoPrint.

### Componenti Principali

| File | Ruolo |
|------|-------|
| `goprostream.py` | Bridge streaming: riceve UDP dalla GoPro, converte in RTMP verso Nginx |
| `goprophoto.py` | Scatto foto remoto e download dalla GoPro |
| `docker-compose.yml` | Stack Podman: nginx-rtmp per generare HLS |
| `nginx.conf` | Configurazione Nginx-RTMP (porta 1935 RTMP, 8080 HTTP) |
| `hlsjs.html` | Player web con hls.js |
| `videojs.html` | Player web con Video.js |

### Hardware

- **GoPro Hero 4 Black** — Crea rete WiFi Direct (`10.5.5.9`), flusso UDP su porta `8554`
- **OUYA (ARMv7l, Tegra 3)** — Si collega alla GoPro, esegue FFmpeg + Nginx-RTMP
- **Proxmox LXC** — Server OctoPrint, legge lo stream HLS dalla porta 8080 dell'OUYA

### Network

```
GoPro ←WiFi Direct→ OUYA ←HTTP HLS→ OctoPrint (LXC su Proxmox)
```

### Comandi Utili

```bash
# Avvia stack streaming
podman-compose up -d

# Esegui streaming (dopo che podman-compose è attivo)
pipenv run python goprostream.py

# Type check Python
npx pyright

# Verifica status
podman-compose ps
curl -s http://localhost:8080/hls/gopro.m3u8
```

### Dipendenze Python

- `goprocam` — Libreria controllo GoPro via WiFi
- Sistema: `ffmpeg` (già installato)

### Container

- `nginx-rtmp` — Media server (image: `vallahaye/nginx-rtmp:stable-alpine`)
- Porte: `1935` (RTMP), `8080` (HTTP/HLS)

### Riferimenti (Le Nostre Skill)

La cartella `docs/references/` contiene la documentazione GoPro Hero 4 archiviata localmente.
**Consultare PRIMA questi file** prima di cercare online.

| File | Contenuto |
|------|----------|
| `hero4-commands.md` | TUTTI i comandi WiFi (video, photo, protune, sistema) |
| `hero4-livestreaming.md` | Streaming UDP, FFmpeg, bitrate |
| `hero4-status.md` | Campi JSON status |
| `gopro-py-api.md` | Libreria goprocam |
| `goprowifihack.md` | Indice repository |

### Altra Documentazione

- `docs/architecture.md` — Architettura completa e topologia di rete
- `docs/context.md` — Contesto progetto e device

### Note Sviluppo

- Pyright è configurato per Python 3.8+ con type checking standard
- Il progetto gira su ARMv7l (OUYA) — attenzione a dipendenze native
- Podman-compose al posto di docker-compose (rootless, compatibile)
- OctoPrint usa Classic Webcam (non Iframe) per visualizzare lo stream HLS
