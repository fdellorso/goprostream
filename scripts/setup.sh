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

# ─── 1. Verifica dipendenze ─────────────────────────────────

echo "[1/5] Verifica dipendenze..."
if command -v podman >/dev/null 2>&1; then
    echo "  ✓ podman"
else
    echo "  ✗ podman mancante"
    exit 1
fi
echo ""

# ─── 2. Configurazione ──────────────────────────────────────

echo "[2/5] Configurazione..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✓ .env creato"
else
    echo "  ✓ .env presente"
fi
echo ""

# ─── 3. Build immagine Python ────────────────────────────────

echo "[3/5] Build immagine goprostream..."
$COMPOSE build goprostream
echo "  ✓ Immagine buildata"
echo ""

# ─── 4. Avvia container ──────────────────────────────────────

echo "[4/5] Avvio container..."
$COMPOSE up -d
echo "  ✓ Container avviati"
echo ""

# ─── 5. Verifica stato ──────────────────────────────────────

echo "[5/5] Stato:"
$COMPOSE ps
echo ""

echo "=== Setup completato! ==="
echo ""
echo "Prossimi passi:"
echo "  ./scripts/wifi-connect.sh   # Connetti WiFi alla GoPro"
echo "  ./scripts/start.sh           # Avvia streaming"
echo ""
echo "Dashboard: http://localhost:8080/"
echo ""
