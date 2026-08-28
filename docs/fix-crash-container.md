# Piano Fix — Crash Container goprostream

> **Data**: 2026-08-28
> **Stato**: Solo documentazione, nessuna implementazione applicata
> **Riferimento**: `docs/analisi-crash-container.md`

---

## Riepilogo fix da applicare

| # | Fix | Priorità | Difficoltà | File |
|---|-----|----------|------------|------|
| 1 | Supervisore `_check_rtmp_socket()` — fix stati kill | 🔴 Alta | Bassa | `python/goprostream.py` |
| 2 | FFmpeg zombie — rimuovere `shell=True` | 🔴 Alta | Bassa | `python/goprostream.py` |
| 3 | FFmpeg zombie — aggiungere `wait()` dopo SIGKILL | 🔴 Alta | Bassa | `python/goprostream.py` |
| 4 | Network mode — valutare rimozione da goprostream | 🟠 Media | Alta | `docker/docker-compose.yml` |
| 5 | Supervisore — monitorare keepalive | 🟠 Media | Bassa | `python/goprostream.py` |

---

## Fix 1: Supervisore `_check_rtmp_socket()` — fix stati kill

### Problema

Il supervisore killa FFmpeg per **qualsiasi stato TCP che non sia ESTABLISHED**.
Gli stati transitori (SYN_SENT, FIN_WAIT_1/2, TIME_WAIT) sono normali durante
riconnessioni. Killare FFmpeg in questi stati causa restart inutili.

### Soluzione

Cambiare la logica: killa solo se lo stato indica una connessione morta.

**Stati da killare**:
- `06` (CLOSE_WAIT) — nginx ha chiuso, FFmpeg non lo sa
- `07` (LAST_ACK) — aspettiamo ACK finale
- `01` con socket chiuso — connessione terminata

**Stati da NON killare** (transitori):
- `02` (SYN_SENT) — sta connettendosi
- `03` (SYN_RECV) — in accettazione
- `04` (FIN_WAIT_1) — abbiamo chiuso, aspettiamo ACK
- `08` (FIN_WAIT_2) — chiuso, aspettiamo chiusura remota
- `06` (TIME_WAIT) — chiuso, aspettiamo pacchetti fantasma

### Pseudocodice

```python
# STATI MORTI — kill
KILL_STATES = {"06", "07"}  # CLOSE_WAIT, LAST_ACK

# STATI TRANSITORI — non killare, aspetta
TRANSIENT_STATES = {"02", "03", "04", "08"}  # SYN_*, FIN_WAIT_*

def _check_rtmp_socket(pid: int) -> str:
    """Restituisce lo stato del socket RTMP.
    Return: 'ESTABLISHED', 'TRANSIENT', 'DEAD', 'UNKNOWN'
    """
    # ... leggi /proc/{pid}/net/tcp ...
    if state == "01":
        return "ESTABLISHED"
    elif state in KILL_STATES:
        return "DEAD"
    elif state in TRANSIENT_STATES:
        return "TRANSIENT"
    else:
        return "UNKNOWN"
```

### Logica supervisore

```python
socket_status = _check_rtmp_socket(stream._ffmpeg.pid)

if socket_status == "DEAD":
    # Kill immediato
    stream._kill_ffmpeg()
    stream._start_ffmpeg()

elif socket_status == "TRANSIENT":
    # Aspetta e ricontrolla dopo N secondi
    # Solo se dura da troppo (> 30s), allora kill
    pass

elif socket_status == "UNKNOWN":
    # Stato sconosciuto, log warning ma non killare
    log.warning("Stato socket sconosciuto: %s", state)

# elif "ESTABLISHED": non fare nulla
```

### Aggiungere contatore transitori

Per evitare di killare durante transitori normali, contare quanti check
consecutivi sono transitori. Se supera una soglia (es. 3 check = 30 secondi),
allora kill.

```python
transient_count = 0

while not stream._shutdown:
    time.sleep(10)
    status = _check_rtmp_socket(stream._ffmpeg.pid)

    if status == "ESTABLISHED":
        transient_count = 0
    elif status == "TRANSIENT":
        transient_count += 1
        if transient_count >= 3:
            log.warning("Socket in stato transitorio da 30s → kill")
            stream._kill_ffmpeg()
            stream._start_ffmpeg()
            transient_count = 0
    elif status == "DEAD":
        log.warning("Socket morto → kill")
        stream._kill_ffmpeg()
        stream._start_ffmpeg()
        transient_count = 0
```

### Impatto

- Riduce drasticamente i restart inutili
- Il supervisore diventa più tollerante ai transienti
- Mantiene la capacità di rilevare connessioni morte

---

## Fix 2: FFmpeg zombie — rimuovere `shell=True`

### Problema

`subprocess.Popen("ffmpeg ...", shell=True)` crea DUE processi:
- Shell (PID X) — è il `self._ffmpeg.pid`
- FFmpeg reale (PID X+1) — il child

Se FFmpeg muore per primo, lo shell resta come potenziale zombie.

### Soluzione

Passare la lista di argomenti direttamente:

