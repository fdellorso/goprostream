# HERO4 Camera Status — Riferimento Completo

> **Source**: https://github.com/KonradIT/goprowifihack/blob/master/HERO4/CameraStatus.md
> **Endpoint**: `http://10.5.5.9/gp/gpControl/status`
> **Formato**: JSON con oggetti `status` e `settings`

## Come Leggere lo Status

```bash
curl http://10.5.5.9/gp/gpControl/status
```

Restituisce un JSON con due oggetti: `status` (stato attuale) e `settings` (impostazioni attive).

---

## Oggetto `status` (Stato Attuale)

| ID | Nome | Valori |
|----|------|--------|
| 1 | Batteria interna presente | 0 = No, 1 = Sì |
| 2 | Livello batteria | 0 = Empty, 1 = Low, 2 = Halfway, 3 = Full, 4 = Charging |
| 8 | Stato registrazione | 0 = Non registrando, 1 = Registrando/Processando |
| 13 | Durata video corrente | Secondi |
| 31 | Clienti connessi al WiFi | Numero |
| 32 | Stato streaming | 0 = Non in stream, 1 = In stream |
| 33 | SD card inserita | 0 = Inserita, 2 = Non presente |
| 34 | Foto rimanenti | Numero |
| 35 | Tempo video rimanente | Secondi |
| 36 | Foto batch scattate | Numero (Timelapse, Burst, Continuous) |
| 37 | Video scattati | Numero |
| 38 | Totale foto scattate | Numero |
| 39 | Totale video scattati | Numero |
| 43 | Modalità corrente | 0 = Video, 1 = Photo, 2 = MultiShot |
| 44 | Sottomodalità corrente | 0 = Single/Burst, 1 = TL/Continuous/TimeLapse, 2 = Video+Photo/Night |
| 54 | Spazio libero SD (bytes) | Numero |

---

## Oggetto `settings` — Video

| ID | Parametro | Valori |
|----|-----------|--------|
| 2 | Risoluzione | 1=4K, 2=4K SV, 4=2.7K, 5=2.7K SV, 6=2.7K 4:3, 7=1440, 8=1080 SV, 9=1080, 10=960, 11=720 SV, 12=720, 13=WVGA |
| 3 | Frame Rate | 0=240, 1=120, 2=100, 3=90, 4=80, 5=60, 6=50, 7=48, 8=30, 9=25, 10=24, 11=15, 12=12.5 |
| 4 | FOV | 0=Wide, 1=Medium, 2=Narrow, 4=Linear |
| 5 | Timelapse Interval | 0=0.5s, 1=1s, 2=2s, 3=5s, 4=10s, 5=30s, 6=60s |
| 6 | Looping Duration | 0=Max, 1=5min, 2=20min, 3=60min, 4=120min |
| 7 | Video+Photo Interval | 1=5s, 2=10s, 3=30s, 4=60s |
| 8 | Low Light | 0=OFF, 1=ON |
| 9 | Spot Meter | 0=OFF, 1=ON |
| 10 | Protune | 0=OFF, 1=ON |
| 11 | White Balance | 0=Auto, 1=3000K, 2=5500K, 3=6500K, 4=Native, 5=4000K, 6=4800K, 7=6000K |
| 12 | Color | 0=GoPro, 1=Flat |
| 13 | ISO Limit | 0=6400, 1=1600, 2=400, 3=3200, 4=800, 7=200, 8=100 |
| 14 | Sharpness | 0=High, 1=Medium, 2=Low |
| 15 | EV Compensation | 0=+2.0 ... 4=0.0 ... 8=-2.0 |
| 68 | SubMode Video | 0=Video, 1=TL Video, 2=Video+Photo, 3=Looping |
| 73 | Manual Exposure | 0=Auto, valori 3-23 per shutter speed |
| 74 | ISO Mode | 0=Max, 1=Lock |

---

## Oggetto `settings` — Photo

