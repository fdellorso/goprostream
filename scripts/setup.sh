#!/bin/bash
# GoPro Streaming Server — Setup
# Installa dipendenze e prepara l'ambiente.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

COMPOSE="podman-compose -f docker/docker-compose.yml"

echo "=== GoPro Streaming Server — Setup ==="
echo ""

# ─── 1. Verifica dipendenze di sistema ───────────────────────

echo "[1/6] Verifica dipendenze di sistema..."

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
check_cmd podman          || MISSING=1

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo "ERRORE: podman è obbligatorio."
    exit 1
fi
echo ""

# ─── 2. Copia .env se non esiste ─────────────────────────────

echo "[2/6] Configurazione..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✓ File .env creato da .env.example"
    echo "  ⚠ MODIFICA .env con i valori corretti per il tuo setup"
else
    echo "  ✓ File .env già presente"
fi
echo ""

# ─── 3. Verifica Dockerfile ──────────────────────────────────

echo "[3/6] Verifica Dockerfile..."
if [ -f docker/Dockerfile.python ]; then
    echo "  ✓ docker/Dockerfile.python presente"
else
    echo "  ✗ docker/Dockerfile.python mancante"
    exit 1
fi
echo ""

# ─── 4. Build immagine Python ────────────────────────────────

echo "[4/6] Build immagine goprostream..."
$COMPOSE build goprostream
echo "  ✓ Immagine buildata"
echo ""

# ─── 5. Avvia container ──────────────────────────────────────

echo "[5/6] Avvio container..."
$COMPOSE up -d

# Attendi che nginx sia pronto
echo "  Attendo nginx..."
for i in $(seq 1 20); do
    if $COMPOSE ps 2>/dev/null | grep -q "healthy\|Up"; then
        echo "  ✓ Container avviati"
        break
    fi
    if [ "$i" -eq 20 ]; then
        echo "  ⚠ Container potrebbero non essere ancora pronti"
    fi
    sleep 1
done
echo ""

# ─── 6. Verifica stato ──────────────────────────────────────

echo "[6/6] Stato container:"
$COMPOSE ps
echo ""

echo "=== Setup completato! ==="
echo ""
echo "Avvio streaming:"
echo "  ./scripts/wifi-connect.sh   # Connetti WiFi alla GoPro"
echo "  ./scripts/start.sh           # Avvia streaming"
echo ""
echo "Stato:"
echo "  podman-compose -f docker/docker-compose.yml ps"
echo "  curl http://localhost:8080/"
echo ""
