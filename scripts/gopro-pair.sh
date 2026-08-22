#!/bin/bash
# GoPro Pairing — Primo collegamento senza app
# Guida l'utente nel processo di pairing via HTTP.
#
# Lo script:
# 1. Verifica se la GoPro è già raggiungibile (pairing già fatto)
# 2. Se non lo è, controlla se la rete GPxxx è visibile
# 3. Chiede il PIN all'utente e completa il pairing

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# ─── Configurazione ──────────────────────────────────────────

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

GOPRO_IP="${GOPRO_IP:-10.5.5.9}"
GOPRO_PASS="${GOPRO_PASS:-goprohero}"

# ─── Funzioni ────────────────────────────────────────────────

check_gopro() {
    curl -s --connect-timeout 3 "http://$GOPRO_IP/gp/gpControl/status" >/dev/null 2>&1
}

get_gopro_name() {
    curl -s --connect-timeout 3 "http://$GOPRO_IP/gp/gpControl/status" 2>/dev/null | \
        python3 -c "import sys,json; print(json.load(sys.stdin)['status']['30'])" 2>/dev/null || echo "sconosciuto"
}

scan_gopro_network() {
    # Cerca una rete che inizia con GP
    nmcli device wifi list 2>/dev/null | grep -i "GP" | head -1 | awk '{print $1}'
}

connect_to_gopro() {
    local ssid="$1"
    nmcli device wifi connect "$ssid" password "$GOPRO_PASS" 2>/dev/null
}

do_pairing() {
    local pin="$1"
    echo "  Inizio pairing..."
    local result=$(curl -sk --connect-timeout 5 "https://$GOPRO_IP/gpPair?c=start&pin=$pin&mode=0" 2>&1)
    echo "  Risposta: $result"

    echo "  Fine pairing..."
    curl -sk --connect-timeout 5 "https://$GOPRO_IP/gpPair?c=finish&pin=$pin&mode=0" 2>&1
    echo ""

    # Verifica
    if check_gopro; then
        echo "  ✅ Pairing completato!"
        return 0
    else
        echo "  ⚠️  Pairing potrebbe non essere riuscito"
        return 1
    fi
}

# ─── Main ────────────────────────────────────────────────────

echo "=== GoPro Pairing ==="
echo ""

# 1. La GoPro è già raggiungibile?
echo "[1/4] Verifica GoPro..."
if check_gopro; then
    NAME=$(get_gopro_name)
    echo "  ✅ GoPro raggiungibile ($NAME)"
    echo "  Pairing già completato o non necessario."
    echo ""
    echo "Vuoi ripetere il pairing? (s/n)"
    read -r -p "> " repeat
    if [[ ! "$repeat" =~ ^[Ss]$ ]]; then
        echo "Ok, niente da fare."
        exit 0
    fi
else
    echo "  ❌ GoPro non raggiungibile su $GOPRO_IP"
fi
echo ""

# 2. La rete GPxxx è visibile?
echo "[2/4] Ricerca rete GoPro..."
SSID=$(scan_gopro_network)

if [ -z "$SSID" ]; then
    echo "  ❌ Nessuna rete GoPro trovata"
    echo ""
    echo "  Assicurati che:"
    echo "    1. La GoPro sia accesa"
    echo "    2. Il pulsante WiFi sia premuto (LED lampeggianti)"
    echo "    3. La rete GP<numero> sia visibile"
    echo ""
    echo "  Riprova quando la rete è disponibile."
    exit 1
fi

echo "  ✅ Rete trovata: $SSID"
echo ""

# 3. Connetti alla rete
echo "[3/4] Connessione alla rete $SSID..."
if connect_to_gopro "$SSID"; then
    echo "  ✅ Connesso"
else
    echo "  ❌ Connessione fallita"
    echo "  Prova: nmcli device wifi connect $SSID password $GOPRO_PASS"
    exit 1
fi
echo ""

# 4. Pairing
echo "[4/4] Pairing..."
echo ""
echo "  📌 Leggi il PIN a 4 cifre dal display della GoPro"
echo "  ⏰ Hai circa 2 minuti prima che la rete sparisca"
echo ""
read -r -p "  Inserisci il PIN: " PIN

if [ -z "$PIN" ]; then
    echo "  PIN vuoto. Annullato."
    exit 1
fi

echo ""
do_pairing "$PIN"

echo ""
echo "=== Finito ==="
echo ""
echo "Ora puoi avviare lo streaming:"
echo "  ./scripts/start.sh"
echo ""
