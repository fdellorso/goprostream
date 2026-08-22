# HERO4 Livestreaming — Guida Completa

> **Source**: https://github.com/KonradIT/goprowifihack/blob/master/HERO4/Livestreaming.md
> **Applicabile a**: HERO4 Black, HERO4 Silver
> **Nota Session**: La HERO4 Session ha procedure diverse (vedere HERO4-Session.md)

## Come Funziona

1. La GoPro avvia un server UDP interno
2. L'applicazione client si connette al flusso UDP
3. Il flusso è in MPEG-TS (MPEG Transport Stream)
4. La GoPro manda continuamente dati, il client deve essere pronto a ricevere

## Avvio Streaming

### Step 1: Avvia il flusso UDP

```bash
# Via HTTP API (GET request)
curl "http://10.5.5.9/gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart"
```

### Step 2: Ricevi il flusso UDP

```bash
# URL del flusso
udp://10.5.5.9:8554
```

### Step 3: Visualizza il flusso

```bash
# Con ffplay (bassa latenza)
ffplay -fflags nobuffer -f mpegts udp://10.5.5.9:8554
```

## Pipeline FFmpeg Completo

### Per il nostro progetto (UDP → RTMP)

```bash
# Copia codec, nessuna transcodifica (bassa latenza, basso uso CPU)
ffmpeg -f mpegts -i udp://10.5.5.9:8554 \
  -c copy -an \
  -f flv rtmp://localhost:1935/live/gopro
```

### Parametri FFmpeg Spiegati

| Parametro | Significato |
|-----------|-------------|
| `-f mpegts` | Formato input: MPEG Transport Stream ( formato nativo UDP GoPro) |
| `-i udp://10.5.5.9:8554` | Input: flusso UDP dalla GoPro |
| `-c copy` | Copia codec senza transcodifica (H.264 rimane H.264) |
| `-an` | Rimuovi traccia audio dal flusso |
| `-f flv` | Formato output: Flash Video (necessario per RTMP) |
| `rtmp://localhost:1935/live/gopro` | Destinazione: Nginx-RTMP locale |

### Opzioni Aggiuntive FFmpeg

```bash
# Bassa latenza aggiuntiva
ffmpeg -fflags nobuffer -flags low_delay \
  -f mpegts -i udp://10.5.5.9:8554 \
  -c copy -an \
  -f flv rtmp://localhost:1935/live/gopro

# Con probesize ridotto (start più veloce)
ffmpeg -probesize 32 -analyzeduration 0 \
  -f mpegts -i udp://10.5.5.9:8554 \
  -c copy -an \
  -f flv rtmp://localhost:1935/live/gopro
```

## Parametri di Streaming (Setting ID 162)

La GoPro permette di configurare bitrate e qualità dello stream.

### Risoluzioni e Bitrate

| Valore | Risoluzione | FPS | Bitrate | ID |
|--------|------------|-----|---------|-----|
| 0 | 480p | 25fps | 250 Kbps | `http://10.5.5.9/gp/gpControl/setting/162/0` |
| 1 | 480p | 25fps | 600 Kbps | `http://10.5.5.9/gp/gpControl/setting/162/1` |
| 2 | 480p | 25fps | 1 Mbps | `http://10.5.5.9/gp/gpControl/setting/162/2` |
| 3 | 720p | 25fps | 1 Mbps | `http://10.5.5.9/gp/gpControl/setting/162/3` |
| 4 | 720p | 25fps | 2.5 Mbps | `http://10.5.5.9/gp/gpControl/setting/162/4` |
| 5 | 720p | 25fps | 4 Mbps | `http://10.5.5.9/gp/gpControl/setting/162/5` |

### Consigli per il Nostro Progetto

- **720p 2.5Mbps (valore 4)**: Buon compromesso qualità/banda
- **720p 4Mbps (valore 5)**: Migliore qualità, richiede WiFi stabile
- **480p 1Mbps (valore 2)**: Più stabile, qualità ridotta

## Streaming BitRate (Setting ID 62)

Supporta valori custom, limitati dal throughput WiFi. Usare il parametro 62 (non 162 per il bitrate custom).