```python
# PRIMA
self._ffmpeg = subprocess.Popen(
    "ffmpeg -y -f mpegts -i udp://10.5.5.9:8554 -c copy -an -f flv rtmp://localhost:1935/live/gopro",
    shell=True,
    preexec_fn=os.setsid,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.PIPE,
)

# DOPO
cmd = [
    "ffmpeg", "-y",
    "-f", "mpegts",
    "-i", f"udp://{GOPRO_IP}:{UDP_PORT}",
    "-c", "copy",
    "-an",
    "-f", "flv",
    RTMP_URL,
]
self._ffmpeg = subprocess.Popen(
    cmd,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.PIPE,
    preexec_fn=os.setsid,
)
```

### Impatto

- Elimina il processo shell intermedio
- `self._ffmpeg.pid` è il PID di FFmpeg stesso
- Riduce la probabilità di zombie
- Riduce l'uso di risorse (1 processo invece di 2)

---

## Fix 3: FFmpeg zombie — aggiungere `wait()` dopo SIGKILL

### Problema

Dopo SIGKILL, manca `self._ffmpeg.wait()`. Il processo diventa zombie
nella tabella processi.

### Soluzione

```python
except subprocess.TimeoutExpired:
    try:
        os.killpg(os.getpgid(self._ffmpeg.pid), signal.SIGKILL)
    except ProcessLookupError:
        pass
    self._ffmpeg.wait()  # ← AGGIUNGERE
```

### Impatto

- Elimina gli zombie dopo ogni restart
- Il container resta pulito nel tempo
- Previene il crash per troppi processi defunct

---

## Fix 4: Network mode — valutare rimozione da goprostream

### Problema

`network_mode: host` su goprostream causa:
- Nessun isolamento di rete
- Possibili collisioni di porta
- DNS interno Podman disabilitato
- FFmpeg e nginx condividono lo stesso namespace

### Soluzione candidata

Mantenere `network_mode: host` solo su nginx-rtmp (per il proxy API),
rimuoverlo da goprostream:

```yaml
nginx-rtmp:
  network_mode: host          # MANTIENI per proxy API

goprostream:
  # RIMUOVI network_mode: host → usa bridge
  extra_hosts:
    - "host.docker.internal:host-gateway"
```

### Complicazioni

- FFmpeg deve raggiungere nginx su `host.docker.internal:1935`
- KeepAlive HTTP (`10.5.5.9`) non funziona dal container bridge
- Restart stream GoPro non funziona dal container bridge
- Servono workaround per keepalive e restart

### Workaround possibili

1. KeepAlive su host (script separato)
2. Restart stream su host (script separato)
3. Miniproxy in goprostream (riabilita di fatto il container API)

### Impatto

- Isolamento di rete per goprostream
- Riduce collisioni
- Aumenta complessità operativa
- Richiede test su OUYA

### Raccomandazione

Fare questo fix per ultimo, dopo aver risolto i bug diretti (punti 1-3).
Con i fix 1-3, il crash dovrebbe essere risolto anche con `network_mode: host`.

---

## Fix 5: Supervisore — monitorare keepalive

### Problema

Il supervisore monitora solo FFmpeg. Se il processo keepalive muore,
nessuno lo sa. Il WiFi potrebbe disconnettersi.

### Soluzione

Aggiungere un check nel supervisore:

```python
# Nel loop del supervisore:
if stream._keepalive and not stream._keepalive.is_running:
    log.warning("KeepAlive morto → restart")
    stream._keepalive.start()
```

### Impatto

- Il keepalive viene riavviato se muore
- Il WiFi resta attivo
- Riduce i crash catenari (keepalive muore → FFmpeg muore → restart → ripete)

### Nota

Il keepalive attualmente funziona (non lo abbiamo visto crashare).
Questo fix è preventivo, non urgente.

---

## Ordine di esecuzione

```
1. Fix 2 + Fix 3 (zombie)  ← indipendenti, si possono fare insieme
2. Fix 1 (supervisore)     ← dopo i zombie, per testare il nuovo comportamento
3. Fix 5 (keepalive)       ← preventivo, bassa priorità
4. Fix 4 (network mode)    ← per ultimo, solo se necessario
```

---

## Fix già applicati

| # | Fix | Data | File |
|---|-----|------|------|
| ✅ | Pipfile pin ==4.2.0, rimosso fallback Dockerfile | 2026-08-28 | `python/Pipfile`, `docker/Dockerfile.python` |
| ✅ | hls_fragment 3, hls_playlist_length 10, hls_sync 100ms | 2026-08-28 | `docker/nginx.conf` |
| ✅ | drop_idle_publisher 30s, idle_streams off | 2026-08-28 | `docker/nginx.conf` |
| ✅ | allow/deny publish, ping 30s | 2026-08-28 | `docker/nginx.conf` |

---

## Testing

Dopo ogni fix, testare su OUYA:

1. `podman-compose up -d` — container parte
2. `curl http://localhost:8080/hls/gopro.m3u8` — HLS risponde
3. `curl http://localhost:8080/stat` — statistiche RTMP
4. Avviare stream GoPro — verificare che FFmpeg riceve UDP
5. Lasciare girare per 30+ minuti — verificare che non crasha
6. `podman exec goprostream ps aux` — verificare nessun zombie
7. `podman logs goprostream --tail 50` — verificare log puliti

---

## Stato

- [x] Documentazione completata
- [ ] Fix 1 applicato (supervisore)
- [ ] Fix 2 applicato (shell=True)
- [ ] Fix 3 applicato (wait dopo SIGKILL)
- [ ] Fix 4 applicato (network mode)
- [ ] Fix 5 applicato (monitor keepalive)
- [ ] Test su OUYA
