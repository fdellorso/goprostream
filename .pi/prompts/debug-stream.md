---
description: Diagnostica problemi di streaming GoPro → OctoPrint
---
Diagnostica il flusso di streaming controllando ogni componente in ordine:

1. **GoPro**: Ping 10.5.5.9, verifica API HTTP (`/gp/gpControl/status`)
2. **WiFi**: Verifica connessione alla rete GoPro dall'OUYA
3. **FFmpeg**: Controlla se il processo è attivo, verifica log
4. **Nginx-RTMP**: `podman-compose logs nginx-rtmp`, verifica porte 1935 e 8080
5. **HLS**: Test endpoint `http://localhost:8080/hls/gopro.m3u8`
6. **OctoPrint**: Verifica che l'URL Classic Webcam sia corretto

Usa `npx pyright` per verificare il codice Python dopo eventuali modifiche.
