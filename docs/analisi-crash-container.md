# Analisi Crash Container goprostream

> **Data**: 2026-08-25 (analisi) → 2026-08-29 (fix)
> **Commit di riferimento**: `42b0726` (pre-regressione) → `HEAD`
> **Stato**: ✅ Fix Fase 1+2 applicati e testati

---

## Riepilogo Regressioni

| # | Regressione | Commit | Tipo | Sospetto | Approfondimento |
|---|-------------|--------|------|----------|------------------|
| 1 | `network_mode: host` | `df0043b` | 🔧 Bug diretto | 🔴 Alto | ✅ 5 opzioni analizzate |
| 2 | Supervisore `_check_rtmp_socket()` troppo aggressivo | `8caba40` | 🔧 Bug diretto | 🔴 Alto | ✅ Approfondito + ✅ **FIXATO** (2026-08-29) |
| 3 | `time.sleep(10)` rimosso dopo `_start_ffmpeg()` | `96870bc` | ⚙️ Rilassamento sistema | 🟡 Basso | ✅ Analisi sleep + keepalive + references GoPro |
| 4 | `hls_fragment 1` (era 3) | `96870bc` | ⚙️ Rilassamento sistema | 🔴 Alto | ✅ Fix: hls_fragment 3, hls_playlist_length 10, hls_sync 100ms |
| 5 | KeepAlive in `multiprocessing.Process` | `96870bc` | ⚙️ Rilassamento sistema | 🟠 Medio | ⚠️ Analisi orfani (risultato: non è il problema) |
| 6 | `drop_idle_publisher 10s` su unica app | `96870bc` | ⚙️ Rilassamento sistema | 🟠 Medio | ✅ Fix: drop_idle_publisher 30s |
| 7 | Dockerfile fallback installation | `96870bc` | — | 🟢 Trascurabile | ✅ Fix: Pipfile pin ==4.2.0, rimosso fallback Dockerfile |
| 8 | Rimossi `allow publish` da nginx | `96870bc` | — | 🟡 Basso | ✅ Fix: allow/deny publish + hls_sync + idle_streams + ping |

**Problema aggiuntivo emerso dall'analisi:**

| # | Problema | Tipo | Probabilità | Approfondimento |
|---|----------|------|-------------|------------------|
| 9 | FFmpeg zombie (`shell=True` + `wait()` mancante dopo SIGKILL) | 🔧 Bug diretto | 🔴 Alta | ✅ 4 bug identificati + ✅ **FIXATO** (2026-08-29) |

> **Legenda Tipo:**
> - 🔧 **Bug diretto** — Causa il crash o il problema direttamente
> - ⚙️ **Rilassamento sistema** — Non causa il crash direttamente, ma riduce i margini di tolleranza e amplifica gli altri bug
> - — Non classificabile

---

## Contesto

Lo streaming funzionava in modo continuo e prolungato al commit `42b0726` (5 luglio 2025).
Da allora il container `goprostream` va in crash dopo un periodo variabile, con sintomo:
FFmpeg si ferma, i logs mostrano attività fino all'ultimo avvio.

Il workaround attuale è `podman-compose restart goprostream`.

---

## Differenze tra `42b0726` e `HEAD`

### Riepilogo Componenti

| Componente | Prima (42b0726) | Dopo (HEAD) |
|------------|-----------------|-------------|
| **Composto** | 1 container (nginx-rtmp) | 2 containers (nginx-rtmp + goprostream) |
| **Python** | Script singolo, ~60 righe | Script complesso, ~440 righe |
| **KeepAlive** | `gopro.KeepAlive()` nel main thread | `multiprocessing.Process` separato |
| **Supervisore** | Nessuno | Loop con health check ogni 30s |
| **FFmpeg** | `stdout=subprocess.PIPE` | `stderr=subprocess.PIPE`, `preexec_fn=os.setsid` |
| **Nginx** | 2 app (live + show), push locale | 1 app, hls più aggressivo |
| **Volume** | `./` (stessa dir) | `../docker/` (path relativi diversi) |
| **Rete** | Porte mappate (`1935:1935`, `8080:8080`) | `network_mode: host` |
| **Restart** | `always` | `unless-stopped` |

