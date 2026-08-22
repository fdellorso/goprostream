# Piano Sviluppo — GoPro Streaming Server

> Obiettivo: prodotto funzionante, deployabile, manutenibile.

---

## Fase 1: Fix Critici 🔴

**Obiettivo**: Il codice funziona senza crash e senza blocchi.

| # | Task | File | Dettaglio |
|---|------|------|-----------|
| 1.1 | Fix tipo `self.ffmpeg` | `goprostream.py` | Cambiare da `str` a `Optional[subprocess.Popen[bytes]]` |
| 1.2 | Loop KeepAlive | `goprostream.py` | Thread/timer che chiama `KeepAlive()` ogni 8 secondi |
| 1.3 | Fix import morti | `goprostream.py`, `goprophoto.py` | Rimuovere `constants` (se non usato) e `concat` |
| 1.4 | Fix variabile | `goprophoto.py` | Rinominare `goprostream` → `goprophoto` |
| 1.5 | Error handling FFmpeg | `goprostream.py` | Catturare stderr, controllare exit code |
| 1.6 | Configurazione centralizzata | `.env` / `config.py` | IP GoPro, bitrate, risoluzione, porta RTMP, porta HTTP |
| 1.7 | Player offline | `hlsjs.html`, `videojs.html` | Scaricare hls.js/video.js localmente nel container |

**Uscita**: Codice che pyright approva (0 errori), KeepAlive funzionante, player offline.

---

## Fase 2: Funzionalità 🟠

**Obiettivo**: Il sistema si deploya e funziona con un comando.

| # | Task | File | Dettaglio |
|---|------|------|-----------|
| 2.1 | Script di setup | `setup.sh` | Installa dipendenze Python, crea venv, avvia container |
| 2.2 | Script di avvio | `start.sh` | Orchestra: podman-compose up → attesa nginx → avvia goprostream.py |
| 2.3 | Connessione WiFi | `wifi-connect.sh` o modulo Python | Si connette alla rete WiFi Direct della GoPro |
| 2.4 | Health checks | `docker-compose.yml` | Verifica che Nginx sia pronto prima di pushare stream |
| 2.5 | Logging strutturato | `goprostream.py` | Modulo `logging` al posto di `print()` |
| 2.6 | Configurazione OctoPrint | `docs/setup-octoprint.md` | Guida setup Classic Webcam con URL HLS |
| 2.7 | Frammenti HLS ottimizzati | `nginx.conf` | `hls_fragment 1` + `hls_playlist_length 3` per bassa latenza |

**Uscita**: `./setup.sh` installa tutto, `./start.sh` avvia tutto, documentazione OctoPrint.

---

## Fase 3: Produzione 🟡

**Obiettivo**: Robusto, manutenibile, deployabile su altra macchina.

| # | Task | File | Dettaglio |
|---|------|------|-----------|
| 3.1 | Systemd service | `goprostream.service` | Avvio automatico all'avvio del sistema |
| 3.2 | Test unitari | `tests/` | Test logica Python (mock GoPro) |
| 3.3 | Test integrazione | `tests/` | Test pipeline completo (mock FFmpeg + Nginx) |
| 3.4 | Aggiornamento dipendenze | `Pipfile`, `package.json` | Python 3.10+, version pin, aggiornamento versioni |
| 3.5 | README completo | `README.md` | Guida deployment passo-passo |
| 3.6 | Dashboard monitoraggio | `monitor.html` | Pagina che mostra stato stream, bitrate, latenza |

**Uscita**: Sistema pronto per produzione, documentato, testato.

---

## Ordine di Esecuzione Consigliato

```
1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6 → 1.7
                                              ↓
                        2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6 → 2.7
                                                                          ↓
                                              3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6
```

## Stima Tempo

| Fase | Task | Stima |
|------|------|-------|
| Fase 1 | Fix critici | 1-2 ore |
| Fase 2 | Funzionalità | 2-3 ore |
| Fase 3 | Produzione | 3-4 ore |
| **Totale** | | **6-9 ore** |

## Dipendenze

- **Fase 1** → Nessuna dipendenza
- **Fase 2** → Richiede Fase 1 completata
- **Fase 3** → Richiede Fase 2 completata
- **2.3 (WiFi)** → Richiede test fisico con GoPro accesa
- **2.6 (OctoPrint)** → Richiede OctoPrint installato e funzionante
