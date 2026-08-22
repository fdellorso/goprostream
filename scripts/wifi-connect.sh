#!/bin/bash
# GoPro WiFi Connect
# Si connette alla rete WiFi Direct della GoPro Hero 4.
#
# La GoPro crea una rete con SSID: GOPRO-BP-XXXX
# Password: goprohero
# IP GoPro: 10.5.5.9

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

echo "=== GoPro WiFi Connect ==="
echo ""
echo "SSID:     $GOPRO_SSID"
echo "Password: $GOPRO_PASS"
echo "Gateway:  $GOPRO_IP"
echo ""

# ─── Rileva interfaccia ──────────────────────────────────────

echo "[1/4] Rilevamento interfaccia WiFi..."

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

# ─── Connetti alla rete GoPro ────────────────────────────────

echo "[2/4] Connessione alla rete GoPro..."

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
    echo "  ✗ Nessuno strumento WiFi trovato (nmcli o wpa_supplicant)"
    echo "  Connettiti manualmente alla rete $GOPRO_SSID"
    read -p "  Premi Enter quando connesso..."
fi
echo ""

# ─── Ottieni IP via DHCP ─────────────────────────────────────

echo "[3/4] Ottieni IP via DHCP..."
dhclient "$WIFI_IF" 2>/dev/null || udhcpc -i "$WIFI_IF" 2>/dev/null || true
echo ""

# ─── Verifica connessione ────────────────────────────────────

echo "[4/4] Verifica connessione..."

if ping -c 1 -W 3 "$GOPRO_IP" >/dev/null 2>&1; then
    echo "  ✓ GoPro raggiungibile su $GOPRO_IP"
    echo ""
    echo "Connessione stabilita! Avvia lo streaming:"
    echo "  ./scripts/start.sh"
else
    echo "  ⚠ GoPro non raggiungibile"
    echo ""
    echo "Possibili cause:"
    echo "  1. La GoPro non è accesa"
    echo "  2. Il WiFi non è attivo sulla GoPro"
    echo "  3. La rete $GOPRO_SSID non è visibile"
    echo "  4. Indirizzo IP errato (default: $GOPRO_IP)"
    echo ""
    echo "Verifica manualmente:"
    echo "  ip addr show $WIFI_IF"
    echo "  ping $GOPRO_IP"
fi