---

## Potenziali Causa di Regressione

### 1. `network_mode: host` — Cambio drammatico di rete

**Commit**: `df0043b` — feat: container Python con network_mode: host

```yaml
# PRIMA
ports:
  - "1935:1935"
  - "8080:8080"

# DOPO
network_mode: host
```

**Impatto**: Con `network_mode: host`, FFmpeg dentro il container usa la stessa rete del host.
Problemi possibili:

- Collisions di porta (FFmpeg di un altro processo, porta 8554 già in uso)
- Conflitto con il container nginx-rtmp (anch'esso in `network_mode: host`?)
- **`network_mode: host` disabilita il DNS interno di Podman** — il container potrebbe non risolvere `localhost` in modo attendibile
- Nessun isolamento di rete: un crash in un processo può influenzare l'altro

**Sospetto**: 🔴 **ALTO** — Candidato #1.

---

### 2. Supervisore: `_check_rtmp_socket()` troppo aggressivo

**Commit**: `8caba40` — debug: crash container - causa identificata, supervisore implementato

```python
def _check_rtmp_socket(pid: int) -> bool:
    """Check 1: Verifica se il socket RTMP di FFmpeg è ESTABLISHED."""
    try:
        inodes = _get_ffmpeg_socket_inodes(pid)
        if not inodes:
            return False

        with open(f"/proc/{pid}/net/tcp") as f:
            for line in f:
                for inode in inodes:
                    if inode in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            state = parts[3]
                            if state == "01":  # ESTABLISHED
                                return True
                            # 06=CLOSE_WAIT, 08=FIN_WAIT_2, 07=LAST_ACK
                            return False  # ← QUI
        return False
    except (OSError, IndexError):
        return False
```

**Impatto**: Il check restituisce `False` (e killa FFmpeg) se il socket non è `ESTABLISHED`.
Ma durante la normale negoziazione TCP, lo stato può essere:

- `SYN_SENT` (connessione in corso)
- `CLOSE_WAIT` (riconnessione)
- `FIN_WAIT_2` (chiusura temporanea)

Il supervisore potrebbe uccidere FFmpeg durante una riconnessione normale.

**Sospetto**: 🔴 **ALTO** — **Probabilmente il bug principale.**

---

### 3. KeepAlive in `multiprocessing.Process`

**Commit**: `96870bc` — fix: fase 1 — fix critici, player offline, configurazione centralizzata

```python
# PRIMA
def startStream(self):
    self.gopro.livestream("start")
    time.sleep(10)
    self.gopro.KeepAlive()  # Blocca nel main thread

# DOPO
class KeepAliveTimer:
    def __init__(self, gopro):
        self._process = multiprocessing.Process(
            target=_keepalive_worker,
            args=(gopro.ip_addr,),
            daemon=True,
        )
```

**Impatto**:

- `multiprocessing.Process` usa `fork()` su Linux. Se il processo padre muore, il child può rimanere orfano
- Il worker crea un nuovo `GoProCamera.GoPro()` — se il WiFi scade, il worker muore silenziosamente
- Nessuno riavvia il keepalive se muore (il supervisore non lo monitora)

**Tipo**: ⚙️ **Rilassamento sistema** — Il keepalive non è monitorato dal supervisore.
Se muore, il supervisore non lo sa, e FFmpeg muore a catena.
In un sistema tolerance, questo sarebbe un problema minore.

**Sospetto**: 🟠 **MEDIO-ALTO** — Il keepalive potrebbe morire senza che il supervisore se ne accorga.

---

### 4. Timing rimosso: `time.sleep(10)` dopo avvio FFmpeg

**Commit**: `96870bc`

```python
# PRIMA
self.ffmpeg = subprocess.Popen(...)
time.sleep(10)  # ← Attesa prima del KeepAlive
self.gopro.KeepAlive()

# DOPO
self._start_ffmpeg()
# Nessun sleep → supervisore parte immediatamente
```

**Contesto**: Il `time.sleep(10)` nel codice originale serviva ad attendere che la GoPro
avviasse il server UDP prima di iniziare a mandare pacchetti keepalive. La documentazione
della libreria goprocam (`GoProCamera.py` riga 96-106) e il riferimento ufficiale
(`hero4-livestreaming.md`) indicano che il keepalive va inviato "dopo 10 secondi"
dall'avvio dello streaming. Il keepalive è un pacchetto UDP `_GPHD_` mandato sulla
stessa porta (8554) dove FFmpeg riceve lo stream, ogni 2.5 secondi.

**Cosa fa il keepalive**: Manda un pacchetto UDP `_GPHD_:0:0:2:0.000000\n` sulla porta
8554. Questo dice alla GoPro "sono ancora qui, non disconnettere il WiFi". Senza
questo pacchetto, la GoPro after ~10 secondi disconnette il WiFi Direct.

**Cosa succede senza il sleep**: Il keepalive parte immediatamente dopo l'avvio di FFmpeg.
I primi pacchetti `_GPHD_` vengono mandati sulla porta 8554 mentre FFmpeg è già in
ascolto. Questo può causare:
- Interferenza minima: FFmpeg ignora i pacchetti non-MPEG-TS
- Rischio teorico: i primi pacchetti keepalive potrebbero non arrivare se la GoPro
  non ha ancora avviato il server UDP

**Empiricamente**: Il WiFi della GoPro non si disconnette mai in pratica. Il timeout
documentato di 10 secondi è conservativo. La GoPro mantiene il WiFi attivo anche
senza keepalive per periodi molto più lunghi. Quindi la rimozione del sleep non
causa problemi operativi.

**Tipo**: ⚙️ **Rilassamento sistema** — Non causa il crash direttamente, ma riduce i margini
di tolleranza del sistema. In un sistema con margini più ampi (sleep(10), hls_fragment 3),
il bug del supervisore aggressivo (#2) si manifesterebbe meno spesso.

**Sospetto**: 🟡 **BASSO** — Non è la causa del crash. Il sleep era una precauzione
conservativa, la sua rimozione rende lo start più veloce senza effetti collaterali
noti.

---

### 5. Nginx: `hls_fragment 1` + `hls_playlist_length 3`

**Commit**: `96870bc`

```nginx
# PRIMA
hls_fragment 3;
hls_playlist_length 10;

# DOPO
hls_fragment 1;
hls_playlist_length 3;
```

**Impatto**: Fragment da 1s significa che FFmpeg deve generare un file `.ts` ogni secondo.
Su OUYA (flash I/O lento), questo crea stress:

- Più operazioni di I/O disco
- Maggiore probabilità di micro-lag
- Più file da gestire per nginx
- Se FFmpeg ha un micro-lag, nginx potrebbe droppare il publisher

**Tipo**: ⚙️ **Rilassamento sistema** — Fragment da 1s significa che FFmpeg deve essere preciso
al secondo. Un micro-lag = manca un fragment = nginx droppa il publisher.
Con hls_fragment 3, FFmpeg aveva 3 secondi di margine.

**Dato empirico**: La latenza reale è già di 5-6 secondi con `hls_fragment 1`, non le 2 secondi
teoriche. Questo significa che il componente che introduce la latenza non è il fragment size
ma altrove (buffer FFmpeg, buffering nginx, jitter GoPro). Quindi la modifica ha portato
il costo (sistema più fragile, I/O più stressato) senza il beneficio (latenza bassa).

**Conclusione**: La modifica è controproducente. Con `hls_fragment 3` la latenza sarebbe
la stessa (5-6s) ma con margine più ampio per FFmpeg. È il candidato ideale per essere
revertito: guadagno in stabilità, nessun costo in latenza reale.

**Sospetto**: 🔴 **ALTO** come candidato al fix — è la modifica più facile da revertire
con il miglior rapporto costo/beneficio.

---

### 6. `drop_idle_publisher 10s` su unica application

**Commit**: `96870bc`

```nginx
# PRIMA (2 app)
application live {
    live on;
    drop_idle_publisher 10s;
    push rtmp://localhost:1935/show;  # ← push a "show"
}
application show {
    live on;
    # Nessun drop_idle_publisher
}

# DOPO (1 app)
application live {
    live on;
    drop_idle_publisher 10s;
    hls on;
    # ...
}
```

**Impatto**: Prima, lo stream veniva pushato da "live" a "show".
"show" non aveva `drop_idle_publisher` → il publisher non veniva droppato.
Ora c'è un'unica app con `drop_idle_publisher 10s` → se FFmpeg ha un lag > 10s,
nginx droppa il publisher.

**Tipo**: ⚙️ **Rilassamento sistema** — Con 2 app, "show" non aveva drop_idle_publisher →
il publisher non veniva droppato. Ora con 1 app, se FFmpeg ha un lag > 10s,
nginx droppa il publisher. Insieme a hls_fragment 1, i margini sono zero.

**Sospetto**: 🟠 **MEDIO** — Contribuisce alla instabilità.

---

### 7. Dockerfile: fallback installation

**Commit**: `96870bc`

```dockerfile
RUN pipenv requirements > requirements.txt 2>/dev/null && \
     pip install --no-cache-dir -r requirements.txt || \
     pip install --no-cache-dir goprocam
```

**Impatto**: Se `Pipfile.lock` non esiste o `pipenv` fallisce, installa `goprocam`
senza version pin. Potrebbe installare una versione diversa con bug.

**Sospetto**: 🟡 **BASSO** — Meno probabile ma possibile.

---

### 8. Rimossi `allow publish` da nginx

```nginx
# PRIMA
allow publish 127.0.0.1;
allow publish 192.168.0.0/16;
allow publish 172.16.0.0/12;
allow publish 10.0.0.0/8;
deny publish all;

# DOPO
# (nessun filtro publish)
```

**Impatto**: Minimo per il crash, ma menosicuro. Qualsiasi processo può pushare a nginx.

**Sospetto**: 🟡 **BASSO** — Non causa crash, ma da valutare.

---

## Circolo Vizioso Identificato

```
FFmpeg ha micro-lag (I/O lento su OUYA)
    ↓
hls_fragment=1 genera molti file .ts
    ↓
nginx droppa publisher (drop_idle_publisher 10s)
    ↓
Socket RTMP non ESTABLISHED
    ↓
Supervisore _check_rtmp_socket() restituisce False
    ↓
Supervisore killa FFmpeg
    ↓
Supervisore riavvia FFmpeg
    ↓
GoPro streamma ancora → nuovo lag
    ↓
Ripete...
```

---

## Commit Coinvolti

| Commit | Data | Descrizione | Modifiche rilevanti |
|--------|------|-------------|---------------------|
| `42b0726` | 2025-07-05 | Stato iniziale (funzionante) | Script singolo, 1 container |
| `96870bc` | 2026-08-21 | Fase 1 — fix critici | KeepAlive, config centralizzata, Dockerfile, hls_fragment, nginx |
| `df0043b` | 2026-08-21 | Container Python | `network_mode: host`, docker-compose con 2 containers |
| `8caba40` | 2026-08-24 | Supervisore implementato | `_check_rtmp_socket()`, auto-recovery, multiprocessing |

---

## Raccomandazioni (solo analisi, da confermare prima di fix)

### Priorità 1 — Fix bug principale

- Rendere `_check_rtmp_socket()` meno aggressivo: aggiungere timeout + retry prima di killare
- Rimettere un delay dopo `_start_ffmpeg()` (almeno 5-10 secondi)
- Considerare di togliere `_check_gopro_streaming()` dal supervisore (può causare loop infiniti)

### Priorità 2 — Valutare `network_mode: host`

- Verificare se il container nginx-rtmp è anch'esso in `network_mode: host`
- Se sì, valutare se mantenere le porte mappate come prima (meno collisioni)
- Testare con `network_mode: bridge` + porte mappate

### Priorità 3 — Ottimizzare nginx

- Testare `hls_fragment 2` (compromesso tra latenza e stabilità)
- Valutare di rimettere 2 application (live + show) per isolare il drop_idle_publisher

### Priorità 4 — KeepAlive robusto

- Monitorare il processo keepalive nel supervisore
- Riavviare il keepalive se muore
- Usare threading invece di multiprocessing (meno overhead, stesso address space)

---

---

## Approfondimento: `network_mode: host` — Problema architetturale

### Contesto

Con `network_mode: host`, il container condivide la rete dell'host. Questo è necessario per:

1. **FFmpeg** → riceve UDP da `10.5.5.9:8554` (GoPro WiFi Direct)
2. **nginx proxy** → fa proxy HTTP a `10.5.5.9/gp/gpControl/...` (comandi GoPro)
3. **KeepAlive** → chiama `10.5.5.9` via HTTP

Il problema è che `10.5.5.9` è la rete **WiFi Direct** della GoPro, isolata dall'esterno. Qualsiasi container **bridge** non può raggiungerla.

### Le 5 opzioni analizzate

| # | Opzione | nginx proxy API | FFmpeg UDP | KeepAlive HTTP | Isolamento | Complessità |
|---|---------|----------------|------------|----------------|------------|-------------|
| 1 | Dashboard chiama GoPro direttamente | — | — | — | — | ❌ OctoPrint non è sulla WiFi Direct |
| 2 | Host solo nginx, bridge per goprostream | ✅ | ❌ | ❌ | 🟠 | Media |
| 3 | Due reti custom (`gopro-net` + `default`) | ✅ | ✅ | ✅ | ✅ | Alta (bridge WiFi Direct custom) |
| 4 | Host solo goprostream, bridge per nginx | ❌ | ✅ | ✅ | 🟠 | Media |
| 5 | Bridge + `extra_hosts` (host.docker.internal) | ✅ | ✅ | ❌ | ✅ | Bassa |

### Dettaglio per opzione

#### Opzione 1: Dashboard chiama GoPro direttamente

```
Browser → http://10.5.5.9/gp/gpControl/status
```

- ✅ Zero infrastruttura, semplice
- ❌ OctoPrint è su un LXC di Proxmox, **non** è sulla rete WiFi Direct. `10.5.5.9` non è raggiungibile.

#### Opzione 2: Host solo nginx, bridge per goprostream

```yaml
nginx-rtmp:
  network_mode: host          # proxy http://10.5.5.9 ✅

goprostream:
  # bridge (default)
```

- ✅ nginx può ancora fare proxy API
- ❌ FFmpeg nel bridge non raggiunge `10.5.5.9` per il UDP
- ❌ KeepAlive HTTP non funziona

#### Opzione 3: Due reti (`gopro-net` + `default`)

```yaml
networks:
  gopro-net:    # WiFi Direct access
  default:      # nginx ↔ goprostream

nginx-rtmp:
  networks: [default, gopro-net]

goprostream:
  networks: [default, gopro-net]
```

- ✅ Isolamento totale, nessun `host` mode
- ❌ Podman non supporta nativamente bridge connesso all'interfaccia WiFi Direct. Servirebbe un bridge custom con route verso `10.5.5.0/24`.
- ❌ Complessità alta, difficile da manutenere

#### Opzione 4: Host solo goprostream, bridge per nginx

```yaml
nginx-rtmp:
  ports: ["1935:1935", "8080:8080"]  # bridge

goprostream:
  network_mode: host  # FFmpeg → localhost:1935, UDP ← 10.5.5.9
```

- ✅ FFmpeg funziona, KeepAlive funziona
- ❌ Proxy API nginx non funziona (nginx in bridge, non raggiunge 10.5.5.9)
- Per ripristinare il proxy API: servirebbe un mini-server in goprostream (bottle/flask su porta 8081) → riabilita di fatto il container API

#### Opzione 5: Bridge + `extra_hosts` (host.docker.internal)

```yaml
goprostream:
  extra_hosts:
    - "host.docker.internal:host-gateway"
  # FFmpeg: rtmp://host.docker.internal:1935/live/gopro
```

- ✅ Isolamento, FFmpeg raggiunge nginx via host gateway
- ❌ KeepAlive HTTP (`/gp/gpControl/...`) non funziona (10.5.5.9 non raggiungibile)
- ❌ Restart stream GoPro non funziona
- Il keepalive e restart andrebbero gestiti fuori dal container

### Diagnosi: cosa richiede accesso a 10.5.5.9

| Componente | Protocollo | Scopo | Necessario? |
|------------|------------|-------|-------------|
| FFmpeg | UDP `10.5.5.9:8554` | Ricevere stream video | Sì, fondamentale |
| KeepAlive | HTTP `10.5.5.9/gp/gpControl/...` | Mantenere WiFi attivo | Sì, senza si disconnette |
| Restart stream | HTTP `10.5.5.9/gp/gpControl/execute` | Riavviare stream UDP | Utile per auto-recovery |
| Dashboard proxy | HTTP `10.5.5.9/gp/gpControl/status` | Status GoPro da browser | Utile ma non critico |

### Raccomandazione

Se l'obiettivo è **togliere `network_mode: host` da goprostream**:

1. **Usare l'opzione 5** (bridge + `extra_hosts`) per FFmpeg → nginx RTMP
2. **Spingere nginx a mantenere `network_mode: host`** per il proxy API
3. **Gestire KeepAlive e Restart stream** in uno di questi modi:
   - a) Script sul host che periodically chiama la GoPro
   - b) Il supervisore nginx (ma nginx non ha logica Python)
   - c) Un petit process sul host (es. `watchdog.sh` con curl)

