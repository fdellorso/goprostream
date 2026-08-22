#!/bin/bash
# GoPro Streaming Server — Start
# Orchestra l'avvio completo: container → attesa nginx → streaming.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== GoPro Streaming Server — Start ==="
echo ""

# ─── 1. Carica configurazione ────────────────────────────────

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

GOPRO_IP="${GOPRO_IP:-10.5.5.9}"
HLS_PORT="${HLS_PORT:-8080}"

# ─── 2. Verifica container ───────────────────────────────────

echo "[1/3] Verifica container nginx-rtmp..."

if podman-compose ps 2>/dev/null | grep -q "Up\|running"; then
    echo "  ✓ Container già attivo"
else
    echo "  Avvio container..."
    podman-compose up -d 2>/dev/null || docker-compose up -d
    echo "  ✓ Container avviati"
fi

# Attendi che nginx sia pronto
echo "  Attendo nginx su porta $HLS_PORT..."
for i in $(seq 1 20); do
    if curl -s -o /dev/null "http://localhost:$HLS_PORT/" 2>/dev/null; then
        echo "  ✓ Nginx pronto"
        break
    fi
    if [ "$i" -eq 20 ]; then
        echo "  ✗ Nginx non risponde dopo 20 secondi"
        echo "  Controlla i log: podman-compose logs nginx-rtmp"
        exit 1
    fi
    sleep 1
done
echo ""

# ─── 3. Verifica GoPro ───────────────────────────────────────

echo "[2/3] Verifica connessione GoPro ($GOPRO_IP)..."

if ping -c 1 -W 2 "$GOPRO_IP" >/dev/null 2>&1; then
    echo "  ✓ GoPro raggiungibile"
else
    echo "  ⚠ GoPro non raggiungibile"
    echo "  Assicurati che:"
    echo "    1. La GoPro sia accesa"
    echo "    2. Il WiFi sia attivo"
    echo "    3. Questo dispositivo sia connesso alla rete GoPro"
    echo ""
    read -p "  Continuo comunque? (s/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi
echo ""

# ─── 4. Avvia streaming ──────────────────────────────────────

echo "[3/3] Avvio streaming..."
echo "  Player: http://localhost:$HLS_PORT/"
echo "  Stream URL: rtmp://localhost:1935/live/gopro"
echo "  Ctrl+C per fermare"
echo ""

pipenv run python goprostream.py
