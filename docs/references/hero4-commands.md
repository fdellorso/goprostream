# HERO4 WiFi Commands — Riferimento Completo

> **Source**: https://github.com/KonradIT/goprowifihack/blob/master/HERO4/WifiCommands.md
> **Firmware**: HD4.02.05.00.00 (Oct 2016)
> **Applicabile a**: HERO4 Black, HERO4 Silver
> **Nota**: Comandi HERO2/3 funzionano su HERO4 ma non consigliati

## Base URL

```
http://10.5.5.9/gp/gpControl/
```

> **Nota**: Le HERO4 **non richiedono password** nelle URL WiFi.

---

## Controlli Base

### Shutter (Scatto/Registrazione)

```bash
# Trigger (start scatto/video)
http://10.5.5.9/gp/gpControl/command/shutter?p=1

# Stop (ferma video/timelapse)
http://10.5.5.9/gp/gpControl/command/shutter?p=0
```

### Modalità Boot Default

```bash
# Video
http://10.5.5.9/gp/gpControl/setting/53/0

# Photo
http://10.5.5.9/gp/gpControl/setting/53/1

# MultiShot
http://10.5.5.9/gp/gpControl/setting/53/2
```

### Modalità Primarie

```bash
# Video
http://10.5.5.9/gp/gpControl/command/mode?p=0

# Photo
http://10.5.5.9/gp/gpControl/command/mode?p=1

# MultiShot
http://10.5.5.9/gp/gpControl/command/mode?p=2
```

### Modalità Secondarie

```bash
# Video (VIDEO)
http://10.5.5.9/gp/gpControl/command/sub_mode?mode=0&sub_mode=0

# TimeLapse Video (VIDEO)
http://10.5.5.9/gp/gpControl/command/sub_mode?mode=0&sub_mode=1

# Video + Photo (VIDEO)
http://10.5.5.9/gp/gpControl/command/sub_mode?mode=0&sub_mode=2

# Looping (VIDEO)
http://10.5.5.9/gp/gpControl/command/sub_mode?mode=0&sub_mode=3

# Single (PHOTO)
http://10.5.5.9/gp/gpControl/command/sub_mode?mode=1&sub_mode=0

# Continuous (PHOTO)
http://10.5.5.9/gp/gpControl/command/sub_mode?mode=1&sub_mode=1

# Night (PHOTO)
http://10.5.5.9/gp/gpControl/command/sub_mode?mode=1&sub_mode=2

# Burst (MultiShot)
http://10.5.5.9/gp/gpControl/command/sub_mode?mode=2&sub_mode=0

# Timelapse (MultiShot)
http://10.5.5.9/gp/gpControl/command/sub_mode?mode=2&sub_mode=1

# NightLapse (MultiShot)
http://10.5.5.9/gp/gpControl/command/sub_mode?mode=2&sub_mode=2
```

### Sistema

```bash
# Locate ON/OFF (fa lampeggiare le LED)
http://10.5.5.9/gp/gpControl/command/system/locate?p=1
http://10.5.5.9/gp/gpControl/command/system/locate?p=0

# Power Off (sleep)
http://10.5.5.9/gp/gpControl/command/system/sleep

# Tag Moment (segna momento nel video)
http://10.5.5.9/gp/gpControl/command/storage/tag_moment
```

### WiFi

```bash
# Imposta nome WiFi
http://10.5.5.9/gp/gpControl/command/wireless/ap/ssid?ssid=GOPRONAME

# Imposta nome e password
http://10.5.5.9/gp/gpControl/command/wireless/ap/ssid?ssid=GOPRONAME&pw=GOPROPASS
```

### Media

```bash
# Elimina file
http://10.5.5.9/gp/gpControl/command/storage/delete?p=/100GOPRO/G0010124.JPG

# Elimina ultimo media
http://10.5.5.9/gp/gpControl/command/storage/delete/last

# Formatta SD (ATTENZIONE: cancella tutto!)
http://10.5.5.9/gp/gpControl/command/storage/delete/all

# Tag moment in video specifico
http://10.5.5.9/gp/gpControl/command/storage/tag_moment/playback?p=XXXGOPRO/XXXXXX.MP4&tag=MILLISECONDS
```

### Accensione (Wake-on-LAN)

La HERO4 Black/Silver si accende via **WoL**:

```
MAC Address: [MAC della GoPro]
IP: 10.5.5.9
Subnet: 255.255.255.0
Port: 9
```