### Trade-off finale

```
Prima:  2 containers, entrambi host mode, tutto funziona ma nessun isolamento
Dopo:   nginx host + goprostream bridge, isolamento parziale,
        keepalive/restart gestiti fuori dal container Python
```

Il vantaggio: goprostream è isolato, crash più contained, nessuna collisione di porta.
Il costo: logica keepalive spostata fuori dal container, maggiore complessità operativa.

---

---

## Approfondimento: FFmpeg e processi Zombie

### Contesto

FFmpeg è gestito via `subprocess.Popen` con `shell=True` e `preexec_fn=os.setsid`.
Il supervisore lo killa e riavvia periodicamente. Ogni restart potrebbe generare zombie
se il processo non viene correttamente ripulito.

### Ciclo di vita di FFmpeg

```
_start_ffmpeg()
    │
    ├── _kill_ffmpeg()           # killa il vecchio se presente
    ├── subprocess.Popen(
    │     shell=True,            # ← crea processo shell + FFmpeg
    │     preexec_fn=os.setsid   # ← nuova sessione di processo
    │   )
    └── time.sleep(1) + poll()   # verifica che sia partito

_kill_ffmpeg()
    │
    ├── poll() → se è morto, logga e basta
    ├── poll() → se è vivo:
    │     ├── os.killpg(SIGTERM)  # killa il GRUPPO di processi
    │     ├── wait(timeout=5)     # aspetta
    │     ├── se non muore: os.killpg(SIGKILL)
    │     │   └── MANCA wait() dopo SIGKILL ❌
    │     └── poll() per exit code
    └── self._ffmpeg = None
```

