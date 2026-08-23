---
name: css-layout
description: "Regole CSS Tecniche ed Esteriche per il progetto goprostream. Pattern flexbox/grid, responsive, design system della dashboard e player. Usa quando si modificano o creano pagine HTML/CSS del progetto."
---

# CSS Layout — GoPro Streaming

Skill tecnica + estetica per le pagine web del progetto.
Per la filosofia di design generale, consultare [frontend-design](../frontend-design/SKILL.md).

---

## Architettura CSS

```
css/base.css          ← Fonte di verità: tokens, header, nav, status-dot, responsive
                        Regolato da questa skill. NON modificare senza aggiornare la skill.

HTML inline           ← CSS specifico della pagina (tabs, card, player, etc.)
                        Libero, ma deve usare i token di base.css
```

**Regola:** `base.css` garantisce coerenza tra tutte le pagine. Il CSS inline è libera scelta.

---

## 0. Checklist — Nuova Pagina

Prima di creare una nuova pagina HTML, verificare:

- [ ] Importare `<link href="/css/base.css">`
- [ ] Usare il page template qui sotto
- [ ] Usare CSS variables di `base.css` per colori e spacing
- [ ] Header con nav-links coerenti (stessi link delle altre pagine)
- [ ] Responsive: `flex-wrap: wrap` su header, `z-index: 10`
- [ ] Focus visibile: `outline: 2px solid var(--accent)` sugli elementi interattivi
- [ ] Font-size minimo: `0.7rem`

---

## 1. Page Template

Ogni nuova pagina deve copiare questa struttura:

```html
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GoPro Stream — [Nome Pagina]</title>
  <link href="/css/base.css" rel="stylesheet">
  <style>
    /* CSS specifico della pagina qui */
  </style>
</head>
<body>
  <div class="header">
    <h1>🎥 GoPro Stream — [Nome]</h1>
    <nav class="nav-links">
      <a href="/dashboard.html">Dashboard</a>
      <a href="/videojs.html">Video.js Player</a>
      <a href="/streamhls.html">HLS.js Player</a>
    </nav>
  </div>

  <!-- Contenuto specifico -->

</body>
</html>
```

---

## 2. Design System del Progetto

### Scelta cromatica (consapevole)

> Il nostro palette (near-black `#0a0a0a` + acid-green `#00ff88`) è una **scelta deliberata** per un tool di monitoring, non un default AI. Il verde evoca "sistema attivo / OK" — coerente con il dominio (GoPro streaming, stato dispositivi).

### Colori

| Token | Hex | Uso |
|-------|-----|-----|
| `--bg` | `#0a0a0a` | Sfondo body |
| `--bg-card` | `#1a1a1a` | Sfondo card, blocchi |
| `--bg-input` | `#111` | Sfondo input, code, log |
| `--border` | `#333` | Bordi generali |
| `--border-hover` | `#555` | Bordi hover |
| `--text` | `#e0e0e0` | Testo principale |
| `--text-muted` | `#888` | Testo secondario, label |
| `--text-dim` | `#666` | Testo terziario, descrizioni |
| `--accent` | `#00ff88` | Verde-acqua (attivo, ok, link) |
| `--error` | `#ff4444` | Errore |
| `--warning` | `#ffaa00` | Warning |

### Tipografia

```css
body {
  font-family: -apple-system, system-ui, sans-serif;
  font-size: 14px; /* base */
}

/* Scale */
h1:       1.4rem   /* titolo header */
h2:       0.9rem   /* titolo card */
body:     0.85rem  /* testo generale, nav, bottoni */
small:    0.75rem  /* descrizioni, URL box */
code:     0.7rem   /* log, output */
```

> **Nota:** System fonts sono una scelta funzionale per un tool embedded (OUYA). Se in futuro serve un display font, scegliere un solo font characterful per i titoli e mantenere system-ui per il body.

### Spacing

| Valore | Uso |
|--------|-----|
| `20px` | Padding page, header |
| `16px` | Gap grid, padding card |
| `12px` | Gap header, padding cmd-block |
| `8px` | Gap nav, padding interni |
| `6px` | Gap bottoni, margin log |

### Border Radius

| Valore | Uso |
|--------|-----|
| `12px` | Card |
| `8px` | Nav links, input, tab, log, cmd-block |
| `6px` | Bottoni, URL box |

---

## 3. Contenuto di base.css

`base.css` contiene esattamente questi pattern:

### Reset + Body

```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}
```

### Header

```css
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 20px;
  border-bottom: 1px solid var(--border);
  position: relative;
  z-index: 10;
}
.header h1 { font-size: 1.4rem; color: #fff; }
```