| ID | Parametro | Valori |
|----|-----------|--------|
| 17 | Megapixels | 0=12MP Wide, 1=7MP Wide, 2=7MP Med, 3=5MP Med |
| 18 | Continuous Rate | 0=3fps, 1=5fps, 2=10fps |
| 19 | Shutter | 0=Auto, 1=2s, 2=5s, 3=10s, 4=15s, 5=20s, 6=30s |
| 20 | Spot Meter | 0=OFF, 1=ON |
| 21 | Protune | 0=OFF, 1=ON |
| 22 | White Balance | 0=Auto, 1=3000K, 2=5500K, 3=6500K, 4=Native, 5=4000K, 6=4800K, 7=6000K |
| 23 | Color | 0=GoPro, 1=Flat |
| 24 | ISO Limit | 0=800, 1=400, 2=200, 3=100 |
| 25 | Sharpness | 0=High, 1=Medium, 2=Low |
| 26 | EV Compensation | 0=+2.0 ... 4=0.0 ... 8=-2.0 |
| 69 | SubMode Photo | 0=Single, 1=Continuous, 2=Night |
| 75 | ISO Min | 0=800, 1=400, 2=200, 3=100 |

---

## Oggetto `settings` — MultiShot

| ID | Parametro | Valori |
|----|-----------|--------|
| 27 | Default SubMode | 0=Burst, 1=TimeLapse, 2=NightLapse |
| 28 | Megapixels | 0=12MP Wide, 1=7MP Wide, 2=7MP Med, 3=5MP Med |
| 29 | Burst Rate | 0=3/1, 1=5/1, 2=10/1, 3=10/2, 4=10/3, 5=30/1, 6=30/2, 7=30/3, 8=30/6 |
| 30 | Timelapse Interval | 0=0.5s, 1=1s, 2=2s, 5=5s, 10=10s, 30=30s, 60=60s |
| 31 | NightLapse Shutter | 0=Auto, 1=2s, 2=5s, 3=10s, 4=15s, 5=20s, 6=30s |
| 32 | NightLapse Interval | 0=Continuous, 4-60 secondi, 60-3600 secondi |
| 33 | Spot Meter | 0=OFF, 1=ON |
| 34 | Protune | 0=OFF, 1=ON |
| 35 | White Balance | (stesso Photo) |
| 36 | Color | 0=GoPro, 1=Flat |
| 37 | ISO Limit | 0=800, 1=400, 2=200, 3=100 |
| 38 | Sharpness | 0=High, 1=Medium, 2=Low |
| 39 | EV Compensation | 0=+2.0 ... 4=0.0 ... 8=-2.0 |
| 70 | SubMode MultiShot | 0=Burst, 1=TimeLapse, 2=NightLapse |
| 76 | ISO Min | 0=800, 1=400, 2=200, 3=100 |

---

## Oggetto `settings` — Generale

| ID | Parametro | Valori |
|----|-----------|--------|
| 49 | LCD Brightness | 0=High, 1=Medium, 2=Low |
| 50 | LCD Lock | 0=OFF, 1=ON |
| 51 | LCD Timeout | 0=Never, 1=1min, 2=2min, 3=3min |
| 52 | Orientation | 0=Auto, 1=Up, 2=Down |
| 53 | Default Boot Mode | 0=Video, 1=Photo, 2=MultiShot |
| 54 | Quick Capture | 0=OFF, 1=ON |
| 55 | LED Status | 0=OFF, 1=2LEDs, 2=4LEDs |
| 56 | Beep Volume | 0=100%, 1=70%, 2=Mute |
| 57 | Video Format | 0=NTSC, 1=PAL |
| 58 | On Screen Display | 0=OFF, 1=ON |
| 59 | Auto Power Off | 0=Never, 1=1min, 2=2min, 3=3min, 4=5min |
| 62 | Stream Bitrate | Valore in bps (es. 250000, 1000000, 4000000) |
| 63 | WiFi AP Mode | 0=OFF, 1=App, 2=GoPro RC, 4=Smart Remote |
| 64 | Stream Window Size | 0=Default, 1=240p, 4=480p, 7=720p, 8=720p 3:4, 9=720p 1:2 |
| 72 | LCD Display | 0=OFF, 1=ON |