### Bug identificati

#### Bug 1: `shell=True` crea DUE processi, ne killa UNO

```python
self._ffmpeg = subprocess.Popen(
    "ffmpeg -y -f mpegts ...",
    shell=True,        # ← PROBLEMA
    preexec_fn=os.setsid,
)
```

Con `shell=True`:

```
Processo shell (PID 100)  →  Processo FFmpeg (PID 101)
       ↑                           ↑
  self._ffmpeg.pid            vero processo ffmpeg
```

- `self._ffmpeg.pid` = PID del **shell** (bash/sh), non di FFmpeg
- FFmpeg reale è un child del shell
- Se FFmpeg muore per primo, lo shell resta in vita come potenziale zombie
- `killpg()` uccide il gruppo (shell + FFmpeg), ma il timing non è garantito

#### Bug 2: `wait()` mancante dopo SIGKILL — PROBLEMA PRINCIPALE

```python
except subprocess.TimeoutExpired:
    try:
        os.killpg(os.getpgid(self._ffmpeg.pid), signal.SIGKILL)
    except ProcessLookupError:
        pass
    # ← MANCA self._ffmpeg.wait() DOPO SIGKILL
```

Dopo SIGKILL:
- Il processo è sicuramente morto
- Ma senza `wait()`, il Popen object non raccoglie il exit code
- Il processo rimane nello stato "defunct" (zombie) nella tabella processi
- `self._ffmpeg = None` dereferenza l'oggetto ma non fa `wait()`

