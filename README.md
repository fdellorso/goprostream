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

### Hardware

- **GoPro Hero 4 Black** con WiFi attivo e batteria carica
- **OUYA** (ARMv7l, Tegra 3) o equivalente con:
  - Linux (Debian/Ubuntu consigliato)
  - Podman + podman-compose
  - Connessione WiFi (per collegarsi alla GoPro)
- **Server** con OctoPrint 1.9.0+ (opzionale, per visualizzazione)

### Software (installati automaticamente da `setup.sh`)

- Python 3.11+ (nel container)
- FFmpeg (nel container)
- Node.js + npm (solo per pyright, development)

## Installazione

```bash
# 1. Clone del repo
git clone https://github.com/fdellorso/goprostream.git
cd goprostream

# 2. Setup (build container, installa deps)
./setup.sh

# 3. Configura
cp .env.example .env
nano .env  # Modifica IP GoPro, SSID, ecc.

# 4. Connetti WiFi alla GoPro
./wifi-connect.sh

# 5. Avvia streaming
./start.sh
```

## Comandi

| Comando | Descrizione |
|---------|-------------|
| `./setup.sh` | Setup iniziale: build container, verifica deps |
| `./start.sh` | Avvia streaming: verifica GoPro, avvia container |
| `./stop.sh` | Ferma tutti i container |
| `./wifi-connect.sh` | Connette alla rete WiFi Direct della GoPro |
| `podman-compose ps` | Stato container |
| `podman-compose logs -f` | Log container |

## Accesso

| Servizio | URL |
|----------|-----|
| Player web | `http://<ouya_ip>:8080/` |
| Stream HLS | `http://<ouya_ip>:8080/hls/gopro.m3u8` |
| Stream RTMP | `rtmp://<ouya_ip>:1935/live/gopro` |

## Configurazione (.env)

```bash
GOPRO_IP=10.5.5.9        # IP della GoPro
GOPRO_SSID=GOPRO-BP-FD   # SSID WiFi Direct
GOPRO_PASS=goprohero      # Password WiFi
RTMP_URL=rtmp://localhost:1935/live/gopro
HLS_PORT=8080
RTMP_PORT=1935
```

## Struttura del Progetto

```
├── goprostream.py              # Bridge streaming UDP → RTMP
├── goprophoto.py               # Scatto foto remoto
├── Dockerfile.python           # Immagine Python container
├── docker-compose.yml          # Stack: nginx-rtmp + goprostream
├── nginx.conf                  # Configurazione Nginx-RTMP
├── setup.sh                    # Setup iniziale
├── start.sh                    # Avvio streaming
├── stop.sh                     # Ferma container
├── wifi-connect.sh             # Connessione WiFi GoPro
├── Pipfile / Pipfile.lock      # Dipendenze Python
├── pyrightconfig.json          # Configurazione type checker
├── .env.example                # Template configurazione
├── player/                     # Player web (offline, no CDN)
│   ├── hlsjs.html              # Player con hls.js
│   ├── videojs.html            # Player con Video.js
│   ├── js/                     # Librerie JS locali
│   └── css/                    # CSS locali
├── .pi/                        # Risorse pi-coding-agent
│   ├── settings.json
│   ├── skills/                 # Skill: podman, python, ffmpeg
│   ├── extensions/             # Extension: python-lsp, commands
│   └── prompts/                # Template prompt
├── docs/
│   ├── architecture.md         # Architettura e topologia
│   ├── context.md              # Contesto e device
│   ├── setup-octoprint.md      # Guida setup OctoPrint
│   ├── references/             # API GoPro Hero 4 (archiviate)
│   ├── handoff/                # Handoff tecnici
│   └── plans/                  # Piano di sviluppo
└── AGENTS.md                   # Contesto progetto per l'agente
```

## Architettura Container

```
Host (OUYA)
│
├── nginx-rtmp (container)
│   ├── Porta 1935 (RTMP input)
│   ├── Porta 8080 (HTTP/HLS output)
│   └── Rete: bridge
│
└── goprostream (container)
    ├── network_mode: host
    ├── Python 3.11 + FFmpeg
    ├── Connessione a GoPro (10.5.5.9)
    └── Push RTMP a localhost:1935
```

### Perché `network_mode: host`

Il container Python deve raggiungere la GoPro su `10.5.5.9` (WiFi Direct).
Con host networking, il container usa la stessa rete dell'OUYA.

## OctoPrint

Per visualizzare lo stream nell'interfaccia OctoPrint:

1. Configura **Classic Webcam** (integrato da OctoPrint 1.9.0)
2. Imposta Stream URL: `http://<ouya_ip>:8080/hls/gopro.m3u8`

Vedi `docs/setup-octoprint.md` per dettagli.

## Troubleshooting

| Problema | Soluzione |
|----------|-----------|
| Container non si avvia | `podman-compose logs nginx-rtmp` |
| GoPro non raggiungibile | `./wifi-connect.sh` poi `ping 10.5.5.9` |
| Stream non visibile | Verifica `curl http://localhost:8080/hls/gopro.m3u8` |
| FFmpeg crash | Controlla log: `podman-compose logs goprostream` |
| Player non funziona | Verifica che nginx sia up: `podman-compose ps` |

## Development

```bash
# Type check Python
npx pyright

# Comandi pi (se in sessione)
/typecheck      # Esegue pyright
/status         # Verifica stato componenti
/handoff        # Genera documento handoff
```

## License

MIT
