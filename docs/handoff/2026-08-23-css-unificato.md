# Handoff — 2023-08-23 CSS Unificato + Skills Design

## Contesto

- **Branch**: main
- **Comando**: Unificazione CSS e aggiunta skills frontend-design + css-layout

## Cosa fatto

### Skill frontend-design (Anthropic)
- Installata da `anthropics/skills` repo
- Contiene filosofia del design: come pensare all'estetica, non al CSS tecnico
- Serve come riferimento quando si creano nuove pagine

### Skill css-layout (nostra, aggiornata)
- Aggiunta **Page Template** (struttura HTML minima)
- Aggiunta **Checklist** per nuove pagine
- Aggiunta sezione **Scelta cromatica** (perché il nostro palette è una scelta, non un default)
- Aggiunto riferimento a `frontend-design` per ispirazione
- Aggiunta sezione **Architettura CSS** (base.css vs inline)
- Documentati pattern CSS specifici (dashboard e player)

### css/base.css (creato)
- 105 righe
- Tokens CSS (:root variables)
- Reset + body
- Header + nav links (con hover, active, focus)
- Status dot (.status-dot, .ok, .err)
- Common button (.cmd-btn)
- Responsive (768px)
- Caricato da tutte e 3 le pagine

### Dashboard (aggiornata)
- CSS ridotto da ~120 a ~55 righe
- Rimosso: reset, header, nav, status-dot (ora in base.css)
- Aggiunto: link a base.css
- Colori hardcoded sostituiti con CSS variables

### Video.js (aggiornato)
- CSS ridotto da ~25 a ~12 righe
- Rimosso: header, nav, status-dot (ora in base.css)
- Aggiunto: link a base.css
- Bottone restart usa classe .cmd-btn

### HLS.js (aggiornato)
- CSS ridotto da ~25 a ~11 righe
- Stesse modifiche di Video.js

## Verifica effettuata
- ✅ Tutti gli HTML referenziano base.css
- ✅ Nessun CSS duplicato
- ✅ CSS variables usate correttamente
- ✅ Struttura HTML valida
- ✅ Ordine CSS corretto (base → inline)
- ✅ Parentesi CSS bilanciate
- ⚠️ Colori hardcoded rimasti: solo variazioni intenzionali + JS inline

## Note per prossimo agente
- `base.css` è la fonte di verità — ogni modifica deve passare dalla skill css-layout
- CSS inline è libera scelta, ma deve usare i token di base.css
- I colori hardcoded nel JS (#00ff88, #ff4444) non usano CSS variables (servirebbero classi)
- Lo skill css-layout ha un page template da copiare per nuove pagine

## Prossimi Passi
- [ ] Testare le pagine nel browser (OUYA)
- [ ] Eventuale estrazione CSS aggiuntivo se la dashboard cresce
