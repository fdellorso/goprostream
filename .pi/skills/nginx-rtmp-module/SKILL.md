# Skill: nginx-rtmp-module

> Guida di riferimento per la configurazione nginx-rtmp nel progetto GoPro Streaming.
> Basata sulla wiki ufficiale: https://github.com/arut/nginx-rtmp-module/wiki

## Quando usare questa skill

- Modifiche a `docker/nginx.conf`
- Troubleshooting streaming RTMP/HLS
- Ottimizzazione latenza e stabilità
- Aggiunta di nuove direttive nginx-rtmp

## Links rapidi

- [Direttive complete](#direttive-complete) — tutte le direttive con default ufficiali
- [HLS focus](#hls-focus) — approfondimento HLS per il nostro caso
- [La nostra config annotata](#la-nostra-config-annotata) — cosa usiamo e perché
- [Best practice](#best-practice) — cosa dice la wiki ufficiale
- [Fix consigliati](#fix-consigliati) — miglioramenti identificati

---

## Direttive complete

### Core

| Direttiva | Default | Noi | Note |
|-----------|---------|-----|------|
| `listen` | 1935 | ✅ 1935 | Porta standard RTMP |
| `chunk_size` | 4096 | 4000 | CPU overhead più basso con valori alti. 4000 va bene |
| `timeout` | 60s | — | Socket timeout, default va bene |
| `ping` | 60s | ❌ **Mancante** | Keepalive RTMP, consigliato 30s |
| `ping_timeout` | 30s | — | Timeout per ping |
| `max_streams` | 32 | — | Default OK per il nostro caso |

### Access

| Direttiva | Default | Noi | Note |
|-----------|---------|-----|------|
| `allow publish` | — | ❌ **Rimossa** | Best practice: `allow publish 127.0.0.1` |
| `deny publish` | — | ❌ **Rimossa** | Best practice: `deny publish all` |
| `allow play` | — | — | Possiamo usare `allow play all` |

### Live

| Direttiva | Default | Noi | Note |
|-----------|---------|-----|------|
| `live` | off | ✅ on | |
| `drop_idle_publisher` | off | 10s | Droppa publisher idle dopo 10s |
| `idle_streams` | on | — | **Consigliato**: `idle_streams off` per disconnettere subscriber quando il publisher muore |
| `sync` | 2ms | — | Default OK |
| `wait_key` | off | — | Utile per seeking |
| `wait_video` | off | — | Utile per IE (FAQ) |
| `interleave` | off | — | Unisce audio/video nello stesso chunk |
| `meta` | on | — | Default OK |

### HLS

| Direttiva | Default | Noi | Note |
|-----------|---------|-----|------|
| `hls` | off | ✅ on | |
| `hls_path` | — | ✅ `/mnt/hls/` | Directory per fragment |
| `hls_fragment` | **5s** | **1s** | ⚠️ Siamo 5x sotto il default |
| `hls_playlist_length` | **30s** | **3s** | ⚠️ Siamo 10x sotto il default |
| `hls_sync` | 2ms | ❌ **Mancante** | Consigliato: `hls_sync 100ms` per evitare crackling |
| `hls_cleanup` | on | — | Cancella fragment vecchi |
| `hls_continuous` | off | — | Per riconnessioni |
| `hls_nested` | off | — | Per multi-stream |
| `hls_fragment_naming` | sequential | — | Naming dei fragment |
| `hls_fragment_slicing` | plain | — | plain o aligned |

### Statistics

| Direttiva | Default | Noi | Note |
|-----------|---------|-----|------|
| `rtmp_stat` | — | ✅ all | Statistiche RTMP |
| `rtmp_stat_stylesheet` | — | ✅ stat.xsl | Style XML |

### Multi-worker

| Direttiva | Default | Noi | Note |
|-----------|---------|-----|------|
| `rtmp_auto_push` | off | — | Serve se `worker_processes > 1` |

---

## HLS Focus

### Il nostro caso

```
GoPro (UDP 8554) → FFmpeg → RTMP (localhost:1935) → nginx → HLS → OctoPrint
```

Latenza reale misurata: **5-6 secondi** con `hls_fragment 1`.

### Default ufficiale vs noi

```
hls_fragment:        default 5s    → noi 1s   (15x più aggressivo)
hls_playlist_length: default 30s   → noi 3s   (10x più aggressivo)
```

### Perché la latenza è 5-6s nonostante hls_fragment 1

La latenza HLS è determinata da:
1. `hls_fragment` (1s) — quanto è lungo ogni chunk
2. Buffer FFmpeg — FFmpeg bufferizza prima di pushare
3. Buffer nginx — nginx processa il flusso RTMP
4. Jitter GoPro — la GoPro non manda pacchetti perfettamente regolari
5. Download del player — il player deve scaricare almeno 2-3 fragment

Con `hls_fragment 1`, il limiting factor non è il fragment ma il buffer FFmpeg + jitter GoPro.

### Quando hls_fragment basso ha senso

- Connessione UDP stabile e veloce
- FFmpeg senza buffer (usando `-fflags nobuffer -flags low_delay`)
- Player con buffer minimo
- Server con I/O veloce

### Quando hls_fragment alto ha senso

- I/O lento (come OUYA con flash)
- WiFi instabile
- Stream continuity più importante della latenza
- Player con buffer generoso

### hls_sync — mancante nel nostro caso

```nginx
hls_sync 100ms;
```

Previene crackling noise dopo conversione da RTMP (1KHz) a MPEG-TS (90KHz). Consigliato dalla wiki ufficiale. Noi non lo usiamo.

### hls_cleanup — default on

Cancella automaticamente i fragment vecchi dalla playlist. Default OK per noi.

---

## La nostra config annotata

```nginx
# ─── RTMP ─────────────────────────────────────────────────
rtmp {
  server {
    listen 1935;          # ✅ Porta standard
    chunk_size 4000;      # ✅ OK (default 4096)

    application live {
      live on;             # ✅ Abilita live streaming
      drop_idle_publisher 10s;  # ⚠️ Droppa publisher idle (default off)
      hls on;              # ✅ Abilita HLS
      hls_fragment 1;      # 🔴 1s (default 5s) — troppo aggressivo
      hls_playlist_length 3;   # 🔴 3s (default 30s) — troppo corto
      hls_path /mnt/hls/;  # ✅ Directory fragment
      # MANCA: hls_sync 100ms;
      # MANCA: allow publish 127.0.0.1;
      # MANCA: deny publish all;
      # MANCA: idle_streams off;
    }

    application stat {
      live on;
      allow 127.0.0.1;    # ✅ Solo locale
      deny all;
    }
  }
}

# ─── HTTP ─────────────────────────────────────────────────
http {
  # ... server config ...
  # ✅ /hls location con CORS e no-cache
  # ✅ /stat per statistiche RTMP
  # ✅ /api/ proxy diretto a GoPro
}
```

---

## Best practice

### Dalla wiki ufficiale

1. **Sicurezza**: `allow publish 127.0.0.1; deny publish all;`
2. **Keepalive RTMP**: `ping 30s;`
3. **HLS sync**: `hls_sync 100ms;`
4. **Subscriber idle**: `idle_streams off;`
5. **Multi-worker**: `rtmp_auto_push on;` se `worker_processes > 1`

### Esempio ufficiale commentato

```nginx
rtmp {
    server {
        listen 1935;
        ping 30s;           # Keepalive RTMP ogni 30s

        application live {
            live on;

            # Sicurezza
            allow publish 127.0.0.1;
            deny publish all;

            # HLS
            hls on;
            hls_path /tmp/hls;
            hls_fragment 5s;        # Default: 5s
            hls_playlist_length 30s; # Default: 30s
            hls_sync 100ms;         # Evita crackling

            # Stabilità
            idle_streams off;        # Disconnetti subscriber quando publisher muore
            drop_idle_publisher 30s; # Droppa publisher idle dopo 30s
        }
    }
}
```

### FAQ dalla wiki

- **IE si blocca dopo qualche secondo**: aggiungere `wait_video on;`
- **HLS non funziona con pull**: HLS non triggera eventi, usare `exec_static` o `pull ... static`
- **Stream sparisce da stats con più worker**: usare `rtmp_auto_push on;`
- **FLV registrati non seekabili**: aggiungere metadata con `exec_record_done yamdi -i $path -o /var/videos/$basename;`

---

## Fix consigliati

Basati sul confronto tra la nostra config e le best practice ufficiali:

### Priorità 1 — Sicurezza

```nginx
# AGGIUNGERE:
application live {
    allow publish 127.0.0.1;
    deny publish all;
}
```

### Priorità 2 — Stabilità HLS

```nginx
# CAMBIARE:
hls_fragment 1;        →  hls_fragment 3;    # o 5 (default)
hls_playlist_length 3; →  hls_playlist_length 10;  # o 30 (default)

# AGGIUNGERE:
hls_sync 100ms;
idle_streams off;
```

### Priorità 3 — Keepalive RTMP

```nginx
# AGGIUNGERE a server{}:
ping 30s;
```

### Priorità 4 — Debug

```nginx
# Per troubleshooting:
error_log /var/log/nginx/error.log debug;  # (solo temporaneo)
```

---

## Control module

nginx-rtmp espone un HTTP control module:

```nginx
http {
    server {
        location /control {
            rtmp_control all;
        }
    }
}
```

API disponibili:
- `GET /control/record/start?app=APP&name=NAME&rec=REC` — avvia recording
- `GET /control/record/stop?app=APP&name=NAME&rec=REC` — ferma recording
- `GET /control/drop/publisher?app=APP&name=NAME` — droppa publisher
- `GET /control/drop/client?app=APP&name=NAME&addr=ADDR` — droppa client

---

## Debug log

Per troubleshooting dettagliato:

1. Compilare nginx con `--with-debug`
2. In nginx.conf: `error_log /var/log/nginx/error.log debug;`
3. Greppare per il problema: `grep "exec\|notify\|hls" /var/log/nginx/error.log`

---

## Docker

Image Alpine ufficiale:

```dockerfile
FROM alpine:3.13.4 as builder
RUN apk add --update build-base git bash gcc make g++ zlib-dev linux-headers pcre-dev openssl-dev
RUN git clone https://github.com/arut/nginx-rtmp-module.git && \
    git clone https://github.com/nginx/nginx.git
RUN cd nginx && ./auto/configure --add-module=../nginx-rtmp-module && make && make install

FROM alpine:3.13.4 as nginx
RUN apk add --update pcre ffmpeg
COPY --from=builder /usr/local/nginx /usr/local/nginx
ENTRYPOINT ["/usr/local/nginx/sbin/nginx"]
CMD ["-g", "daemon off;"]
```

Noi usiamo `vallahaye/nginx-rtmp:stable-alpine` (pre-compilato).

---

## Note per il progetto

### Perché hls_fragment 1 non funziona

Abbiamo verificato empiricamente che la latenza reale è 5-6s nonostante `hls_fragment 1`.
Il limiting factor è il buffer FFmpeg + jitter GoPro, non il fragment size.
La modifica ha introdotto I/O stress su OUYA senza beneficio in latenza.

### Circolo vizioso con hls_fragment 1

```
hls_fragment=1 → FFmpeg deve essere preciso al secondo
→ micro-lag = manca un fragment
→ nginx droppa publisher (drop_idle_publisher 10s)
→ supervisore killa FFmpeg
→ restart → nuovo lag → ripete
```

### Il nostro container usa network_mode: host

Questo significa che nginx vede la stessa rete dell'host.
Il proxy API (`/api/`) funziona perché raggiunge `10.5.5.9` direttamente.
