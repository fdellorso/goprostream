---
name: podman
description: Gestione container e stack Podman/podman-compose per il deploy del media server nginx-rtmp. Usa quando serve avviare, fermare, verificare o modificare i container del progetto.
---

# Podman Skill

Gestione container Podman per il progetto goprostream.

## Stack del progetto

Il file `docker-compose.yml` (compatibile podman-compose) definisce il servizio nginx-rtmp.

## Comandi principali

```bash
# Avvia lo stack
podman-compose -f docker/docker-compose.yml up -d

# Ferma lo stack
podman-compose -f docker/docker-compose.yml down

# Status container
podman-compose -f docker/docker-compose.yml ps

# Log nginx-rtmp
podman-compose -f docker/docker-compose.yml logs -f nginx-rtmp

# Riavvia
podman-compose -f docker/docker-compose.yml restart

# Build/ricostruisci
podman-compose -f docker/docker-compose.yml up -d --force-recreate
```

## Verifica salute servizi

```bash
# Controlla che nginx-rtmp sia in ascolto
podman exec nginx-rtmp ss -tlnp | grep -E '1935|8080'

# Test HLS endpoint
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/hls/gopro.m3u8

# Test DASH endpoint
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/dash/gopro.mpd
```

## Diagnostica

```bash
# Log errori
podman-compose -f docker/docker-compose.yml logs --tail=50 nginx-rtmp

# Verifica spazio disco (HLS fragments)
podman exec nginx-rtmp df -h /mnt/hls

# Verifica processi interni
podman exec nginx-rtmp ps aux | grep nginx
```

## Note

- Il container espone le porte `1935` (RTMP) e `8080` (HTTP)
- I file di configurazione sono montati da `./nginx.conf` e `./videojs.html`, `./hlsjs.html`
- I frammenti HLS vanno in `/mnt/hls/` dentro il container
- Podman-compose è installato nel sistema (v1.5.0)
