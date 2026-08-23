#!/bin/bash
# watch-stream.sh — Monitoraggio continua dello streaming
# Logga stato container, GoPro, nginx, HLS ogni 30s
# Uso: ./scripts/watch-stream.sh [&]

LOG_FILE="/tmp/watch-stream.log"
INTERVAL=30

GOPRO_IP="${GOPRO_IP:-10.5.5.9}"
HLS_URL="http://localhost:8080/hls/gopro.m3u8"
STAT_URL="http://localhost:8080/stat"
GOPRO_URL="http://${GOPRO_IP}/gp/gpControl/status"

log() {
    echo "$1" | tee -a "$LOG_FILE"
}

check_container() {
    log "--- Container ---"
    podman stats --no-stream goprostream nginx-rtmp 2>&1 | tee -a "$LOG_FILE"
    log ""
}

check_ffmpeg() {
    log "--- FFmpeg ---"
    pgrep -a ffmpeg 2>&1 | tee -a "$LOG_FILE" || echo "(non attivo)" | tee -a "$LOG_FILE"
    log ""
}

check_gopro() {
    log "--- GoPro ---"
    curl -s --max-time 3 "$GOPRO_URL" 2>&1 | tee -a "$LOG_FILE" || echo "(non raggiungibile)" | tee -a "$LOG_FILE"
    log ""
}

check_rtmp() {
    log "--- RTMP stat ---"
    local stat
    stat=$(curl -s --max-time 3 "$STAT_URL" 2>&1)
    if [ $? -eq 0 ] && echo "$stat" | grep -q "<name>"; then
        local names
        names=$(echo "$stat" | grep -oP '<name>\K[^<]+' | tr '\n' ', ' | sed 's/,$//')
        local active
        active=$(echo "$stat" | grep -oP '<active>\K[^<]+' | head -1)
        echo "publishers: $names (active=$active)" | tee -a "$LOG_FILE"
    else
        echo "(nessun publisher o non raggiungibile)" | tee -a "$LOG_FILE"
    fi
    log ""
}

check_hls_endpoint() {
    log "--- HLS endpoint ---"
    local http_code
    http_code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$HLS_URL" 2>&1)
    echo "HTTP $http_code" | tee -a "$LOG_FILE"
    log ""
}

check_hls_files() {
    log "--- HLS files (nginx container) ---"
    podman exec nginx-rtmp ls -la /mnt/hls/ 2>&1 | tail -10 | tee -a "$LOG_FILE"
    log ""
}

check_hls_disk() {
    log "--- HLS disk ---"
    podman exec nginx-rtmp df -h /mnt/hls 2>&1 | tee -a "$LOG_FILE"
    log ""
}

echo "=== watch-stream avviato (intervallo: ${INTERVAL}s) ===" | tee -a "$LOG_FILE"
echo "=== Log: $LOG_FILE ===" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

while true; do
    log "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
    check_container
    check_ffmpeg
    check_gopro
    check_rtmp
    check_hls_endpoint
    check_hls_files
    check_hls_disk
    log "--- fine check ---"
    log ""
    sleep "$INTERVAL"
done
