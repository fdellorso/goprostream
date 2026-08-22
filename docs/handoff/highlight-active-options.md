# Highlight Active Options — Handoff

> **Data:** 2026-08-22
> **Stato:** ✅ Completato

## Funzionalità

Nel tab "Commands" della Dashboard, i bottoni delle opzioni attualmente attive sulla GoPro vengono evidenziati con un bordo e sfondo verde (`#00ff88`).

## Come Funziona

### 1. Attributi HTML sui bottoni

Ogni bottone ha due attributi `data-*`:

```html
<button class="cmd-btn" data-group="resolution" data-value="9" onclick="...">1080p</button>
```

- `data-group` — Categoria (resolution, fps, mode, etc.)
- `data-value` — Valore API GoPro (9 = 1080p)

### 2. CSS per stato attivo

```css
.cmd-btn.active {
  background: #003300;
  border-color: #00ff88;
  color: #00ff88;
}
```

### 3. JavaScript — Funzione updateHighlights()

```javascript
function updateHighlights(settings) {
  // Rimuovi tutti gli highlight
  document.querySelectorAll('.cmd-btn').forEach(b => b.classList.remove('active'));
  
  // Mappa gruppo → valore API
  var map = {
    'mode': statusData['43'],
    'resolution': settings['2'],
    'fps': settings['3'],
    'fov': settings['4'],
    'protune': settings['10'],
    'wb': settings['11'],
    'color': settings['12'],
    'iso': settings['13'],
    'sharpness': settings['14'],
    'ev': settings['15']
  };
  
  // Evidenzia i bottoni corrispondenti
  for (var group in map) {
    var val = map[group];
    var btn = document.querySelector('[data-group="'+group+'"][data-value="'+val+'"]');
    if (btn) btn.classList.add('active');
  }
}
```

### 4. Aggiornamento periodico

`updateHighlights(st)` viene chiamata dentro `updateStatus()` ogni 10 secondi.

## Gruppi Mappati

| Gruppo | Campo API | Valori |
|--------|-----------|--------|
| mode | status.43 | 0=Video, 1=Photo, 2=MultiShot |
| resolution | settings.2 | 1=4K, 9=1080p, 12=720p, etc. |
| fps | settings.3 | 0=240, 5=60, 8=30, etc. |
| fov | settings.4 | 0=Wide, 1=Medium, 2=Narrow, 4=Linear |
| protune | settings.10 | 0=OFF, 1=ON |
| wb | settings.11 | 0=Auto, 1=3000K, etc. |
| color | settings.12 | 0=GoPro, 1=Flat |
| iso | settings.13 | 0=6400, 8=100, etc. |
| sharpness | settings.14 | 0=High, 1=Medium, 2=Low |
| ev | settings.15 | 0=+2.0, 4=0.0, 8=-2.0 |

## File Modificati

| File | Modifica |
|------|----------|
| `player/dashboard.html` | CSS `.active`, data-attributes su 60 bottoni, funzione `updateHighlights()` |
