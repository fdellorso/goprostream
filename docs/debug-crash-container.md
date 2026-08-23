# Debug Crash Container goprostream — Report Completo

> Data: 2026-08-23/24
> Stato: In corso — causa identificata, fix non ancora implementato

---

## 1. Problema

Il container `goprostream` va in crash periodicamente. Dopo il crash, lo stream HLS si interrompe. Riavviando il container, lo stream riprende.

**Sintomi osservati:**
- Container goprostream mostra `Up` ma l'HLS non funziona
- FFmpeg è ancora vivo ma non manda dati a nginx
- Il player mostra "Non connesso"
- Riavviando il container → tutto riprende

---

## 2. Componenti del sistema

```
GoPro Hero 4 ──UDP:8554──► goprostream.py ──RTMP:1935──► nginx-rtmp ──HLS:8080──► Browser
                              │
                              ├── KeepAlive (processo separato, ogni 2.5s)
                              │
                              └── FFmpeg (subprocess)
                                  └── converte UDP → RTMP
```

| Componente | Tipo | Ruolo |
|------------|------|-------|
| GoPro Hero 4 | Hardware | Sorgente video, manda flusso UDP |
| WiFi Direct | Rete wireless | Trasporto UDP tra GoPro e OUYA |
| goprostream.py | Python (container) | Bridge UDP → RTMP, supervisore |
| KeepAlive | Processo Python | Mantiene vivo il WiFi (ogni 2.5s) |
| FFmpeg | Processo esterno | Converte UDP MPEG-TS → RTMP FLV |
| nginx-rtmp | Container | Riceve RTMP, genera segmenti HLS |
| Linux kernel | OS | TCP/UDP stack, socket management |

---

## 3. Debug eseguito

### 3.1 Aggiunta logging a goprostream.py

**Fase 1 — Logging base:**
- Log FFmpeg PID all'avvio
- Heartbeat ogni 60 secondi
- Log exit code di FFmpeg quando si ferma
- Log ultime 20 righe di stderr di FFmpeg

**Fase 2 — Monitoraggio processo:**
- Check FFmpeg ogni 10 secondi (vivo/morto)
- Check HLS endpoint ogni 30 secondi (HTTP status)

**Fase 3 — Check connettività:**
- Check UDP GoPro ogni 30 secondi (socket.connect_ex)
- Check status GoPro ogni 30 secondi (HTTP API)
- Check nginx RTMP stat ogni 30 secondi

### 3.2 Script watch-stream.sh

Script di monitoraggio esterno che logga ogni 30 secondi:
- Container stats (podman stats)
- Processo FFmpeg
- Status GoPro (API HTTP)
- Nginx RTMP stat
- HLS endpoint
- File HLS dentro il container (podman exec)
- Spazio disco

### 3.3 Ricerca documentazione

- **FFmpeg:** Nessun auto-reconnect per RTMP output, nessun timeout interno di 60s
- **RTMP protocol:** Nessun keepalive nativo, nessun feedback sullo stato
- **nginx-rtmp:** `drop_idle_publisher` è l'unico timeout (10s default)
- **TCP:** `tcp_fin_timeout=60s` sul kernel OUYA

### 3.4 tcpdump captures

| Capture | File | Risultato |
|---------|------|-----------|
| UDP GoPro (3 min) | /tmp/udp_capture.pcap | 16.537 pacchetti, **NESSUN gap** |
| WiFi KeepAlive (1 min) | /tmp/keepalive.pcap | 33 pacchetti, **ogni 2.5s esatti** |
| RTMP TCP (3 min) | /tmp/rtmp_capture.pcap | **FIN da FFmpeg ogni 60s** |

### 3.5 Socket monitoring

- Verificato stato socket RTMP con `/proc/PID/net/tcp`
- Socket passa da ESTABLISHED (01) a FIN_WAIT_2 (08)
- `tcp_fin_timeout=60s` spiega quanto a lungo resta in FIN_WAIT_2

### 3.6 nginx RTMP logging

- Aggiunto `error_log info;` a nginx.conf
- Aggiunto `location /stat` per statistiche RTMP
- Log trovati via `podman logs nginx-rtmp`:
  ```
  22:00:52 disconnect, client: 127.0.0.1
  22:01:02 client connected '127.0.0.1'
  22:01:02 publish: name='gopro' type=live
  22:01:52 disconnect, client: 127.0.0.1  ← 60s dopo
  ```

---

## 4. Risultati delle prove

### 4.1 Cosa funziona

| Componente | Stato | Verifica |
|------------|-------|----------|
| GoPro UDP | ✅ Continuo | tcpdump: 16.537 pacchetti, 0 gap |
| WiFi KeepAlive | ✅ Perfetto | tcpdump: ogni 2.5s, 0 gap |
| goprostream.py | ✅ Supervisore funziona | Log: rileva, killa, riavvia |
| nginx-rtmp | ✅ Funziona | HLS 200 quando FFmpeg è connesso |
| HLS | ✅ Funziona | Segmenti .ts scritti correttamente |