> La HERO4 Session richiede il magic packet quando si vuole operare con la camera.

### Pairing Codice

Le HERO4 richiedono un codice di autenticazione 4 cifre (PIN sul display GoPro) per il primo collegamento.

```bash
# 1. Connettersi alla rete GOPRO-BP-XXXX (password: goprohero)

# 2. Inizia pairing
https://10.5.5.9/gpPair?c=start&pin=XXXX&mode=0

# 3. Finisci pairing
https://10.5.5.9/gpPair?c=finish&pin=XXXX&mode=0
```

---

## Impostazioni Video

### Risoluzioni (HERO4 Black)

| Risoluzione | URL |
|------------|-----|
| 4K | `http://10.5.5.9/gp/gpControl/setting/2/1` |
| 4K SuperView | `http://10.5.5.9/gp/gpControl/setting/2/2` |
| 2.7K | `http://10.5.5.9/gp/gpControl/setting/2/4` |
| 2.7K SuperView | `http://10.5.5.9/gp/gpControl/setting/2/5` |
| 2.7K 4:3 | `http://10.5.5.9/gp/gpControl/setting/2/6` |
| 1440p | `http://10.5.5.9/gp/gpControl/setting/2/7` |
| 1080p SuperView | `http://10.5.5.9/gp/gpControl/setting/2/8` |
| 1080p | `http://10.5.5.9/gp/gpControl/setting/2/9` |
| 960p | `http://10.5.5.9/gp/gpControl/setting/2/10` |
| 720p SuperView | `http://10.5.5.9/gp/gpControl/setting/2/11` |
| 720p | `http://10.5.5.9/gp/gpControl/setting/2/12` |
| WVGA | `http://10.5.5.9/gp/gpControl/setting/2/13` |

### Frame Rate (HERO4 Black)

| FPS | URL |
|-----|-----|
| 240 | `http://10.5.5.9/gp/gpControl/setting/3/0` |
| 120 | `http://10.5.5.9/gp/gpControl/setting/3/1` |
| 100 | `http://10.5.5.9/gp/gpControl/setting/3/2` |
| 90 | `http://10.5.5.9/gp/gpControl/setting/3/3` |
| 80 | `http://10.5.5.9/gp/gpControl/setting/3/4` |
| 60 | `http://10.5.5.9/gp/gpControl/setting/3/5` |
| 50 | `http://10.5.5.9/gp/gpControl/setting/3/6` |
| 48 | `http://10.5.5.9/gp/gpControl/setting/3/7` |
| 30 | `http://10.5.5.9/gp/gpControl/setting/3/8` |
| 25 | `http://10.5.5.9/gp/gpControl/setting/3/9` |
| 24 | `http://10.5.5.9/gp/gpControl/setting/3/10` |
| 15 | `http://10.5.5.9/gp/gpControl/setting/3/11` |
| 12.5 | `http://10.5.5.9/gp/gpControl/setting/3/12` |

### FOV (Field of View)

| Valore | URL |
|--------|-----|
| Wide | `http://10.5.5.9/gp/gpControl/setting/4/0` |
| Medium | `http://10.5.5.9/gp/gpControl/setting/4/1` |
| Narrow | `http://10.5.5.9/gp/gpControl/setting/4/2` |
| Linear (anti-barrel, solo FW 5.00) | `http://10.5.5.9/gp/gpControl/setting/4/4` |

### Protune Video

