---
description: Aggiungi una nuova feature al progetto seguendo le convenzioni
argument-hint: "<descrizione feature>"
---
Aggiungi la feature: $@

Prima di implementare:
1. Leggi `docs/architecture.md` per capire dove si inserisce
2. Verifica che non esista già in `docs/references/`
3. Aggiorna `docs/architecture.md` se cambia l'architettura
4. Aggiorna `AGENTS.md` se ci sono nuovi comandi o dipendenze

Dopo aver implementato:
1. Esegui `npx pyright` per verificare il codice
2. Testa che il progetto funzioni ancora
3. Genera handoff con `/handoff <cosa ho fatto>`
4. Crea un commit con `/commit feat: <descrizione>`
