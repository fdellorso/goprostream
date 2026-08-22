# Audit Codice — 2026-08-21

## Scope

Revisione completa del codice sorgente: `goprostream.py`, `goprophoto.py`, `docker-compose.yml`, `nginx.conf`, player HTML, `Pipfile`.

---

## 1. `goprostream.py` — Bridge Streaming

### ✅ Cosa funziona

- Logica di base corretta: avvia streaming GoPro → lancia FFmpeg UDP→RTMP → KeepAlive
- Gestione segnali con `os.setsid` / `os.killpg` per chiudere FFmpeg pulitamente

### ❌ Cosa non funziona

| # | Problema | Riga | Gravità |
|---|----------|------|---------|
| S1 | `self.ffmpeg = ""` — tipo `str`, poi usato come `Popen`. Pyright: `attribute "pid" unknown for str` | L9, L43 | 🔴 Alto |
| S2 | `import constants` non usato | L10 | 🟡 Basso |
| S3 | `KeepAlive` chiamato **una volta sola** dopo 10s. La GoPro disconnette dopo ~10s senza keepalive. Serve un **loop continuo** | L35-36 | 🔴 Alto |
| S4 | Nessun controllo errore su `subprocess.Popen` — se FFmpeg fallisce, crash silenzioso | L29 | 🟠 Medio |
| S5 | `shell=True` — rischio command injection | L35 | 🟠 Medio |
| S6 | `stdout=subprocess.PIPE` ma non viene mai letto → può bloccare il processo | L33 | 🟠 Medio |
| S7 | Solo `print()`, nessun log strutturato | Tutte | 🟡 Basso |
| S8 | Nessuna configurabilità (bitrate, risoluzione, IP) — tutto hardcoded | Tutte | 🟡 Basso |

### ⚠️ Cosa va migliorato

- `self.ffmpeg` deve essere `Optional[subprocess.Popen[bytes]]` non `str`
- Il KeepAlive deve essere in un **thread/timer separato** che gira continuamente
- Aggiungere `stderr=subprocess.PIPE` per catturare errori FFmpeg
- Parametri da config: IP GoPro, bitrate, risoluzione, porta RTMP
- Logging strutturato (modulo `logging`)

---

## 2. `goprophoto.py` — Scatto Foto

### ✅ Cosa funziona

- Logica corretta: imposta modalità Photo → scatta → scarica

### ❌ Cosa non funziona

| # | Problema | Riga | Gravità |
|---|----------|------|---------|
| P1 | `from operator import concat` — import inutilizzato e fuori contesto | L3 | 🔴 Alto |
| P2 | `constants` non usato direttamente | L6 | 🟡 Basso |
| P3 | Nessun controllo errore se il download fallisce | L22 | 🟠 Medio |
| P4 | Variabile `goprostream` fuorviante (è un `GoProPhoto`) | L27 | 🟡 Basso |
| P5 | `take_photo(0)` — parametro non documentato | L22 | 🟡 Basso |

### ⚠️ Cosa va migliorato

- Rimuovere `from operator import concat`
- Rinominare la variabile in `goprophoto`
- Aggiungere gestione errori su download

---

## 3. `docker-compose.yml`

### ✅ Cosa funziona

- Struttura semplice e corretta
- Porte mappate correttamente (1935, 8080)
- Volume nginx.conf montato
- Compatibile podman-compose

### ⚠️ Cosa va migliorato

| # | Problema | Gravità |
|---|----------|---------|
| D1 | Mancano health checks | 🟠 Medio |
| D2 | Mancano limiti risorse (memoria/CPU) | 🟡 Basso |
| D3 | Nessuna rete definita esplicitamente | 🟡 Basso |
| D4 | `restart: always` potrebbe non funzionare con podman-compose | 🟡 Basso |

---

## 4. `nginx.conf`

### ✅ Cosa funziona

- Configurazione RTMP→HLS funzionante
- CORS abilitato
- Publish limitato a reti private
- HLS + DASH entrambi configurati

### ⚠️ Cosa va migliorato

| # | Problema | Gravità |
|---|----------|---------|
| N1 | `hls_fragment 3` e `hls_playlist_length 10` → latenza ~13s. Per bassa latenza meglio 1s/3s | 🟠 Medio |
| N2 | Mancano header di sicurezza (X-Frame-Options, CSP) | 🟡 Basso |
| N3 | `chunk_size 4000` → potrebbe essere più alto per performance | 🟡 Basso |
| N4 | `sendfile off` + `directio 512` → potenziale impatto performance | 🟡 Basso |

---

## 5. Player HTML

### `hlsjs.html`

| # | Problema | Gravità |
|---|----------|---------|
| H1 | **CDN esterno necessario** — se l'OUYA non ha internet, il player non funziona | 🔴 Alto |
| H2 | Bootstrap 3.3.7 (2017, vecchio) | 🟡 Basso |
| H3 | jQuery 3.4.1 (vecchio) | 🟡 Basso |
| H4 | `muted="muted"` → audio disattivato di default | 🟡 Basso |

### `videojs.html`

| # | Problema | Gravità |
|---|----------|---------|
| H5 | **CDN esterno necessario** — stesso problema di H1 | 🔴 Alto |
| H6 | Video.js 7.5.5 (2018, vecchio) | 🟡 Basso |

> **Nota CDN**: La GoPro crea una rete WiFi Direct **senza accesso a Internet**. Se le librerie JS (hls.js, video.js) vengono caricate da CDN esterni, il browser non riesce a scaricarle e il player non parte. Soluzione: includere le librerie localmente nel container.

---

## 6. `Pipfile`

| # | Problema | Gravità |
|---|----------|---------|
| F1 | `python_version = "3.8"` → EOL ottobre 2024. Meglio 3.10+ | 🟠 Medio |
| F2 | `goprocam = "*"` → nessun version pin | 🟡 Basso |
| F3 | `[dev-packages]` vuoto → pyright non è nel Pipfile | 🟡 Basso |

---

## 7. Struttura Mancante

| Cosa | Stato | Priorità |
|------|-------|----------|
| `.env` o configurazione centralizzata | ❌ Manca | 🔴 Alta |
| `requirements.txt` (per chi non usa pipenv) | ❌ Manca | 🟡 Bassa |
| Test | ❌ Nessuno | 🟡 Bassa |
| Script di setup/installazione | ❌ Manca | 🟠 Media |
| Script di avvio | ❌ Manca | 🟠 Media |
| Configurazione WiFi (connessione alla GoPro) | ❌ Manca | 🔴 Alta |
| Configurazione OctoPrint Classic Webcam | ❌ Manca | 🟠 Media |
| Librerie JS locali (no CDN) | ❌ Manca | 🔴 Alta |

---

## Riepilogo per Priorità

### 🔴 Priorità Alta (Bloccante)
- S1: Tipo `self.ffmpeg` errato
- S3: KeepAlive senza loop
- H1/H5: CDN esterno (player offline non funziona)
- F1: Configurazione centralizzata (.env)
- Connessione WiFi alla GoPro

### 🟠 Priorità Media
- S4/S5/S6: Error handling FFmpeg
- P1: Import morto in goprophoto
- D1: Health checks docker
- N1: Frammenti HLS troppo grandi
- Script setup/avvio
- Configurazione OctoPrint

### 🟡 Priorità Bassa
- S7/S8: Logging e configurabilità
- P2/P4/P5: Pulizia goprophoto
- D2/D3/D4: Docker improvements
- N2/N3/N4: Nginx improvements
- H2/H3/H4/H6: Aggiornamento versioni
- F2/F3: Pipfile improvements
- Test