```bash
# Protune ON/OFF
http://10.5.5.9/gp/gpControl/setting/10/1   # ON
http://10.5.5.9/gp/gpControl/setting/10/0   # OFF

# White Balance
http://10.5.5.9/gp/gpControl/setting/11/0   # Auto
http://10.5.5.9/gp/gpControl/setting/11/1   # 3000K
http://10.5.5.9/gp/gpControl/setting/11/2   # 5500K
http://10.5.5.9/gp/gpControl/setting/11/3   # 6500K
http://10.5.5.9/gp/gpControl/setting/11/4   # Native
http://10.5.5.9/gp/gpControl/setting/11/5   # 4000K
http://10.5.5.9/gp/gpControl/setting/11/6   # 4800K
http://10.5.5.9/gp/gpControl/setting/11/7   # 6000K

# Color
http://10.5.5.9/gp/gpControl/setting/12/0   # GoPro Color
http://10.5.5.9/gp/gpControl/setting/12/1   # Flat

# ISO Limit
http://10.5.5.9/gp/gpControl/setting/13/0   # 6400
http://10.5.5.9/gp/gpControl/setting/13/1   # 1600
http://10.5.5.9/gp/gpControl/setting/13/2   # 400
http://10.5.5.9/gp/gpControl/setting/13/3   # 3200
http://10.5.5.9/gp/gpControl/setting/13/4   # 800
http://10.5.5.9/gp/gpControl/setting/13/7   # 200
http://10.5.5.9/gp/gpControl/setting/13/8   # 100

# Sharpness
http://10.5.5.9/gp/gpControl/setting/14/0   # High
http://10.5.5.9/gp/gpControl/setting/14/1   # Medium
http://10.5.5.9/gp/gpControl/setting/14/2   # Low

# ISO Mode
http://10.5.5.9/gp/gpControl/setting/74/0   # Max
http://10.5.5.9/gp/gpControl/setting/74/1   # Lock

# EV Compensation
http://10.5.5.9/gp/gpControl/setting/15/0   # +2.0
http://10.5.5.9/gp/gpControl/setting/15/1   # +1.5
http://10.5.5.9/gp/gpControl/setting/15/2   # +1.0
http://10.5.5.9/gp/gpControl/setting/15/3   # +0.5
http://10.5.5.9/gp/gpControl/setting/15/4   # 0.0
http://10.5.5.9/gp/gpControl/setting/15/5   # -0.5
http://10.5.5.9/gp/gpControl/setting/15/6   # -1.0
http://10.5.5.9/gp/gpControl/setting/15/7   # -1.5
http://10.5.5.9/gp/gpControl/setting/15/8   # -2.0
```

### Low Light / Spot Meter

```bash
# Low Light
http://10.5.5.9/gp/gpControl/setting/8/1    # ON
http://10.5.5.9/gp/gpControl/setting/8/0    # OFF

# Spot Meter
http://10.5.5.9/gp/gpControl/setting/9/1    # ON
http://10.5.5.9/gp/gpControl/setting/9/0    # OFF
```

### Video Timelapse Interval

| Secondi | URL |
|---------|-----|
| 0.5 | `http://10.5.5.9/gp/gpControl/setting/5/0` |
| 1 | `http://10.5.5.9/gp/gpControl/setting/5/1` |
| 2 | `http://10.5.5.9/gp/gpControl/setting/5/2` |
| 5 | `http://10.5.5.9/gp/gpControl/setting/5/3` |
| 10 | `http://10.5.5.9/gp/gpControl/setting/5/4` |
| 30 | `http://10.5.5.9/gp/gpControl/setting/5/5` |
| 60 | `http://10.5.5.9/gp/gpControl/setting/5/6` |

### Looping Duration

| Durata | URL |
|--------|-----|
| Max | `http://10.5.5.9/gp/gpControl/setting/6/0` |
| 5 min | `http://10.5.5.9/gp/gpControl/setting/6/1` |
| 20 min | `http://10.5.5.9/gp/gpControl/setting/6/2` |
| 60 min | `http://10.5.5.9/gp/gpControl/setting/6/3` |
| 120 min | `http://10.5.5.9/gp/gpControl/setting/6/4` |

### Video+Photo Interval

| Secondi | URL |
|---------|-----|
| 5 | `http://10.5.5.9/gp/gpControl/setting/7/1` |
| 10 | `http://10.5.5.9/gp/gpControl/setting/7/2` |
| 30 | `http://10.5.5.9/gp/gpControl/setting/7/3` |
| 60 | `http://10.5.5.9/gp/gpControl/setting/7/4` |

---

## Impostazioni Photo

### Risoluzione

| Risoluzione | URL |
|------------|-----|
| 12MP Wide | `http://10.5.5.9/gp/gpControl/setting/17/0` |
| 7MP Wide | `http://10.5.5.9/gp/gpControl/setting/17/1` |
| 7MP Medium | `http://10.5.5.9/gp/gpControl/setting/17/2` |
| 5MP Wide | `http://10.5.5.9/gp/gpControl/setting/17/3` |

### Continuous Rate

| FPS | URL |
|-----|-----|
| 3 | `http://10.5.5.9/gp/gpControl/setting/18/0` |
| 5 | `http://10.5.5.9/gp/gpControl/setting/18/1` |
| 10 | `http://10.5.5.9/gp/gpControl/setting/18/2` |

### Exposure (NightPhoto)