```bash
# Esempi di bitrate custom
http://10.5.5.9/gp/gpControl/setting/62/250000    # 250 Kbps
http://10.5.5.9/gp/gpControl/setting/62/1000000   # 1 Mbps
http://10.5.5.9/gp/gpControl/setting/62/2000000   # 2 Mbps
http://10.5.5.9/gp/gpControl/setting/62/4000000   # 4 Mbps
http://10.5.5.9/gp/gpControl/setting/62/7000000   # 7 Mbps
```

## Stream Window Size (Setting ID 64)

Dimensione della finestra di streaming:

| Valore | Risoluzione | URL |
|--------|------------|-----|
| 0 | Default | `http://10.5.5.9/gp/gpControl/setting/64/0` |
| 1 | 240p | `http://10.5.5.9/gp/gpControl/setting/64/1` |
| 4 | 480p | `http://10.5.5.9/gp/gpControl/setting/64/4` |
| 7 | 720p (1280x720) | `http://10.5.5.9/gp/gpControl/setting/64/7` |
| 8 | 720p 3:4 (960x720) | `http://10.5.5.9/gp/gpControl/setting/64/8` |
| 9 | 720p 1:2 (640x720) | `http://10.5.5.9/gp/gpControl/setting/64/9` |

## Parametri Protune per Streaming

```bash
# Protune ON/OFF (influenza qualità stream)
http://10.5.5.9/gp/gpControl/setting/10/1   # Protune ON
http://10.5.5.9/gp/gpControl/setting/10/0   # Protune OFF

# White Balance
http://10.5.5.9/gp/gpControl/setting/11/0   # Auto
http://10.5.5.9/gp/gpControl/setting/11/2   # 5500K (daylight)

# Color
http://10.5.5.9/gp/gpControl/setting/12/0   # GoPro Color
http://10.5.5.9/gp/gpControl/setting/12/1   # Flat

# ISO Limit
http://10.5.5.9/gp/gpControl/setting/13/0   # 6400
http://10.5.5.9/gp/gpControl/setting/13/4   # 800
http://10.5.5.9/gp/gpControl/setting/13/8   # 100

# Sharpness
http://10.5.5.9/gp/gpControl/setting/14/0   # High
http://10.5.5.9/gp/gpControl/setting/14/1   # Medium
http://10.5.5.9/gp/gpControl/setting/14/2   # Low

# EV Compensation
http://10.5.5.9/gp/gpControl/setting/15/4   # 0.0 (nessuna compensazione)
http://10.5.5.9/gp/gpControl/setting/15/0   # +2.0
http://10.5.5.9/gp/gpControl/setting/15/8   # -2.0
```

## Note Importanti

1. **UDP vs TCP**: Il flusso è UDP, può perdere pacchetti con WiFi instabile
2. **KeepAlive**: Dopo 10 secondi è necessario inviare KeepAlive per mantenere attivo lo streaming. La libreria `goprocam` gestisce questo con `gopro.KeepAlive()`
3. **Latenza**: Con `-c copy` la latenza è minima (~1-2 secondi)
4. **Risoluzione**: Per streaming stabile consigliato 720p max
5. **Audio**: Il flusso UDP include audio, FFmpeg con `-an` lo scarta
6. **WiFi Direct**: La GoPro crea una rete isolata, non è sulla rete locale
7. **Raggio**: La connessione WiFi Direct ha raggio limitato (~10-15 metri)
8. **Interferenze**: Il 2.4GHz è soggetto a interferenze da altri dispositivi WiFi

## Troubleshooting

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| Stream vuoto | GoPro non in streaming | Verificare `gopro.livestream("start")` |
| "Connection refused" | FFmpeg non riesce a connettersi UDP | Controllare che la GoPro sia connessa e il WiFi attivo |
| Stream interrotto | KeepAlive non inviato | Assicurarsi di chiamare `gopro.KeepAlive()` ogni ~10s |
| Buffering nel player | Fragment HLS troppo grandi | Ridurre `hls_fragment` in nginx.conf |
| Pixelazione | Bitrate troppo alto per la banda | Ridurre bitrate (setting 162 o 62) |
| Ritardo elevato | Buffer FFmpeg troppo grande | Aggiungere `-fflags nobuffer -flags low_delay` |
