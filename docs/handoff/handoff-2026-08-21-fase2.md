# Handoff Fase 2 — 2026-08-21

## Commit

```
ddb3cb8 feat: fase 2 — script setup/start/wifi, health checks, doc OctoPrint
```

## Completato

| Task | Descrizione | Stato |
|------|-------------|-------|
| 2.1 | Script setup.sh (verifica deps, .env, pipenv, npm, container) | ✅ |
| 2.2 | Script start.sh (verifica container, GoPro, avvia streaming) | ✅ |
| 2.3 | Script wifi-connect.sh (connette alla rete WiFi Direct GoPro) | ✅ |
| 2.4 | Health check in docker-compose.yml | ✅ |
| 2.5 | Logging strutturato (già fatto in fase 1) | ✅ |
| 2.6 | Documentazione setup OctoPrint Classic Webcam | ✅ |
| 2.7 | Frammenti HLS ottimizzati (già fatto in fase 1) | ✅ |

## File Nuovi

| File | Descrizione |
|------|-------------|
| `setup.sh` | Setup completo: deps, .env, pipenv, npm, container |
| `start.sh` | Avvio: verifica container → verifica GoPro → streaming |
| `wifi-connect.sh` | Connessione WiFi alla rete GoPro (nmcli/wpa_supplicant) |
| `docs/setup-octoprint.md` | Guida configurazione Classic Webcam in OctoPrint |

## Modalità d'Uso

### Setup iniziale
```bash
./setup.sh
```

### Connessione WiFi alla GoPro
```bash
./wifi-connect.sh
```

### Avvio streaming
```bash
./start.sh
```

### Verifica stato
```bash
/status        # Comando pi (se in sessione)
podman-compose ps
curl http://localhost:8080/hls/gopro.m3u8
```

## Note

- `wifi-connect.sh` usa nmcli (NetworkManager) o wpa_supplicant come fallback
- Lo SSID GoPro di default è `GOPRO-BP-FD` — personalizzare in .env se diverso
- `start.sh` chiede conferma se la GoPro non è raggiungibile (utile per test senza hardware)
- Il container ha health check: `podman-compose ps` mostra lo stato

## Prossimi Passi (Fase 3)

- [ ] Systemd service
- [ ] Test unitari
- [ ] Aggiornamento dipendenze (Python 3.10+, version pin)
- [ ] README completo con guida deployment
- [ ] Dashboard monitoraggio
