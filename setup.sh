#!/bin/bash
# GoPro Streaming Server — Setup
# Installa dipendenze e prepara l'ambiente di sviluppo.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== GoPro Streaming Server — Setup ==="
echo ""

# ─── 1. Verifica dipendenze di sistema ───────────────────────

echo "[1/5] Verifica dipendenze di sistema..."

check_cmd() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "  ✓ $1"
        return 0
    else
        echo "  ✗ $1 — MANCANTE"
        return 1
    fi
}

MISSING=0
check_cmd podman       || MISSING=1
check_cmd podman-compose || MISSING=1
check_cmd ffmpeg       || MISSING=1
check_cmd python3      || MISSING=1
check_cmd pipenv       || MISSING=1
check_cmd node         || MISSING=1
check_cmd npm          || MISSING=1

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo "ERRORE: Alcune dipendenze mancano. Installale e riesegui."
    exit 1
fi
echo ""

# ─── 2. Copia .env se non esiste ─────────────────────────────

echo "[2/5] Configurazione..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✓ File .env creato da .env.example — MODIFICALI se necessario"
else
    echo "  ✓ File .env già presente"
fi
echo ""

# ─── 3. Installa dipendenze Python ───────────────────────────

echo "[3/5] Installazione dipendenze Python..."
pipenv install --dev 2>/dev/null || pipenv install
echo "  ✓ Dipendenze Python installate"
echo ""

# ─── 4. Installa dipendenze npm (pyright) ────────────────────

echo "[4/5] Installazione dev tools..."
if [ -f package.json ]; then
    npm install 2>/dev/null
    echo "  ✓ npm packages installati"
else
    echo "  ⚠ package.json non trovato, salto npm"
fi
echo ""

# ─── 5. Avvia container ──────────────────────────────────────

echo "[5/5] Avvio nginx-rtmp..."
podman-compose up -d 2>/dev/null || docker-compose up -d

# Attendi che nginx sia pronto
echo "  Attendo nginx..."
for i in $(seq 1 15); do
    if curl -s -o /dev/null http://localhost:8080/ 2>/dev/null; then
        echo "  ✓ Nginx pronto su http://localhost:8080/"
        break
    fi
    sleep 1
done

echo ""
echo "=== Setup completato! ==="
echo ""
echo "Avvio streaming:"
echo "  ./start.sh"
echo ""
echo "Oppure manualmente:"
echo "  pipenv run python goprostream.py"
echo ""