| Secondi | URL |
|---------|-----|
| Auto | `http://10.5.5.9/gp/gpControl/setting/19/0` |
| 2 | `http://10.5.5.9/gp/gpControl/setting/19/1` |
| 5 | `http://10.5.5.9/gp/gpControl/setting/19/2` |
| 10 | `http://10.5.5.9/gp/gpControl/setting/19/3` |
| 15 | `http://10.5.5.9/gp/gpControl/setting/19/4` |
| 20 | `http://10.5.5.9/gp/gpControl/setting/19/5` |
| 30 | `http://10.5.5.9/gp/gpControl/setting/19/6` |

### Protune Photo

```bash
# Protune ON/OFF
http://10.5.5.9/gp/gpControl/setting/21/1   # ON
http://10.5.5.9/gp/gpControl/setting/21/0   # OFF

# White Balance
http://10.5.5.9/gp/gpControl/setting/22/0   # Auto
http://10.5.5.9/gp/gpControl/setting/22/1   # 3000K
http://10.5.5.9/gp/gpControl/setting/22/2   # 5500K
http://10.5.5.9/gp/gpControl/setting/22/3   # 6500K
http://10.5.5.9/gp/gpControl/setting/22/4   # Native
http://10.5.5.9/gp/gpControl/setting/22/5   # 4000K
http://10.5.5.9/gp/gpControl/setting/22/6   # 4800K
http://10.5.5.9/gp/gpControl/setting/22/7   # 6000K

# Color
http://10.5.5.9/gp/gpControl/setting/23/0   # GoPro Color
http://10.5.5.9/gp/gpControl/setting/23/1   # Flat

# ISO Limit
http://10.5.5.9/gp/gpControl/setting/24/0   # 800
http://10.5.5.9/gp/gpControl/setting/24/1   # 400
http://10.5.5.9/gp/gpControl/setting/24/2   # 200
http://10.5.5.9/gp/gpControl/setting/24/3   # 100

# ISO Min
http://10.5.5.9/gp/gpControl/setting/75/0   # 800
http://10.5.5.9/gp/gpControl/setting/75/1   # 400
http://10.5.5.9/gp/gpControl/setting/75/2   # 200
http://10.5.5.9/gp/gpControl/setting/75/3   # 100

# Sharpness
http://10.5.5.9/gp/gpControl/setting/25/0   # High
http://10.5.5.9/gp/gpControl/setting/25/1   # Medium
http://10.5.5.9/gp/gpControl/setting/25/2   # Low

# Spot Meter
http://10.5.5.9/gp/gpControl/setting/20/1   # ON
http://10.5.5.9/gp/gpControl/setting/20/0   # OFF

# EV Compensation
http://10.5.5.9/gp/gpControl/setting/26/0   # +2.0
http://10.5.5.9/gp/gpControl/setting/26/4   # 0.0
http://10.5.5.9/gp/gpControl/setting/26/8   # -2.0
```

---

## Impostazioni MultiShot

### Burst Rate

| Rate | URL |
|------|-----|
| 3/1 | `http://10.5.5.9/gp/gpControl/setting/29/0` |
| 5/1 | `http://10.5.5.9/gp/gpControl/setting/29/1` |
| 10/1 | `http://10.5.5.9/gp/gpControl/setting/29/2` |
| 10/2 | `http://10.5.5.9/gp/gpControl/setting/29/3` |
| 10/3 | `http://10.5.5.9/gp/gpControl/setting/29/4` |
| 30/1 | `http://10.5.5.9/gp/gpControl/setting/29/5` |
| 30/2 | `http://10.5.5.9/gp/gpControl/setting/29/6` |
| 30/3 | `http://10.5.5.9/gp/gpControl/setting/29/7` |
| 30/6 | `http://10.5.5.9/gp/gpControl/setting/29/8` |

### Timelapse Interval

| Secondi | URL |
|---------|-----|
| 0.5 | `http://10.5.5.9/gp/gpControl/setting/30/0` |
| 1 | `http://10.5.5.9/gp/gpControl/setting/30/1` |
| 2 | `http://10.5.5.9/gp/gpControl/setting/30/2` |
| 5 | `http://10.5.5.9/gp/gpControl/setting/30/5` |
| 10 | `http://10.5.5.9/gp/gpControl/setting/30/10` |
| 30 | `http://10.5.5.9/gp/gpControl/setting/30/30` |
| 60 | `http://10.5.5.9/gp/gpControl/setting/30/60` |