**Sequenza che genera zombie:**
```
1. FFmpeg non risponde a SIGTERM in 5 secondi
2. Supervisore fa SIGKILL
3. Manca wait() dopo SIGKILL
4. Processo diventa zombie
5. _ffmpeg = None → dereferenza Popen
6. Zombie resta nella tabella processi
7. Dopo N restart, ci sono N zombie
8. Podman potrebbe killare il container per troppi processi
```

#### Bug 3: `shell=True` + FFmpeg che muore prima dello shell

Se FFmpeg crasha, lo shell (PID 100) resta in vita come zombie fino a quando:
- Il shell stesso termina (emula exit code di FFmpeg)
- Viene fatto `wait()` sul PID 100

Il `_kill_ffmpeg()` fa `self._ffmpeg.wait(timeout=5)` sul PID 100 (shell), quindi
normalmente lo ripulisce. Ma se il timeout scade, si applica il Bug 2.

#### Bug 4: `preexec_fn=os.setsid` + child interni di FFmpeg

`os.setsid()` crea una nuova sessione. FFmpeg potrebbe creare processi interni
(thread pool, subprocess) che non sono nel gruppo → non vengono uccisi da `killpg()`
→ possono diventare orfani.

Probabilità: bassa (FFmpeg di solito non crea subprocess).

