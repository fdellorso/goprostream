# Architecture - GoPro Streaming Server

## Architettura del Sistema

Il progetto implementa un **video streaming bridge** tra una GoPro Hero 4 Black e OctoPrint.

### Componenti

```
GoPro Hero 4 Black ──WiFi Direct──► OUYA (ARMv7l)
                                         │
                                    ┌────┴────┐
                                    │ FFmpeg  │
                                    │UDP→RTMP │
                                    └────┬────┘
                                         │ RTMP :1935
                                    ┌────┴────────┐
                                    │ Nginx-RTMP  │
                                    │ (Podman)    │
                                    │ HLS :8080   │
                                    └────┬────────┘
                                         │ HTTP HLS
                                    ┌────┴────────┐
                                    │  OctoPrint  │
                                    │  (LXC)      │
                                    │  Classic    │
                                    │  Webcam     │
                                    └─────────────┘
```

### Archivio Componenti

#### 1. GoPro Interface (`goprostream.py`, `goprophoto.py`)

- **Libreria**: `goprocam` (gopro-py-api)
- **Protocollo**: HTTP REST API su `http://10.5.5.9/gp/gpControl/`
- **Funzioni**:
  - Avvio/fermo streaming
  - Controllo fotocamera (foto, video, modalità)
  - KeepAlive per mantenere attivo il WiFi
  - Spegnimento remoto

#### 2. FFmpeg Bridge

- **Input**: MPEG-TS over UDP da `udp://10.5.5.9:8554`
- **Output**: FLV over RTMP verso `rtmp://localhost:1935/live/gopro`
- **Parametri**: `-c copy` (copy codec, nessuna transcodifica) `-an` (no audio)
- **Note**: Usa `nobuffer` per bassa latenza se si usa ffplay

#### 3. Nginx-RTMP (Container Podman)

- **Image**: `vallahaye/nginx-rtmp:stable-alpine`
- **Porte esposte**:
  - `1935` - RTMP input
  - `8080` - HTTP (HLS/DASH fragments + player HTML)
- **Configurazioni chiave**:
  - App `live`: riceve RTMP, push a `show`
  - App `show`: genera HLS (fragment 3s, playlist 10s) e DASH
  - CORS abilitato per HLS e DASH
  - Publish limitato a reti private (10.x, 172.16.x, 192.168.x)

#### 4. OctoPrint Integration

- **Plugin**: Classic Webcam (integrato da v1.9.0)
- **URL Stream**: `http://<ouya_ip>:8080/hls/gopro.m3u8`
- **Formato**: HLS (HTTP Live Streaming)
- **Note**: Iframe plugin disabilitato, Classic Webcam è la scelta attiva

## Scelte Architetturali

### Perché Podman e non Docker?
- Il sistema è un server Proxmox con container LXC
- Podman è più leggero e rootless-friendly
- Compatibile con docker-compose files esistenti

### Perché HLS e non RTMP diretto?
- OctoPrint non supporta nativamente RTMP
- HLS è supportato nativamente dai browser (via hls.js)
- Permette di servire lo stream su porta HTTP standard

### Perché FFmpeg con `-c copy`?
- Nessuna transcodifica = bassa latenza
- Minimo uso di CPU sull'OUYA (Tegra 3 è limitato)
- La Goproduce già in H.264 compatibile

### Perché Classic Webcam e non Iframe?
- Classic Webcam è il plugin ufficiale OctoPrint (v1.9.0+)
- Gestisce nativamente URL HLS
- Meno configurazione,更好 integrazione con l'UI

## Sicurezza

- La rete WiFi della GoPro è isolata (WiFi Direct)
- Nginx limita la publicazione a reti private
- Nessuna autenticazione sullo stream HLS (è in rete locale)
- OctoPrint ha la sua autenticazione

## Reference Documentation (Le Nostre Skill)

La cartella `docs/references/` contiene la documentazione completa delle API GoPro Hero 4, scaricata e archiviata localmente. Queste **sono le nostre skill** per il progetto — non serve andare sui siti web esterni.

| File | Contenuto |
|------|----------|
| `goprowifihack.md` | Indice del repository, link diretti, repo correlati |
| `gopro-py-api.md` | Libreria goprocam: installazione, API, compatibilità |
| `hero4-livestreaming.md` | Guida streaming UDP, FFmpeg, parametri bitrate |
| `hero4-commands.md` | **TUTTI** i comandi WiFi: video, photo, multiShot, protune, sistema |
| `hero4-status.md` | Significato di ogni campo del JSON status |

> **Nota per l'agente**: Quando devi lavorare sui comandi GoPro, consulta PRIMA i file in `docs/references/` prima di cercare online. Il contenuto è già scaricato e ottimizzato per il nostro device (Hero4 Black).

## Dipendenze

### Python
- `goprocam` (gopro-py-api) - Controllo GoPro
- `ffmpeg` - Conversione stream (sistema)

### Container
- `nginx-rtmp` - Media server

### Browser
- `hls.js` - Player HLS (CDN)
- `video.js` - Player alternativo (CDN)
