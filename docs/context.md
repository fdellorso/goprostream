# Context - GoPro Streaming Server

## Overview

Progetto di **live streaming da GoPro Hero 4 Black** verso OctoPrint, un bridge che converte il flusso video UDP della GoPro in un flusso HLS visualizzabile nell'interfaccia web di OctoPrint.

## Device

### GoPro Hero 4 Black
- **Rete WiFi**: Crea una rete WiFi Direct (Access Point) con SSID `GOPRO-BP-XXXX`
- **IP Gateway**: `10.5.5.9` (default GoPro)
- **Subnet**: `255.255.255.0`
- **Range IP**: `10.5.5.x`
- **WiFi Password**: `goprohero` (default)
- **Streaming UDP**: `udp://10.5.5.9:8554`
- **API HTTP**: `http://10.5.5.9/gp/gpControl/`
- **Protocoll**: gpControl API (non OpenGoPro, che è solo per Hero9+)

### OUYA (Macchina di elaborazione)
- **SoC**: Nvidia Tegra 3
- **Architettura**: ARMv7l (armhf)
- **OS**: Linux (kernel 6.12.x)
- **Ruolo**: Si collega alla rete WiFi della GoPro, riceve il flusso UDP, lo converte via FFmpeg in RTMP verso Nginx-RTMP, e serve il player HLS
- **IP GoPro network**: `10.5.5.x` (assegnato dalla GoPro via DHCP)

### Server Proxmox (OctoPrint)
- **Virtualizzazione**: LXC Container
- **OctoPrint**: Versione 1.9.0+ (con Classic Webcam plugin integrato)
- **Porta**: 5000 (default)
- **Ruolo**: Visualizza lo stream HLS nell'interfaccia web

## Topologia di Rete

```
┌─────────────────────────────────────────────────────────┐
│                    RETE LOCALE                          │
│                                                         │
│  ┌──────────────┐    WiFi Direct    ┌───────────────┐  │
│  │   GoPro      │◄─────────────────►│    OUYA       │  │
│  │   Hero 4     │  10.5.5.9         │  (ARMv7l)     │  │
│  │   Black      │  UDP:8554         │               │  │
│  │              │  HTTP API         │  FFmpeg        │  │
│  └──────────────┘                   │  Nginx-RTMP   │  │
│                                     │  Porta: 1935  │  │
│                                     │  Porta: 8080  │  │
│                                     └───────┬───────┘  │
│                                             │          │
│                                     ┌───────▼───────┐  │
│                                     │  Proxmox LXC  │  │
│                                     │  OctoPrint    │  │
│                                     │  :5000        │  │
│                                     └───────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Flusso Dati

1. GoPro crea rete WiFi Direct → OUYA si collega
2. GoPro avvia streaming UDP (`http://10.5.5.9/gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart`)
3. FFmpeg cattura UDP `://10.5.5.9:8554` → converte in FLV → push RTMP `rtmp://localhost:1935/live/gopro`
4. Nginx-RTMP riceve RTMP → genera frammenti HLS (`/mnt/hls/gopro.m3u8`)
5. OctoPrint (Classic Webcam) legge `http://<ouya_ip>:8080/hls/gopro.m3u8`
6. Utente vede lo stream nella WebUI di OctoPrint

## Stack Tecnologico

| Componente | Tecnologia | Ruolo |
|-----------|-----------|-------|
| Client GoPro | `goprocam` (Python) | Controllo remoto GoPro |
| Streaming bridge | FFmpeg | Conversione UDP → RTMP |
| Media server | Nginx-RTMP (Podman) | RTMP → HLS/DASH |
| Player web | hls.js / Video.js | Riproduzione HLS nel browser |
| 3D Printer UI | OctoPrint | Visualizzazione stream + controllo stampante |
| Container runtime | Podman | Deploy del media server |

## Limiti Conosciuti

- La GoPro Hero 4 supporta streaming solo a risoluzioni limitate (max 720p per streaming stabile)
- La rete WiFi Direct ha raggio limitato (~10-15m)
- Il flusso UDP può essere instabile con interferenze WiFi
- OctoPrint gira su macchina separata (LXC su Proxmox), non sull'OUYA
