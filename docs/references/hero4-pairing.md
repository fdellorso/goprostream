# HERO4 Pairing Senza App — Guida Completa

> **Source**: Informazioni testate su HERO4 Black (GP26479007)
> **Problema**: GoPro Quik (Android) non riesce a completare il pairing
> **Soluzione**: Pairing manuale via HTTP API

## Il Problema

La GoPro Hero 4 Black, dopo un reset WiFi o un primo utilizzo, richiede un **pairing** con un dispositivo prima di creare una rete WiFi permanente. Senza pairing concluso:

- La rete WiFi (`GP<numero_seriale>`) appare **solo per ~2 minuti** dopo l'accensione
- Dopo 2 minuti l'AP si disattiva automaticamente
- Non c'è rete WiFi permanente

## Credenziali

| Parametro | Valore |
|-----------|--------|
| SSID | `GP<numero_seriale>` (es. `GP26479007`) |
| Password | `goprohero` (default di fabbrica) |
| IP Gateway | `10.5.5.9` |
| Subnet | `255.255.255.0` |

> **Nota**: Il SSID contiene il numero di serie della GoPro, visibile sul display o dallo status JSON (`status.30`).

## Processo di Pairing via HTTP

### Prerequisiti

1. La GoPro deve essere accesa e in modalità WiFi (pulsante WiFi premuto)
2. La rete `GP<numero_seriale>` deve essere visibile
3. L'OUYA deve essere connesso a quella rete
4. Il **PIN a 4 cifre** deve essere visibile sul display della GoPro

### Step 1: Connettersi alla rete GoPro

```bash
# Da OUYA
nmcli device wifi connect GP26479007 password goprohero
```

### Step 2: Verificare connessione

```bash
curl -s http://10.5.5.9/gp/gpControl/status
```

Se risponde con JSON, la connessione è attiva.

### Step 3: Iniziare il pairing

```bash
# Il PIN va letto dal display della GoPro
curl -sk "https://10.5.5.9/gpPair?c=start&pin=XXXX&mode=0"
```

**Risposta attesa** (password generata):
```json
{
  "password": "XXXXXXXXXXXXXXXX"
}
```

> **Nota**: `curl -k` serve perché la GoPro usa un certificato SSL self-signed.

### Step 4: Concludere il pairing

```bash
curl -sk "https://10.5.5.9/gpPair?c=finish&pin=XXXX&mode=0"
```

**Risposta attesa**:
```json
{}
```

### Step 5: Verificare il pairing

```bash
curl -s http://10.5.5.9/gp/gpControl/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'WiFi mode: {d[\"settings\"][\"63\"]}')  # 1 = App mode
print(f'Client: {d[\"status\"][\"31\"]}')
"
```

## Script Automatico

```bash
#!/bin/bash
# gopro-pair.sh — Pairing GoPro via HTTP

PIN="${1:?Usage: $0 <PIN>}"
GOPRO_IP="10.5.5.9"

echo "Pairing con PIN: $PIN"

echo "[1/2] Inizio pairing..."
curl -sk "https://$GOPRO_IP/gpPair?c=start&pin=$PIN&mode=0"

echo ""
echo "[2/2] Fine pairing..."
curl -sk "https://$GOPRO_IP/gpPair?c=finish&pin=$PIN&mode=0"

echo ""
echo "Verifica stato..."
curl -s "http://$GOPRO_IP/gpgpControl/status" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'WiFi mode: {d[\"settings\"][\"63\"]}')"
```

## Troubleshooting

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| `curl: (60) SSL certificate problem` | Certificato self-signed | Usare `curl -k` |
| `Connection refused` | GoPro non in pairing mode | Premere pulsante WiFi |
| Pairing fallisce | PIN errato | Verificare PIN sul display |
| Password non funziona | Pairing non concluso | Ripetere il processo |
| Rete sparisce dopo 2 minuti | Pairing non completato | Completare entro 2 minuti |

## Note Importanti

- Il pairing va fatto **una sola volta** per dispositivo
- Dopo il pairing, la rete WiFi rimane attiva quando la GoPro è accesa
- Il PIN cambia ad ogni sessione di pairing
- La password generata dal pairing (`gpPair` response) è diversa da `goprohero`
- `goprohero` è la password della rete WiFi, non del pairing
