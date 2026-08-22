#!/bin/bash
# GoPro Streaming Server — Start
# Avvia i container e verifica lo stato.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

COMPOSE="podman-compose -f docker/docker-compose.yml"

echo "=== GoPro Streaming Server — Start ==="
echo ""

# ─── 1. Carica configurazione ────────────────────────────────

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

GOPRO_IP="${GOPRO_IP:-10.5.5.9}"
HLS_PORT="${HLS_PORT:-8080}"

# ─── 2. Verifica connessione GoPro ───────────────────────────

echo "[1/3] Verifica GoPro ($GOPRO_IP)..."

if ping -c 1 -W 2 "$GOPRO_IP" >/dev/null 2>&1; then
    echo "  ✓ GoPro raggiungibile"
else
    echo "  ⚠ GoPro non raggiungibile"
    echo ""
    echo "  Possibili cause:"
    echo "    1. La GoPro non è accesa"
    echo "    2. Non sei connesso alla rete WiFi Direct"
    echo "    3. Esegui prima: ./scripts/wifi-connect.sh"
    echo ""
    read -p "  Continuo comunque? (s/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi
echo ""

# ─── 3. Avvia container ──────────────────────────────────────

echo "[2/3] Avvio container..."

if $COMPOSE ps 2>/dev/null | grep -q "goprostream.*Up"; then
    echo "  ✓ Container goprostream già attivo"
else
    echo "  Avvio..."
    $COMPOSE up -d
    echo "  ✓ Container avviati"
fi
echo ""

# ─── 4. Verifica stato ──────────────────────────────────────

echo "[3/3] Stato:"
$COMPOSE ps
echo ""

echo "=== Streaming attivo! ==="
echo ""
echo "  Player:  http://localhost:$HLS_PORT/"
echo "  HLS:     http://localhost:$HLS_PORT/hls/gopro.m3u8"
echo "  RTMP:    rtmp://localhost:1935/live/gopro"
echo ""
echo "Ferma con:"
echo "  ./scripts/stop.sh"
echo ""
