---
description: Revisiona il codice di streaming e verifica coerenza con la GoPro Hero 4
---
Revisiona il codice Python del progetto concentrandoti su:

1. **Coerenza API GoPro Hero 4**: Verifica che i comandi HTTP usati siano corretti per Hero4 (gpControl API, non OpenGoPro)
2. **Gestione errori**: Controlla che la connessione WiFi, FFmpeg e il KeepAlive siano gestiti correttamente
3. **Type safety**: Verifica che pyright non segnali errori critici
4. **Compatibilità ARMv7l**: Assicurati che non ci siano dipendenze native che non funzionano su ARM

Riferimenti utili:
- API Hero4: `docs/references/hero4-commands.md`
- Streaming: `docs/references/hero4-livestreaming.md`
- Libreria: `docs/references/gopro-py-api.md`
