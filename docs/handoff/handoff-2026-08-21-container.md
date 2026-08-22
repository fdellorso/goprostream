# Handoff Container Python — 2026-08-21

## Commit

```
df0043b feat: container Python con network_mode: host, Dockerfile, script avvio/ferma
```

## Architettura Finale

```
Host (OUYA):
  ├── wifi-connect.sh          ← Connessione WiFi GoPro (host-side)
  ├── podman-compose up        ← Avvia tutto
  │
  ├── Container: nginx-rtmp
  │   ├── Porta 1935 (RTMP)
  │   ├── Porta 8080 (HTTP/HLS)
  │   └── Rete: bridge (default)
  │
  └── Container: goprostream
      ├── network_mode: host    ← Usa la rete dell'host
      ├── Python + FFmpeg
      ├── Connessione a GoPro (10.5.5.9)
      └── Push RTMP a localhost:1935
```

## Perché `network_mode: host`

- Il container Python deve raggiungere la GoPro su `10.5.5.9`
- La GoPro è sulla rete WiFi Direct dell'OUYA
- Con `network_mode: host` il container usa la stessa rete dell'host
- Raggiunge anche nginx-rtmp su `localhost:1935`

## Flusso d'Uso

```bash
# 1. Setup (una tantum)
./setup.sh

# 2. Connetti WiFi alla GoPro (deve essere prima, host-side)
./wifi-connect.sh

# 3. Avvia tutto
./start.sh

# 4. Ferma tutto
./stop.sh
```

## File

| File | Descrizione |
|------|-------------|
| `Dockerfile.python` | Immagine Python 3.11 + FFmpeg + goprocam |
| `docker-compose.yml` | 2 servizi: nginx-rtmp + goprostream (host network) |
| `setup.sh` | Build immagine + avvia container |
| `start.sh` | Verifica GoPro + avvia container |
| `stop.sh` | Ferma container |
| `.dockerignore` | Esclude file non necessari dal build |
| `.env.example` | Template configurazione aggiornato |

## Note

- La connessione WiFi DEVE essere fatta prima di avviare il container
- Il container goprostream ha `restart: unless-stopped` (si riavvia automaticamente)
- Il container goprostream dipende da nginx-rtmp (`condition: service_healthy`)
- Il build dell'immagine Python richiede ~1-2 minuti la prima volta
