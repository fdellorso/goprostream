# Handoff — Debug Crash Container goprostream

## Contesto

- **Branch**: main
- **Comando**: Debug completo del crash periodico del container goprostream
- **Durata**: ~4 ore (23/08/2026 20:00 - 24/08/2026 00:30)

## Cosa fatto

### 1. Aggiunta logging a goprostream.py
- TP1: Log exit code FFmpeg
- TP2: Log stderr FFmpeg
- TP3: Check UDP GoPro
- TP4: Monitoraggio processo (heartbeat 60s)
- TP5: Check status GoPro (API HTTP)
- TP6: Check HLS endpoint + RTMP stat

### 2. Creato script watch-stream.sh
- Monitoraggio continuo ogni 30s
- Container stats, GoPro, nginx, HLS, file system

### 3. Implementato supervisore con auto-recovery
- Check socket RTMP (ESTABLISHED vs FIN_WAIT_2)
- Check GoPro streaming
- Kill + restart automatico FFmpeg
- Restart stream GoPro

### 4. Aggiunto logging nginx RTMP
- `error_log info;` in nginx.conf
- `location /stat` per statistiche RTMP

### 5. tcpdump captures
- UDP GoPro: 16.537 pacchetti, 0 gap (confermato continuo)
- WiFi KeepAlive: 33 pacchetti, ogni 2.5s (confermato perfetto)
- RTMP TCP: FIN da FFmpeg ogni 60s (confermato: FFmpeg chiude)

## Causa identificata

**FFmpeg chiude la connessione RTMP dopo ~50 secondi di publish.**

Confermato da:
- Log nginx: `disconnect` ogni 60s
- tcpdump: FIN da FFmpeg (non da nginx)
- Socket: passa da ESTABLISHED a FIN_WAIT_2

**Non è:**
- GoPro (UDP continuo)
- WiFi (KeepAlive perfetto)
- nginx (non chiude lui)
- drop_idle_publisher (timeout a 10s, non 60s)

## Fix implementato

Supervisore con auto-recovery: il sistema si ripara da solo in ~2 secondi.
Il crash continua ogni 60s ma lo stream si ripristina automaticamente.

## Da fare

- [ ] Capire perché FFmpeg chiude dopo ~50s
- [ ] Testare opzioni FFmpeg per risolvere
- [ ] Implementare fix definitivo

## File modificati

```
python/goprostream.py    — supervisore + auto-recovery
docker/nginx.conf        — log info + /stat
scripts/watch-stream.sh  — monitoraggio esterno
docs/debug-crash-container.md — report completo
```

## Note per prossimo agente

- Il report completo è in `docs/debug-crash-container.md`
- I container sono FERMI (fermati per pulizia)
- I file di capture sono in /tmp/ (udp_capture.pcap, rtmp_capture.pcap)
- Il problema è che FFmpeg chiude il socket RTMP dopo ~50s
- Il supervisore gestisce il recovery ma non risolve la causa
