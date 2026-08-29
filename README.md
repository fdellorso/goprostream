# GoPro Streaming Server

Bridge di streaming video tra **GoPro Hero 4 Black** e **OctoPrint**.

```
GoPro Hero 4 ──WiFi Direct──► OUYA (ARMv7l) ──HLS──► OctoPrint
                               │
                          Podman Containers
                          ├── goprostream (Python + FFmpeg)
                          └── nginx-rtmp (media server)
```

## Requisiti

- **GoPro Hero 4 Black** con WiFi attivo e batteria carica
- **OUYA** (ARMv7l, Tegra 3) o equivalente con Linux e Podman
- **Server** con OctoPrint 1.9.0+ (opzionale, per visualizzazione)

## Installazione

```bash
git clone https://github.com/fdellorso/goprostream.git
cd goprostream

# Setup (build container, verifica deps)
./scripts/setup.sh

# Configura
cp .env.example .env
nano .env

# Connetti WiFi alla GoPro
./scripts/wifi-connect.sh

# Avvia streaming
./scripts/start.sh
```

## Comandi

| Comando | Descrizione |
|---------|-------------|
| `./scripts/setup.sh` | Setup iniziale: build container, verifica deps |
| `./scripts/start.sh` | Avvia streaming: verifica GoPro, avvia container |
| `./scripts/stop.sh` | Ferma tutti i container |
| `./scripts/wifi-connect.sh` | Connette alla rete WiFi Direct della GoPro |
| `npx pyright` | Type check Python |

## Accesso

| Servizio | URL |
|----------|-----|
| Dashboard HTTP | `http://<ouya_ip>:8080/` |
| Dashboard HTTPS | `https://<ouya_ip>:8443/` |
| Stream HLS (HTTP) | `http://<ouya_ip>:8080/hls/gopro.m3u8` |
| Stream HLS (HTTPS) | `https://<ouya_ip>:8443/hls/gopro.m3u8` |
| Stream RTMP | `rtmp://<ouya_ip>:1935/live/gopro` |

## Struttura del Progetto

```
├── python/                 # Codice Python
│   ├── goprostream.py      # Bridge streaming UDP → RTMP
│   ├── goprophoto.py       # Scatto foto remoto
│   ├── Pipfile             # Dipendenze
│   └── pyrightconfig.json  # Type checker
├── docker/                 # Infrastruttura container
│   ├── docker-compose.yml  # Stack: nginx-rtmp + goprostream
│   ├── Dockerfile.python   # Immagine Python container
│   ├── nginx.conf          # Configurazione Nginx-RTMP
│   ├── nginx.conf.template # Template con env var
│   └── entrypoint.sh       # Script avvio con envsubst
├── player/                 # Player web offline
│   ├── dashboard.html      # Dashboard monitoraggio
│   ├── hlsjs.html          # Player hls.js
│   ├── videojs.html        # Player Video.js
│   ├── js/                 # Librerie JS locali
│   └── css/                # CSS locali
├── scripts/                # Script di gestione
│   ├── setup.sh            # Setup iniziale
│   ├── start.sh            # Avvio streaming
│   ├── stop.sh             # Ferma container
│   └── wifi-connect.sh     # Connessione WiFi GoPro
├── docs/                   # Documentazione
│   ├── architecture.md     # Architettura e topologia
│   ├── context.md          # Contesto e device
│   ├── setup-octoprint.md  # Guida setup OctoPrint
│   ├── references/         # API GoPro Hero 4 (archiviate)
│   ├── handoff/            # Handoff tecnici
│   └── plans/              # Piano di sviluppo
├── .pi/                    # Risorse pi-coding-agent
│   ├── skills/             # Skill: podman, python, ffmpeg
│   ├── extensions/         # Extension: python-lsp, commands
│   └── prompts/            # Template prompt
├── .env.example            # Template configurazione
└── AGENTS.md               # Contesto progetto per l'agente
```

## Architettura Container

```
Host (OUYA)
│
├── nginx-rtmp (container)   ← Rete bridge, porta 1935 + 8080
│
└── goprostream (container)  ← network_mode: host
    ├── Python 3.11 + FFmpeg
    ├── Connessione a GoPro (10.5.5.9)
    └── Push RTMP a localhost:1935
```

## OctoPrint

Per visualizzare lo stream nell'interfaccia OctoPrint:

1. Configura **Classic Webcam** (integrato da OctoPrint 1.9.0)
2. Imposta Stream URL: `http://<ouya_ip>:8080/hls/gopro.m3u8`

Vedi `docs/setup-octoprint.md` per dettagli.

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `GOPRO_IP` | `10.5.5.9` | IP della GoPro |
| `SERVER_NAME` | `ouya.fritz.box` | Dominio nginx |
| `NGINX_RTMP_PORT` | `1935` | Porta RTMP |
| `SSL_CERT_PATH` | `/etc/letsencrypt/live/ouya.fritz.box/fullchain.pem` | Path certificato SSL |
| `SSL_KEY_PATH` | `/etc/letsencrypt/live/ouya.fritz.box/privkey.pem` | Path chiave SSL |

Vedi `.env.example` per la configurazione completa.

## License

MIT
