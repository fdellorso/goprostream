# Dashboard API Refactor — Handoff

> **Data:** 2026-08-22
> **Stato:** ✅ Completato

## Riepilogo

Semplificato l'architettura della Dashboard rimuovendo il server Python API intermedio e configurando nginx come proxy diretto verso la GoPro.

## Prima vs Dopo

### Prima
```
Browser → nginx (/api/) → Python API (bottle, porta 8081) → GoPro (10.5.5.9)
```

### Dopo
```
Browser → nginx (/api/) → GoPro (10.5.5.9)
```

## Perché la Modifica

- La GoPro è connessa all'OUYA via WiFi Direct (`10.5.5.9`)
- Il browser non può raggiungere direttamente la GoPro
- Nginx con `network_mode: host` può accedere alla rete WiFi Direct
- Il container Python era un layer inutile

## Modifiche Effettuate

### 1. `docker/docker-compose.yml`
- Commentato servizio `gopro-api`
- Il container Python non viene più avviato

### 2. `docker/nginx.conf`
Aggiunte due nuove location:

```nginx
# Proxy diretto status GoPro
location = /api/status {
  proxy_pass http://10.5.5.9/gp/gpControl/status;
  proxy_set_header Host 10.5.5.9;
}

# Proxy diretto comandi GoPro
location /api/cmd/ {
  rewrite ^/api/cmd/(.*)$ /gp/gpControl/$1 break;
  proxy_pass http://10.5.5.9;
  proxy_set_header Host 10.5.5.9;
}
```

La vecchia configurazione (`proxy_pass http://127.0.0.1:8081`) è commentata come backup.

### 3. `player/dashboard.html`
- Vecchia funzione `goproCmd` (POST + JSON) commentata
- Nuova funzione `goproCmd` (GET con path nell'URL)

**Prima:**
```javascript
xhr.open('POST', '/api/cmd', true);
xhr.send(JSON.stringify({path: path}));
```

**Dopo:**
```javascript
xhr.open('GET', '/api/cmd' + path, true);
xhr.send();
```

## File Non Modificati (mantenuti)

- `python/gopro_api.py` — Server bottle (non usato, ma nel repo)
- `python/Pipfile` — Dipendenza bottle aggiunta
- `docker/Dockerfile.python` — Copia gopro_api.py

## API Endpoints

| Endpoint | Metodo | Destinazione GoPro |
|----------|--------|-------------------|
| `/api/status` | GET | `http://10.5.5.9/gp/gpControl/status` |
| `/api/cmd/{path}` | GET | `http://10.5.5.9/gp/gpControl/{path}` |

## Container Attivi

| Container | Ruolo |
|-----------|-------|
| `nginx-rtmp` | Nginx-RTMP + proxy GoPro |
| `goprostream` | Bridge UDP→RTMP (FFmpeg) |

## Rollback

Per tornare alla configurazione precedente:

1. Decommentare `gopro-api` in `docker-compose.yml`
2. Decommentare location `/api/` in `nginx.conf`
3. Decommentare vecchia funzione `goproCmd` in `dashboard.html`
4. Riavviare: `podman-compose up -d --build`

## Test Eseguiti

```bash
# Status
curl http://localhost:8080/api/status → ✅ JSON GoPro

# Comando
curl http://localhost:8080/api/cmd/command/system/locate?p=1 → ✅ {}
```
