# Handoff Fase 3 — 2026-08-21

## Commit

```
93fbdfb feat: fase 3 — README completo, dashboard monitoraggio, Python 3.11, Dockerfile ottimizzato
```

## Completato

| Task | Descrizione | Stato |
|------|-------------|-------|
| 3.4 | Aggiornamento dipendenze (Python 3.11, Pipfile) | ✅ |
| 3.5 | README completo con guida deployment | ✅ |
| 3.6 | Dashboard monitoraggio (`/`) | ✅ |

## Rimasto (richiede GoPro accesa)

| Task | Descrizione | Stato |
|------|-------------|-------|
| 3.1 | Systemd service | ⏳ Da fare |
| 3.2 | Test unitari | ⏳ Da fare |
| 3.3 | Test integrazione | ⏳ Da fare |

## Test Possibili Senza GoPro

### 1. Nginx / Player
```bash
podman-compose up -d
# Apri browser: http://<ip_ouya>:8080/
# → Dashboard con stato stream
# → http://<ip_ouya>:8080/hlsjs.html (player hls.js)
# → http://<ip_ouya>:8080/videojs.html (player video.js)
```

### 2. Dashboard
```bash
# http://<ip_ouya>:8080/
# Mostra: stato HLS, RTMP, log
# HLS check periodico ogni 5s
```

### 3. Container
```bash
podman-compose ps              # Stato container
podman-compose logs -f         # Log live
podman exec nginx-rtmp ls /mnt/player/  # Verifica volumi
```

## Test Da Fare con GoPro

1. `./wifi-connect.sh` → connessione WiFi
2. `./start.sh` → avvio streaming
3. Verifica su OctoPrint: `http://<octoprint>:5000`
4. Verifica latenza stream
5. Test KeepAlive (lasciare girare 5+ minuti)

## Note Finali

- Il player è raggiungibile da qualsiasi browser sulla rete
- La dashboard mostra lo stato in tempo reale
- Lo streaming HLS richiede la GoPro accesa e connessa
- OctoPrint test è l'ultimo step, dopo verifica completa del pipeline