### Riepilogo zombie

| # | Bug | Zombie? | Probabilità | Gravità |
|---|-----|---------|-------------|--------|
| 1 | `shell=True` crea 2 processi | Sì, se shell sopravvive | Media | 🟠 Medio |
| 2 | `wait()` mancante dopo SIGKILL | **Sì, sempre dopo timeout** | **Alta** | 🔴 **Alto** |
| 3 | Shell diventa zombie | Sì, se timeout scade | Media | 🟠 Medio |
| 4 | `os.setsid` + child interni | Possibile | Bassa | 🟡 Basso |

### Soluzione concettuale (da implementare)

1. **Rimuovere `shell=True`** — passare lista argomenti a Popen:
   ```python
   # PRIMA
   subprocess.Popen("ffmpeg -y -f mpegts ...", shell=True)
   # DOPO
   subprocess.Popen(["ffmpeg", "-y", "-f", "mpegts", ...])
   ```
   Elimina il processo shell intermedio. `self._ffmpeg.pid` è il PID di FFmpeg.

2. **Aggiungere `wait()` dopo SIGKILL**:
   ```python
   except subprocess.TimeoutExpired:
       try:
           os.killpg(os.getpgid(self._ffmpeg.pid), signal.SIGKILL)
       except ProcessLookupError:
           pass
       self._ffmpeg.wait()  # ← AGGIUNGERE
   ```

