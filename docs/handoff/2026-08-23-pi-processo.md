# Handoff — 2023-08-23 Miglioramento Processo Pi

## Contesto

- **Branch**: main
- **Comando**: Ristrutturazione processo di sviluppo pi-coding-agent

## Cosa fatto

### Fase 1 — Fix Critici
- `/status`: sostituito `ping` con `curl` per GoPro check (come da AGENTS.md)
- `/commit`: `git add -u` invece di `git add -A`, verifica staged prima del commit
- `/stream`: semplificato a `podman-compose up -d`

### Fase 2 — Pulizia
- Rimossa skill superdesign (10 file, non pertinente al progetto)
- Pulito `settings.json` (rimossi `extensions` e `prompts` ridondanti)
- Rimosso comando `/typecheck` duplicato (rimane tool `python_typecheck`)

### Fase 3 — Miglioramenti
- Aggiunta sezione "Documentazione" in AGENTS.md
- Aggiunta tabella "Comandi Pi" in AGENTS.md
- Aggiunto comando `/debug` (diagnostica completa: GoPro, FFmpeg, Container, RTMP, HLS, Pyright)
- Aggiornato albero .pi in AGENTS.md
- Aggiornato prompt `new-feature.md` con handoff nel flusso

## Modifiche file

| File | Azione |
|------|--------|
| `.pi/extensions/project-commands.ts` | Fix /status, /commit, /stream + aggiunto /debug |
| `.pi/extensions/python-lsp.ts` | Rimosso comando /typecheck |
| `.pi/settings.json` | Pulito |
| `.pi/skills/superdesign/` | Rimosso |
| `AGENTS.md` | Aggiunta Documentazione, Comandi Pi, albero .pi |
| `.pi/prompts/new-feature.md` | Aggiunto step handoff nel flusso |

## Note per prossimo agente

- Handoff va fatto PRIMA del commit (snapshot dello stato)
- La skill CSS layout è stata rimandata — da valutare se serve
- Fase 4 (auto-restart stream, health check periodico) è opzionale, non urgente
- Il bug crash container goprostream è ancora aperto

## Prossimi Passi

- [ ] Skill CSS layout (da cercare o creare)
- [ ] Bug crash container (da investigare)
- [ ] Eventuale health check automatico