### NightLapse Exposure

| Secondi | URL |
|---------|-----|
| Auto | `http://10.5.5.9/gp/gpControl/setting/31/0` |
| 2 | `http://10.5.5.9/gp/gpControl/setting/31/1` |
| 5 | `http://10.5.5.9/gp/gpControl/setting/31/2` |
| 10 | `http://10.5.5.9/gp/gpControl/setting/31/3` |
| 15 | `http://10.5.5.9/gp/gpControl/setting/31/4` |
| 20 | `http://10.5.5.9/gp/gpControl/setting/31/5` |
| 30 | `http://10.5.5.9/gp/gpControl/setting/31/6` |

### NightLapse Interval

| Intervallo | URL |
|-----------|-----|
| Continuous | `http://10.5.5.9/gp/gpControl/setting/32/0` |
| 4s | `http://10.5.5.9/gp/gpControl/setting/32/4` |
| 5s | `http://10.5.5.9/gp/gpControl/setting/32/5` |
| 10s | `http://10.5.5.9/gp/gpControl/setting/32/10` |
| 15s | `http://10.5.5.9/gp/gpControl/setting/32/15` |
| 20s | `http://10.5.5.9/gp/gpControl/setting/32/20` |
| 30s | `http://10.5.5.9/gp/gpControl/setting/32/30` |
| 1m | `http://10.5.5.9/gp/gpControl/setting/32/60` |
| 2m | `http://10.5.5.9/gp/gpControl/setting/32/120` |
| 5m | `http://10.5.5.9/gp/gpControl/setting/32/300` |
| 30m | `http://10.5.5.9/gp/gpControl/setting/32/1800` |
| 60m | `http://10.5.5.9/gp/gpControl/setting/32/3600` |

### Risoluzione MultiShot

| Risoluzione | URL |
|------------|-----|
| 12MP Wide | `http://10.5.5.9/gp/gpControl/setting/28/0` |
| 7MP Wide | `http://10.5.5.9/gp/gpControl/setting/28/1` |
| 7MP Medium | `http://10.5.5.9/gp/gpControl/setting/28/2` |
| 5MP Medium | `http://10.5.5.9/gp/gpControl/setting/28/3` |

### Protune MultiShot

```bash
# Protune ON/OFF
http://10.5.5.9/gp/gpControl/setting/34/1   # ON
http://10.5.5.9/gp/gpControl/setting/34/0   # OFF

# White Balance
http://10.5.5.9/gp/gpControl/setting/35/0   # Auto
http://10.5.5.9/gp/gpControl/setting/35/4   # Native

# Color
http://10.5.5.9/gp/gpControl/setting/36/0   # GoPro Color
http://10.5.5.9/gp/gpControl/setting/36/1   # Flat

# ISO Limit
http://10.5.5.9/gp/gpControl/setting/37/0   # 800
http://10.5.5.9/gp/gpControl/setting/37/3   # 100

# ISO Min
http://10.5.5.9/gp/gpControl/setting/76/0   # 800
http://10.5.5.9/gp/gpControl/setting/76/3   # 100

# Sharpness
http://10.5.5.9/gp/gpControl/setting/38/0   # High
http://10.5.5.9/gp/gpControl/setting/38/1   # Medium
http://10.5.5.9/gp/gpControl/setting/38/2   # Low

# Spot Meter
http://10.5.5.9/gp/gpControl/setting/33/1   # ON
http://10.5.5.9/gp/gpControl/setting/33/0   # OFF
```

---

## Impostazioni Generali