3. **Valutare se `os.setsid` è ancora necessario** senza `shell=True`.
   Se FFmpeg non crea processi figli, `os.setsid` serve solo per `killpg()`.
   Alternativa: usare `terminate()` sul singolo processo senza `os.setsid`.

4. **Aggiungere controllo zombie periodico** nel supervisore (opzionale):
   ```python
   import psutil
   def _check_zombies():
       for proc in psutil.process_iter(['pid', 'status']):
           if proc.info['status'] == 'zombie':
               log.warning("Zombie: PID %d", proc.info['pid'])
   ```

---

## File Coinvolti

- `python/goprostream.py` — Bridge streaming + supervisore
- `docker/docker-compose.yml` — Stack container
- `docker/nginx.conf` — Configurazione Nginx-RTMP
- `docker/Dockerfile.python` — Immagine Python con FFmpeg
- `.env` — Configurazione runtime

---

## Sintesi: Bug Diretti vs Rilassamento Sistema

Il crash del container non è causato da un singolo bug, ma dall'interazione di
**bug diretti** e **rilassamenti del sistema**.

### Bug diretti (🔧)

Sono le cause primarie del crash:

| Bug | Effetto |
|-----|--------|
| `network_mode: host` | Nessun isolamento di rete, collisioni, DNS non attendibile |
| `_check_rtmp_socket()` aggressivo | Uccide FFmpeg durante transient normali (riconnessioni, negoziazione TCP) |
| `wait()` mancante dopo SIGKILL | Zombie si accumulano ad ogni restart, podman potrebbe killare il container |

