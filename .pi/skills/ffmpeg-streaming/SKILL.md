---
name: ffmpeg-streaming
description: Gestione del flusso video con FFmpeg: conversione UDP->RTMP, diagnostica stream, test di connettivita con la GoPro. Usa quando serve verificare, testare o modificare il pipeline di streaming.
---

# FFmpeg Streaming Skill

Gestione del flusso video tra GoPro e Nginx-RTMP.

## Pipeline di Streaming

```
GoPro (UDP:8554) → FFmpeg → RTMP (localhost:1935) → Nginx-RTMP → HLS (:8080)
```

## Comandi FFmpeg

### Avvia bridge (come nel progetto)

```bash
ffmpeg -f mpegts -i udp://10.5.5.9:8554 \
  -c copy -an -f flv \
  rtmp://localhost:1935/live/gopro
```

### Parametri chiave

| Parametro | Significato |
|-----------|-------------|
| `-f mpegts` | Formato input: MPEG Transport Stream |
| `-i udp://10.5.5.9:8554` | Input: flusso UDP dalla GoPro |
| `-c copy` | Copia codec senza transcodifica |
| `-an` | Rimuovi audio |
| `-f flv` | Formato output: Flash Video (per RTMP) |
| `rtmp://localhost:1935/live/gopro` | Destinazione RTMP |

### Test flusso con ffplay (bassa latenza)

```bash
ffplay -fflags nobuffer -f mpegts udp://10.5.5.9:8554
```

### Test output RTMP

```bash
ffplay -fflags nobuffer rtmp://localhost:1935/live/gopro
```

## Diagnostica

### Verifica che la GoPro stia mandando dati

```bash
# Test ricezione UDP (Ctrl+C per fermare)
timeout 5 ffmpeg -i udp://10.5.5.9:8554 -f null - 2>&1 | grep -E 'Stream|bitrate'
```

### Verifica che FFmpeg stia mandando a RTMP

```bash
# Controlla processi FFmpeg attivi
ps aux | grep ffmpeg

# Log dettagliato FFmpeg
ffmpeg -loglevel verbose -f mpegts -i udp://10.5.5.9:8554 \
  -c copy -an -f flv rtmp://localhost:1935/live/gopro
```

### Verifica connessione con GoPro

```bash
# Ping alla GoPro
ping -c 3 10.5.5.9

# Test API HTTP
curl -s http://10.5.5.9/gp/gpControl/status | head -20
```

## Note per ARMv7l (OUYA)

- Con `-c copy` non serve trascodifica, la CPU è risparmiata
- Il buffer UDP può essere regolato con `-probesize` e `-analyzeduration`
- Per bassa latenza: `-fflags nobuffer` su ffplay, `-flags low_delay` su ffmpeg

## Troubleshooting

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| "Connection refused" su RTMP | Nginx-RTMP non avviato | `podman-compose up -d` |
| Stream vuoto/nero | GoPro non in streaming | Verificare `gopro.livestream("start")` |
| "No such device" | GoPro non connessa WiFi | Controllare connessione WiFi Direct |
| Audio nel flusso | FFmpeg non scarta audio | Aggiungere `-an` |
| Buffering nel player | Fragment HLS troppo grandi | Ridurre `hls_fragment` in nginx.conf |
