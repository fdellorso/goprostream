# Setup OctoPrint — GoPro Streaming

## Prerequisiti

- OctoPrint 1.9.0+ (con Classic Webcam integrato)
- L'OUYA con nginx-rtmp in esecuzione
- Rete comune tra OctoPrint e OUYA (o accesso alla porta 8080)

## Classificazione Webcam

OctoPrint 1.9.0+ include il plugin **Classic Webcam** di default.
Non serve installare nulla — va solo configurato.

> **Nota**: Il plugin Iframe (`OctoPrint-WebcamIframe`) è stato disabilitato in favore di Classic Webcam.

## Configurazione

1. Apri la WebUI di OctoPrint: `http://<octoprint_ip>:5000`
2. Vai su **Settings** (ingranaggio) → **Classic Webcam**
3. Configura:

| Campo | Valore |
|-------|--------|
| **Stream URL** | `http://<ouya_ip>:8080/hls/gopro.m3u8` |
| **Snapshot URL** | *(lascia vuoto)* |
| **Stream Aspect Ratio** | `16:9` |
| **Stream Rotation** | `0` |
| **Flip Horizontally** | `false` |
| **Flip Vertically** | `false` |
| **MJPEG Alignment** | `Left` |
| **Aspect Ratio** | `16:9` |
| **Flip Horizontally** | `false` |
| **Flip Vertically** | `false` |

4. Salva

## Verifica

1. Avvia lo streaming: `./start.sh`
2. Apri OctoPrint → dovresti vedere il video nella sidebar
3. Se non si vede:
   - Verifica che l'URL sia raggiungibile
   - Controlla che il formato sia HLS (m3u8)
   - Apri la console del browser per errori CORS

## Configurazione HTTPS

Se OctoPrint è servito su HTTPS, usa la porta 8443:

| Campo | Valore
|-------|--------|
| **Stream URL** | `https://ouya.fritz.box:8443/hls/gopro.m3u8` |
| **Snapshot URL** | *(lascia vuoto)* |

### Note SSL

- nginx gira su porta 8443 con certificati Let's Encrypt/step-ca
- La porta 8080 resta disponibile per HTTP (redirect)
- Il certificato viene rinnovato automaticamente via cron (giornaliero)

### Rinnovo certificati

```bash
# Verifica scadenza certificati
openssl x509 -in /etc/letsencrypt/live/ouya.fritz.box/fullchain.pem -noout -dates

# Rinnovo manuale
sudo certbot renew

# Cron job (già configurato)
cat /etc/cron.d/certbot-renew
```

## Troubleshooting

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| Video non visibile | URL errato | Verifica URL nel settings OctoPrint |
| "Not playing" | Stream non attivo | Avvia streaming con `./start.sh` |
| Errore CORS | Nginx non configura CORS | Verifica `nginx.conf` |
| Video scattoso | Frammenti troppo grandi | Riduci `hls_fragment` in nginx.conf |
| Audio attivo | Browser non ha autoplay | Il player è muted di default |

## Rete

Se OctoPrint e OUYA sono su reti diverse (es. OUYA su WiFi Direct GoPro, OctoPrint su LAN):

```
GoPro ←WiFi Direct→ OUYA ←HTTP→ Router ←HTTP→ Proxmox LXC (OctoPrint)
```

In questo caso, assicurati che:
- OUYA abbia anche una connessione alla rete LAN (o un routing)
- La porta 8080 sia raggiungibile da OctoPrint
- In alternativa, configura un reverse proxy o un tunnel
