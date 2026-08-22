# GoPro Streaming Server

Bridge di streaming video tra **GoPro Hero 4 Black** e **OctoPrint**.

## Architettura

```
GoPro Hero 4 ──WiFi Direct──► OUYA (ARMv7l) ──HLS──► OctoPrint
                               │
                          FFmpeg + Nginx-RTMP
                          (Podman Container)
```

La GoPro crea una rete WiFi Direct. L'OUYA si collega, cattura il flusso UDP e lo converte in HLS tramite FFmpeg e Nginx-RTMP. OctoPrint visualizza lo stream nell'interfaccia web tramite il plugin Classic Webcam.

## Requisiti

- **GoPro Hero 4 Black** con WiFi attivo
- **OUYA** (ARMv7l) con:
  - Python 3.8+ e pipenv
  - FFmpeg
  - Podman + podman-compose
  - Node.js (per pyright, type checking)
- **Proxmox LXC** con OctoPrint 1.9.0+

## Setup

### 1. Installa dipendenze Python

```bash
pipenv install
```

### 2. Avvia il media server

```bash
podman-compose up -d
```

### 3. Avvia lo streaming

```bash
pipenv run python goprostream.py
```

### 4. Visualizza in OctoPrint

Configura il plugin **Classic Webcam** con URL:
```
http://<ouya_ip>:8080/hls/gopro.m3u8
```

## Struttura del Progetto

```
├── goprostream.py          # Bridge streaming UDP → RTMP
├── goprophoto.py           # Scatto foto remoto
├── docker-compose.yml      # Stack Podman (nginx-rtmp)
├── nginx.conf              # Configurazione Nginx-RTMP
├── Pipfile / Pipfile.lock  # Dipendenze Python
├── pyrightconfig.json      # Configurazione type checker
├── hlsjs.html              # Player HLS (hls.js)
├── videojs.html            # Player HLS (Video.js)
├── AGENTS.md               # Contesto progetto per l'agente
├── .pi/                    # Risorse locali al progetto
│   ├── settings.json
│   ├── skills/             # Skill: podman, python, ffmpeg-streaming
│   └── extensions/         # Extension: python-lsp
└── docs/
    ├── architecture.md     # Architettura e topologia di rete
    ├── context.md          # Contesto e device
    ├── references/         # API GoPro Hero 4
    ├── handoff/            # Handoff tecnici
    ├── plans/              # Roadmap
    └── archive/            # Backup storico codice originale
```

## Comandi Utili

| Comando | Descrizione |
|---------|-------------|
| `podman-compose up -d` | Avvia nginx-rtmp |
| `podman-compose down` | Ferma nginx-rtmp |
| `podman-compose logs -f` | Log container |
| `pipenv run python goprostream.py` | Avvia streaming |
| `pipenv run python goprophoto.py` | Scatta foto |
| `npx pyright` | Type check Python |

## Documentazione

- [Architettura](docs/architecture.md) — Componenti e flussi dati
- [Contesto](docs/context.md) — Device, rete, stack tecnologico
- [Riferimenti GoPro](docs/references/) — API WiFi HERO4
