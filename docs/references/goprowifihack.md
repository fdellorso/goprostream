# GoPro WiFi Hack — Riferimento Completo

> **Source**: https://github.com/KonradIT/goprowifihack
> **Autore**: Konrad Iturbe (@KonradIT)
> **Status**: Progetto "sunsetted" in favore di OpenGoPro
> **Nostra device**: GoPro Hero 4 Black

## Descrizione

Repository principale che documenta le API WiFi (gpControl) di tutte le telecamere GoPro. È la **fonte primaria** per il controllo remoto delle telecamere WiFi-enabled. Copre un decennio di rilasci GoPro.

## Note Critiche per il Nostro Progetto

- **OpenGoPro** supporta solo Hero9+ — per la **Hero4** questo repo resta l'unica fonte
- La HERO4 è la **base** per le API future (le chiamate sono simili per Hero4 in poi)
- Hero4 **non richiede password** nelle URL WiFi
- Le credenziali WiFi default sono: SSID `GOPRO-BP-XXXX`, password `goprohero`
- L'IP della GoPro è sempre `10.5.5.9`

## Mappa del Repository

| Sezione | Contenuto |
|---------|-----------|
| [HERO4/](https://github.com/KonradIT/goprowifihack/tree/master/HERO4) | Tutto per Hero4: streaming, media, comandi, status |
| [HERO4/Livestreaming.md](https://github.com/KonradIT/goprowifihack/blob/master/HERO4/Livestreaming.md) | Come avviare lo streaming UDP |
| [HERO4/WifiCommands.md](https://github.com/KonradIT/goprowifihack/blob/master/HERO4/WifiCommands.md) | Comandi WiFi completi (setting, protune, media) |
| [HERO4/CameraStatus.md](https://github.com/KonradIT/goprowifihack/blob/master/HERO4/CameraStatus.md) | Significato di ogni campo dello status JSON |
| [HERO4/Mediabrowsing.md](https://github.com/KonradIT/goprowifihack/blob/master/HERO4/Mediabrowsing.md) | Browse e download media via WiFi |
| [HERO4/Framerates-Resolutions.md](https://github.com/KonradIT/goprowifihack/blob/master/HERO4/Framerates-Resolutions.md) | Tabella completa risoluzioni/FPS |
| [Libraries.md](https://github.com/KonradIT/goprowifihack/blob/master/Libraries.md) | Lista wrapper di terze parti |

## Repository Correlati (librerie di KonradIT)

| Repo | Scopo | Installazione |
|------|-------|---------------|
| [gopro-py-api](https://github.com/KonradIT/gopro-py-api) | Wrapper Python per le API WiFi | `pip install goprocam` |
| [gopro-ble-py](https://github.com/KonradIT/gopro-ble-py) | Comandi Bluetooth BLE (accensione) | `pip install goproble` |
| [GoProStream](https://github.com/KonradIT/GoProStream) | Tool streaming Python di esempio | Script standalone |
| [gopro-control](https://github.com/KonradIT/gopro-control) | Interfaccia web di controllo | Web app |
| [gopro-linux](https://github.com/KonradIT/gopro-linux) | Script Linux per media GoPro | Bash scripts |
| [hero4hack](https://github.com/KonradIT/hero4hack) | Hack specifici HERO4 | Ricerca/analyisi |
| [OpenGoPro](https://gopro.github.io/OpenGoPro) | API ufficiale (Hero9+ solo) | BLE + WiFi |

## Camere Coperte

| Modello | Anno | Note |
|---------|------|------|
| HERO2 w/ WiFi BacPac | 2012 | |
| HERO3 (Black/Silver/White) | 2013 | |
| HERO3+ (Silver/Black) | 2013 | |
| HERO4 (Black/Silver/Session) | 2014 | **La nostra** |
| HERO+ / HERO+ LCD | 2015 | |
| GoPro HERO (2018) | 2018 | |
| HERO5 (Black/Session) | 2016 | |
| HERO6 Black | 2016 | |
| HERO7 (Black/Silver/White) | 2017 | |
| Fusion 1 | 2017 | |
| MAX | 2019 | |
| HERO8 Black | 2018 | Usa comandi Hero7, tranne Webcam |
| HERO9 Black | 2019 | Prima con OpenGoPro BLE |
| HERO10 Black | 2021 | OpenGoPro v2, USB Ethernet |
| HERO11 Black | 2022 | |

## Acknowledgements

- Konrad Iturbe — sviluppatore principale
- EvilWombat — ricerca HERO3
- 3v1n0, Maelstrom Napalm, fraannk — ricerca HERO4
- krystof-k — comandi Bluetooth
- Mark Kirschenbaum (gethypoxic.com) — info Bluetooth
- dough29 — ricerca HERO2
