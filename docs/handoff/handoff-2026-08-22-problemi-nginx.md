# Handoff Problemi Nginx — 2026-08-22

## Stato Attuale

### ✅ Cosa funziona

| Componente | Stato | Note |
|------------|-------|------|
| Container `nginx-rtmp` | ✅ Avviato | Immagine `vallahaye/nginx-rtmp:stable-alpine` |
| Container `goprostream` | ✅ Creato | Non avviato (manca GoPro connessa) |
| Dashboard (`/`) | ✅ Funziona | `http://localhost:8080/` → `dashboard.html` |
| `dashboard.html` | ✅ Funziona | Accessibile via `http://localhost:8080/dashboard.html` |
| `videojs.html` | ✅ Funziona | Accessibile via `http://localhost:8080/videojs.html` |
| `test.txt/html` | ✅ Funziona | File di test creati on-the-fly funzionano |
| RTMP server | ✅ In ascolto | Porta 1935 |
| HTTP server | ✅ In ascolto | Porta 8080 |
| `nginx.conf` | ✅ Caricata | Config RTMP + HTTP funzionante |
| Pairing GoPro | ✅ Testato | `gpPair` funziona via HTTP/HTTPS |
| SSID GoPro | ✅ Documentato | `GP<numero_seriale>`, password `goprohero` |

### ❌ Cosa NON funziona

| Componente | Problema | Gravità |
|------------|----------|---------|
| `hlsjs.html` | Restituisce 404 nonostante il file esista e sia leggibile | 🔴 Alto |
| Location HTTP `/dash` | Causa conflitto con modulo RTMP → tutti i file restituiscono 404 | 🔴 Alto |
| `allow publish` in RTMP | Causa conflitto con HTTP → 404 su tutti i file | 🔴 Alto |
| GoPro streaming | Non testato (batteria scarica, SD card needed) | 🟠 Da fare |

### ⚠️ Problema Specifico: hlsjs.html

**Sintomi:**
- `dashboard.html` → ✅ 200 OK
- `videojs.html` → ✅ 200 OK
- `hlsjs.html` → ❌ 404 Not Found
- Copia di `hlsjs.html` con nome diverso → ✅ 200 OK
- File di test creati on-the-fly → ✅ 200 OK
- Riavvio container → ❌ Ancora 404

**Cose verificate:**
- Il file esiste nel container (`/mnt/player/hlsjs.html`)
- Il file è leggibile (`cat` funziona)
- Il file ha permessi corretti (`-rw-r--r--`)
- Nessun carattere nascosto nel nome file
- Encoding UTF-8 (come gli altri file)
- Stesso contenuto copiato con nome diverso → funziona
- Bind mount corretto (`../player:/mnt/player:ro`)

**Ipotesi rimaste:**
- Cache a livello di filesystem/podman sul file specifico
- Inode o metadata corrotto dal sistema operativo host (OUYA)
- Bug nella gestione dei bind mount di podman con file pre-esistenti

### 🔧 Soluzione Provvisoria

Rinominare `hlsjs.html` in un altro nome (es. `stream.html`) o usare `dashboard.html` come player di default.

### 📋 nginx.conf — Configurazione Finale

La config funzionante **NON include**:
- ❌ `allow publish` / `deny publish` nel blocco RTMP
- ❌ Location HTTP `/dash`

La config funzionante **include**:
- ✅ RTMP: `application live` con push a `show`
- ✅ RTMP: `application show` con HLS + DASH
- ✅ HTTP: location `/` con root `/mnt/player` e index `dashboard.html`
- ✅ HTTP: location `/hls` con types HLS
- ✅ HTTP: location `/js/` e `/css/`

### 📝 Modifiche Non Committate

| File | Modifica |
|------|----------|
| `docker/nginx.conf` | Rimossa location `/dash`, rimossi `allow/deny publish` |
| `docker/docker-compose.yml` | Rimosso health check dependency |
| `docker/Dockerfile.python` | Rimosso HEALTHCHECK |
| `scripts/setup.sh` | Semplificato (rimosso loop attesa) |
| `scripts/wifi-connect.sh` | Logica pairing basata su status 63+31 |
| `scripts/gopro-pair.sh` | Nuovo: pairing senza app |

## Prossimi Passi (Prossima Sessione)

1. **Risolvere il problema hlsjs.html** — opzioni:
   - Rinominare il file (soluzione veloce)
   - Investigare il problema di podman/filesystem
   - Usare `dashboard.html` come unico player

2. **Testare lo streaming** — quando la GoPro è pronta:
   - `./scripts/wifi-connect.sh`
   - `./scripts/start.sh`
   - Verificare flusso HLS su OctoPrint

3. **Aggiornare il player** — il file `hlsjs.html` include:
   - CDN hls.js locale (funziona offline)
   - Codice di auto-play
   - Gestione errori

4. **Commit delle modifiche** — tutte le modifiche attuali non sono committate

## GoPro Status (testato oggi)

```
SSID: GP26479007
Password: goprohero
IP: 10.5.5.9
WiFi mode: 1 (App)
Batteria: 0 (scarica)
SD Card: presente
Auto Power Off: 0 (Never)
Pairing PIN: 6105 (testato, funziona)
```

## Comandi Utili

```bash
# Verifica stato container
podman ps -a

# Log nginx
podman logs nginx-rtmp

# Test dashboard
curl -4 http://localhost:8080/

# Test file specifico
curl -4 http://localhost:8080/hlsjs.html

# Riavvia container
podman-compose -f docker/docker-compose.yml restart

# Ferma tutto
./scripts/stop.sh
```