### Nav Links

```css
.nav-links { display: flex; gap: 10px; }
.nav-links a {
  color: var(--text-muted);
  text-decoration: none;
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.85rem;
  transition: all 0.2s;
}
.nav-links a:hover { color: #fff; border-color: var(--border-hover); background: var(--bg-card); }
.nav-links a.active { color: var(--accent); border-color: var(--accent); }
.nav-links a:focus { outline: 2px solid var(--accent); outline-offset: 2px; }
```

### Status Dot

```css
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #555; margin-right: 6px; display: inline-block; }
.status-dot.ok { background: var(--accent); }
.status-dot.err { background: var(--error); }
```

### Responsive

```css
@media (max-width: 768px) {
  .header { flex-direction: column; align-items: flex-start; }
  .nav-links { flex-wrap: wrap; }
}
```

---

## 4. CSS Specifico (inline, per pagina)

### Dashboard — pattern disponibili

```css
/* Tabs */
.tabs { display: flex; gap: 0; background: var(--bg-input); border-bottom: 1px solid var(--border); }
.tab-btn { padding: 12px 24px; background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.9rem; border-bottom: 2px solid transparent; }
.tab-btn.active { color: #fff; border-bottom-color: var(--accent); }

/* Grid */
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }

/* Card */
.card { background: var(--bg-card); border-radius: 12px; padding: 16px; border: 1px solid var(--border); }
.card h2 { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }

/* Status Row */
.status-row { display: flex; align-items: center; gap: 8px; margin: 6px 0; font-size: 0.85rem; }
.status-label { color: var(--text-muted); min-width: 120px; }

/* Commands */
.cmd-block { background: var(--bg-input); border-radius: 8px; padding: 12px; margin: 8px 0; }
.cmd-title { font-size: 0.85rem; color: var(--accent); margin-bottom: 8px; font-weight: 600; }
.cmd-btns { display: flex; flex-wrap: wrap; gap: 6px; }
.cmd-btn { padding: 6px 12px; background: #222; border: 1px solid #444; border-radius: 6px; color: var(--text); cursor: pointer; font-size: 0.8rem; }
.cmd-btn:hover { background: #333; border-color: var(--accent); }
.cmd-btn:active { background: var(--accent); color: #000; }

/* Log */
#log { font-family: monospace; font-size: 0.7rem; max-height: 200px; overflow-y: auto; background: var(--bg-input); padding: 10px; border-radius: 8px; margin-top: 12px; }
```

### Player — pattern disponibili

```css
/* Player wrapper (centra il player) */
.player-wrapper { flex: 1; display: flex; align-items: center; justify-content: center; padding: 20px; }

/* Player container */
.player-container { background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border); width: 100%; max-width: 1200px; overflow: hidden; aspect-ratio: 16/9; }

/* Video.js hacks */
.video-js { width: 100% !important; height: 100% !important; }
.vjs-tech { width: 100% !important; height: 100% !important; }

/* Status bar */
.status-bar { padding: 12px 20px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: var(--text-muted); }
```

---

## 5. Regole Responsive

| Regola | Dettaglio |
|--------|-----------|
| Sempre `flex-wrap: wrap` | Su header e nav per mobile |
| Grid `auto-fit` | Si adatta automaticamente |
| `min-width` su input | `150px` minimo, `flex: 1` per espandersi |
| Video player | `aspect-ratio: 16/9` o `width: 100%` |
| Z-index header | `z-index: 10` per stare sopra video/player |

---

## 6. Anti-Pattern da Evitare

| Anti-Pattern | Perché | Soluzione |
|-------------|--------|-----------|
| Seleatori troppo specifici | `.section .card .title` resetta stili | Usare classi piane |
| `!important` | Segnala conflitti non risolti | Ristrutturare la cascade |
| Colori hardcoded | Difficile cambiare tema | Usare CSS variables |
| Pixel fixes | Non responsive | Usare `rem`, `%`, `vw` |
| Border-radius misti | Inconsistenza visiva | Usare i token del design system |
| Font-size < 0.7rem | Illeggibile su mobile | Minimo 0.7rem |

---

## 7. Quando Usare Questa Skill

| Scenario | Cosa fare |
|----------|-----------|
| Nuova pagina | Seguire Page Template + Checklist |
| Modifica dashboard | Usare pattern di sezione 4 |
| Modifica player | Usare pattern di sezione 4 |
| Nuovo componente | Usare variabili colore e spacing di base.css |
| Debug layout | Controllare anti-pattern di sezione 6 |
| Ispirazione estetica | Consultare `frontend-design` per filosofia |