```bash
# Orientamento
http://10.5.5.9/gp/gpControl/setting/52/0   # Auto (Gyro)
http://10.5.5.9/gp/gpControl/setting/52/1   # Up
http://10.5.5.9/gp/gpControl/setting/52/2   # Down

# Quick Capture
http://10.5.5.9/gp/gpControl/setting/54/1   # ON
http://10.5.5.9/gp/gpControl/setting/54/0   # OFF

# LED Status
http://10.5.5.9/gp/gpControl/setting/55/0   # OFF
http://10.5.5.9/gp/gpControl/setting/55/1   # 2 LEDs
http://10.5.5.9/gp/gpControl/setting/55/2   # 4 LEDs

# Beeps Volume
http://10.5.5.9/gp/gpControl/setting/56/0   # 100%
http://10.5.5.9/gp/gpControl/setting/56/1   # 70%
http://10.5.5.9/gp/gpControl/setting/56/2   # Mute

# Video Format
http://10.5.5.9/gp/gpControl/setting/57/0   # NTSC
http://10.5.5.9/gp/gpControl/setting/57/1   # PAL

# LCD Display
http://10.5.5.9/gp/gpControl/setting/72/1   # ON
http://10.5.5.9/gp/gpControl/setting/72/0   # OFF

# On Screen Display
http://10.5.5.9/gp/gpControl/setting/58/1   # ON
http://10.5.5.9/gp/gpControl/setting/58/0   # OFF

# LCD Brightness
http://10.5.5.9/gp/gpControl/setting/49/0   # High
http://10.5.5.9/gp/gpControl/setting/49/1   # Medium
http://10.5.5.9/gp/gpControl/setting/49/2   # Low

# LCD Lock
http://10.5.5.9/gp/gpControl/setting/50/1   # ON
http://10.5.5.9/gp/gpControl/setting/50/0   # OFF

# LCD Timeout
http://10.5.5.9/gp/gpControl/setting/51/0   # Never
http://10.5.5.9/gp/gpControl/setting/51/1   # 1 min
http://10.5.5.9/gp/gpControl/setting/51/2   # 2 min
http://10.5.5.9/gp/gpControl/setting/51/3   # 3 min

# Auto Power Off
http://10.5.5.9/gp/gpControl/setting/59/0   # Never
http://10.5.5.9/gp/gpControl/setting/59/1   # 1 min
http://10.5.5.9/gp/gpControl/setting/59/2   # 2 min
http://10.5.5.9/gp/gpControl/setting/59/3   # 3 min
http://10.5.5.9/gp/gpControl/setting/59/4   # 5 min
```

---

## Data e Ora

```bash
# Imposta data e ora (formato hex: YY MM DD HH MM SS)
http://10.5.5.9/gp/gpControl/command/setup/date_time?p=%11%0b%10%11%29%2c

# Esempio: 11=(20)17, 0b=11(Nov), 10=16, 11=17, 29=41, 2c=44
```

---

## Bluetooth Pairing

```bash
# Lista dispositivi abbinati (whitelist)
http://10.5.5.9/gp/gpControl/command/ble/whitelist/list

# Scansiona dispositivi
http://10.5.5.9/gp/gpControl/command/ble/scan?p=1

# Lista dispositivi scansionati
http://10.5.5.9/gp/gpControl/command/ble/scan/list

# Avvia pairing
http://10.5.5.9/gp/gpControl/command/ble/pairing_available
http://10.5.5.9/gp/gpControl/command/ble/pairing_phase?p=1

# Stato pairing
http://10.5.5.9/gp/gpControl/command/ble/pair/status

# Pair con dispositivo
http://10.5.5.9/gp/gpControl/command/ble/pair/start?device=DEVICE_ID&address_type=ADDRESS_TYPE
```

---

## GoPro Clips (Estrai clip da video)

```bash
# Avvia conversione
http://10.5.5.9/gp/gpControl/command/transcode/request?source=DCIM/[XXXGOPRO]/GOPRXXXX.MP4&res=VIDEO_RESOLUTION&fps_divisor=FPS&in_ms=In_MS&out_ms=Out_MS

# Stato conversione
http://10.5.5.9/gp/gpControl/command/transcode/status?id=STATUS_ID

# Annulla conversione
http://10.5.5.9/gp/gpControl/command/transcode/cancel?id=STATUS_ID
```

### Parametri Risoluzione Clip

| Valore | Risoluzione |
|--------|------------|
| 0 | 1080p |
| 1 | 960p |
| 2 | 720p |
| 3 | WVGA |
| 4 | 640p |
| 5 | 432x240 (live preview) |
| 6 | 320x240 |

### Parametri FPS Divisor

| Valore | Fattore |
|--------|---------|
| 0 | 1/1 (originale) |
| 1 | 1/2 |
| 2 | 1/3 |
| 3 | 1/4 |
| 4 | 1/8 |

---

## WiFi AP Settings

```bash
# WiFi OFF
http://10.5.5.9/gp/gpControl/setting/63/0

# Modalità App/Smartphone
http://10.5.5.9/gp/gpControl/setting/63/1

# Modalità GoPro RC
http://10.5.5.9/gp/gpControl/setting/63/2

# Modalità GoPro Smart Remote
http://10.5.5.9/gp/gpControl/setting/63/4
```