### Rilassamenti del sistema (⚙️)

Non causano il crash direttamente, ma rendono il sistema meno tollerante,
facilitando la manifestazione dei bug diretti:

| Rilassamento | Effetto |
|-------------|--------|
| `time.sleep(10)` rimosso | Supervisore giudica FFmpeg prima che sia stabilizzato |
| `hls_fragment 1` (era 3) | FFmpeg deve essere preciso al secondo, micro-lag = manca un fragment |
| KeepAlive in multiprocessing | Processo keepalive non monitorato, può morire senza che nessuno lo sappia |
| `drop_idle_publisher 10s` su unica app | Nginx droppa il publisher con lag > 10s, prima era isolato |

### Il circolo vizioso

```
Rilassamenti del sistema                    Bug diretti
                │                               │
                ▼                               ▼
    hls_fragment=1                    _check_rtmp_socket()
    sleep(10) rimosso                       │
    drop_idle_publisher                     │
    multiprocessing                         │
                │                               │
                └───────────┬───────────────────┘
                            │
                            ▼
                    FFmpeg muore
                            │
                            ▼
                    Supervisore restarta
                            │
                            ▼
                    wait() mancante → zombie
                            │
                            ▼
                    Dopo N restart → crash container
```

I rilassamenti creano le condizioni (transient, micro-lag, margini zero)
per cui i bug diretti si manifestano con maggiore frequenza e gravità.
In un sistema tolerance (con sleep(10), hls_fragment 3, drop_idle isolato),
i bug diretti esisterebbero ma sarebbero meno impactosi.

---

## Risultati post-fix (2026-08-29)

Dopo l'applicazione di tutti i fix, il sistema è stabile con le seguenti performance:

| Metrica | Valore |
|---------|--------|
| **Latenza stream** | **~8 secondi** |
| Zombie FFmpeg | 0 |
| Kill supervisore | 0 |
| Socket RTMP | ESTABLISHED |
| Stabilità | Nessun crash |

> **Nota latenza**: La latenza di ~8s è dovuta al pipeline completo:
> GoPro UDP → FFmpeg → RTMP → Nginx HLS → Browser.
> Con `hls_fragment 3` (era 1), il sistema è stabile con margine ampio.
> La latenza è accettabile per il monitoraggio remoto della stampante 3D.

---

## Stato

- [x] Analisi completata
- [x] Fix applicati (Fase 1+2+3: shell=True, wait(), keepalive monitor, supervisore)
- [x] Test su OUYA (confermato: zero zombie, nessun kill supervisore)
- [x] Conferma fix risolve il problema
- [x] Performance misurate: latenza ~8s, sistema stabile
