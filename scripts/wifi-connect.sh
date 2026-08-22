#!/bin/bash
# GoPro WiFi Connect
# Si connette alla rete WiFi Direct della GoPro Hero 4.
#
# Credenziali:
#   SSID: GP<numero_seriale> (es. GP26479007)
#   Password: goprohero
#   IP: 10.5.5.9

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# ─── Configurazione ──────────────────────────────────────────

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

GOPRO_SSID="${GOPRO_SSID:-GP26479007}"
GOPRO_PASS="${GOPRO_PASS:-goprohero}"
GOPRO_IP="${GOPRO_IP:-10.5.5.9}"

# ─── Funzioni ────────────────────────────────────────────────

check_pairing_done() {
    # Se settings.63=1 (App mode) E status.31>=1 (client connesso)
    # → pairing già fatto, non serve chiedere
    local status=$(curl -s --connect-timeout 3 "http://$GOPRO_IP/gp/gpControl/status" 2>/dev/null)
    if [ -z "$status" ]; then
        return 1  # GoPro non risponde
    fi

    local wifi_mode=$(echo "$status" | python3 -c "import sys,json; print(json.load(sys.stdin)['settings']['63'])" 2>/dev/null)
    local clients=$(echo "$status" | python3 -c "import sys,json; print(json.load(sys.stdin)['status']['31'])" 2>/dev/null)

    if [ "$wifi_mode" = "1" ] && [ "$clients" -ge 1 ] 2>/dev/null; then
        return 0  # Pairing fatto
    fi
    return 1
}

# ─── Main ────────────────────────────────────────────────────

echo "=== GoPro WiFi Connect ==="
echo ""
echo "SSID:     $GOPRO_SSID"
echo "Password: $GOPRO_PASS"
echo "Gateway:  $GOPRO_IP"
echo ""

# ─── 1. Rileva interfaccia WiFi ──────────────────────────────

echo "[1/5] Rilevamento interfaccia WiFi..."

WIFI_IF=""
for iface in wlan0 wlan1 wlp2s0 wlp3s0; do
    if ip link show "$iface" >/dev/null 2>&1; then
        WIFI_IF="$iface"
        break
    fi
done

if [ -z "$WIFI_IF" ]; then
    WIFI_IF=$(ip -o link show | awk -F': ' '/wl/{print $2}' | head -1)
fi

if [ -z "$WIFI_IF" ]; then
    echo "  ✗ Nessuna interfaccia WiFi trovata"
    exit 1
fi

echo "  ✓ Interfaccia: $WIFI_IF"
echo ""

# ─── 2. Connetti alla rete GoPro ─────────────────────────────

echo "[2/5] Connessione alla rete GoPro..."

if command -v nmcli >/dev/null 2>&1; then
    echo "  Usando nmcli..."
    if nmcli connection show "$GOPRO_SSID" >/dev/null 2>&1; then
        echo "  Connessione esistente, riconnessione..."
        nmcli connection up "$GOPRO_SSID" 2>/dev/null || true
    else
        echo "  Creazione connessione..."
        nmcli device wifi connect "$GOPRO_SSID" password "$GOPRO_PASS" ifname "$WIFI_IF"
    fi
elif command -v wpa_supplicant >/dev/null 2>&1; then
    echo "  Usando wpa_supplicant..."
    WPA_CONF=$(mktemp /tmp/gopro-wpa-XXXX.conf)
    cat > "$WPA_CONF" <<EOF
network={
    ssid="$GOPRO_SSID"
    psk="$GOPRO_PASS"
    key_mgmt=WPA-PSK
}
EOF
    wpa_supplicant -i "$WIFI_IF" -c "$WPA_CONF" -B
    sleep 3
    rm -f "$WPA_CONF"
else
    echo "  ✗ Nessuno strumento WiFi trovato"
    echo "  Connettiti manualmente alla rete $GOPRO_SSID"
    read -p "  Premi Enter quando connesso..."
fi
echo ""

# ─── 3. DHCP ─────────────────────────────────────────────────

echo "[3/5] Ottieni IP via DHCP..."
dhclient "$WIFI_IF" 2>/dev/null || udhcpc -i "$WIFI_IF" 2>/dev/null || true
echo ""

# ─── 4. Verifica GoPro e stato pairing ───────────────────────

echo "[4/5] Verifica GoPro..."

if curl -s --connect-timeout 3 "http://$GOPRO_IP/gp/gpControl/status" >/dev/null 2>&1; then
    echo "  ✓ GoPro raggiungibile"

    # Controlla se pairing è già fatto
    if check_pairing_done; then
        echo "  ✓ Pairing già completato (client connesso)"
        echo ""
        echo "Connessione stabilita! Avvia lo streaming:"
        echo "  ./scripts/start.sh"
        exit 0
    fi

    # GoPro risponde ma nessun client connesso → chiedi
    echo "  ⚠ GoPro raggiungibile ma nessun client connesso"
    echo ""
    echo "  Serve il pairing? (la rete potrebbe scadere tra 2 minuti)"
    echo "  Se hai già fatto il pairing in precedenza, rispondi 'n'"
    echo ""
    read -p "  Serve il pairing? (s/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        exec "$SCRIPT_DIR/gopro-pair.sh"
    else
        echo "  Ok, continua senza pairing."
        echo ""
        echo "Avvia lo streaming:"
        echo "  ./scripts/start.sh"
    fi
else
    echo "  ❌ GoPro non raggiungibile"
    echo ""
    echo "Possibili cause:"
    echo "  1. La GoPro non è accesa"
    echo "  2. Il WiFi non è attivo (premi pulsante WiFi)"
    echo "  3. Serve il pairing → esegui: ./scripts/gopro-pair.sh"
    echo ""
    read -p "  Vuoi avviare il pairing? (s/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        exec "$SCRIPT_DIR/gopro-pair.sh"
    fi
fi

echo ""
echo "[5/5] Stato finale:"
echo ""
echo "  GoPro:  $GOPRO_IP"
echo "  Rete:   $GOPRO_SSID"
echo ""