### 4.2 Cosa NON funziona

| Componente | Stato | Dettaglio |
|------------|-------|-----------|
| Connessione RTMP | 🔴 Caduta ogni 60s | FFmpeg chiude il socket |
| FFmpeg | ⚠️ Non esce da solo | Resta vivo anche con socket morto |

### 4.3 Dati chiave

| Dato | Valore |
|------|--------|
| Intervallo crash | **60 secondi esatti** |
| Durata publish prima del crash | **~50 secondi** |
| Chi chiude la connessione | **FFmpeg** (manda FIN, non nginx) |
| tcp_fin_timeout | **60 secondi** (kernel) |
| drop_idle_publisher | 10s (non è la causa) |

---

## 5. Catena del crash

```
T+0s   : FFmpeg si connette a nginx:1935, inizia a mandare dati RTMP
T+50s  : FFmpeg manda FIN a nginx (chiude la connessione)
T+50s  : nginx registra "disconnect"
T+50s  : Socket entra in FIN_WAIT_2
T+60s  : Kernel chiude il socket (tcp_fin_timeout)
T+60s  : Supervisore rileva "socket non ESTABLISHED"
T+60s  : Supervisore killa FFmpeg
T+62s  : Supervisore avvia nuovo FFmpeg
T+62s  : Nuovo FFmpeg si connette a nginx → riprende
T+112s : FFmpeg chiude di nuovo → repeat
```

---

## 6. Causa identificata

### FFmpeg chiude la connessione RTMP dopo ~50 secondi

**Confermato da:**
1. Log nginx: `disconnect` ogni 60s
2. tcpdump: FIN da FFmpeg ogni 60s
3. Socket monitoring: FIN_WAIT_2 ogni 60s

### Perché FFmpeg chiude?

**Ipotesi (da verificare):**

| # | Ipotesi | Probabilità |
|---|---------|-------------|
| 1 | FFmpeg ha un timeout interno sulla connessione RTMP | 🟡 Media |
| 2 | FFmpeg rileva un errore di scrittura (EPIPE) e chiude | 🟡 Media |
| 3 | Il buffer FLV si riempie e FFmpeg chiude per gestire l'errore | 🟢 Bassa |
| 4 | La GoPro causa un errore che FFmpeg traduce in chiusura | 🟢 Bassa |
| 5 | Interferenza del KeepAlive sul socket UDP | 🟢 Bassa |

### Cosa NON è la causa

| Causa esclusa | Perché |
|---------------|--------|
| GoPro interrompe UDP | tcpdump: 0 gap in 3 minuti |
| WiFi Direct cade | KeepAlive: ogni 2.5s, 0 gap |
| nginx droppa il publisher | tcpdump: FIN viene da FFmpeg, non da nginx |
| drop_idle_publisher | Timeout a 10s, non 60s |
| KeepAlive non funziona | tcpdump: perfetto ogni 2.5s |

---

## 7. Soluzione temporanea (implementata)

### Supervisore con auto-recovery

```
Supervisor loop (ogni 30s):
├── Check 1: Socket RTMP (ESTABLISHED?)
│   ├── Sì → OK
│   └── No → kill FFmpeg → restart
├── Check 2: GoPro streaming?
│   ├── Sì → OK
│   └── No → restart stream GoPro
└── Diagnostica: HLS endpoint (log)
```

**Risultato:** Il sistema si auto-ripara. Crash ogni 60s ma recovery automatico in ~2s.

---

## 8. TODO

- [ ] Capire perché FFmpeg chiude dopo ~50s (opzione FFmpeg o codice sorgente)
- [ ] Testare se un'opzione FFmpeg diversa risolve il problema
- [ ] Implementare fix definitivo
- [ ] Verificare se il problema si verifica anche senza supervisore
- [ ] Testare su hardware diverso (non OUYA)

---

## 9. File modificati

| File | Modifiche |
|------|-----------|
| `python/goprostream.py` | Supervisore con auto-recovery, socket monitoring, health checks |
| `docker/nginx.conf` | Log level `info`, stat endpoint `/stat` |
| `scripts/watch-stream.sh` | Script di monitoraggio esterno |

---

## 10. Comandi utili per debug futuro

```bash
# Stato container
podman ps --format "{{.Names}}: {{.Status}}"

# Log goprostream (ultimi 20)
podman logs --tail 20 goprostream

# Log nginx RTMP
podman logs nginx-rtmp 2>&1 | grep -E "disconnect|connect|publish"

# Socket state
FFPID=$(pgrep ffmpeg); FD4=$(readlink /proc/$FFPID/fd/4 | grep -oP '\d+'); cat /proc/$FFPID/net/tcp | grep $FD4

# Stat RTMP
curl -s http://localhost:8080/stat | grep -E "<name>|<active>|<nclients>"

# HLS test
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/hls/gopro.m3u8
```
