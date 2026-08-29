#!/bin/bash
# watch-stream.sh — Monitoraggio continua dello streaming
# Logga stato container, GoPro, nginx, HLS, supervisore, keepalive, zombie ogni 30s
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
    local active
    active=$(pgrep -a ffmpeg 2>/dev/null | grep -v defunct)
    if [ -n "$active" ]; then
        echo "$active" | tee -a "$LOG_FILE"
    else
        echo "(non attivo)" | tee -a "$LOG_FILE"
    fi
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

check_zombies() {
    log "--- Zombie ---"
    local ffmpeg_zombies
    ffmpeg_zombies=$(pgrep -c -f "ffmpeg.*defunct" 2>/dev/null || echo "0")
    local total_zombies
    total_zombies=$(ps aux 2>/dev/null | awk '$8 ~ /Z/ {count++} END {print count+0}')
    echo "FFmpeg zombie: $ffmpeg_zombies | Totali sistema: $total_zombies" | tee -a "$LOG_FILE"
    log ""
}

check_supervisor() {
    log "--- Supervisore ---"
    local last_lines
    last_lines=$(podman logs goprostream --tail 5 2>&1)
    local supervisor_lines
    supervisor_lines=$(echo "$last_lines" | grep -i "supervisore\|keepalive\|morto\|restart" | tail -3)
    if [ -n "$supervisor_lines" ]; then
        echo "$supervisor_lines" | tee -a "$LOG_FILE"
    else
        echo "(nessun warning negli ultimi 5 log)" | tee -a "$LOG_FILE"
    fi
    log ""
}

check_keepalive() {
    log "--- KeepAlive ---"
    local ka_status
    ka_status=$(podman logs goprostream 2>&1 | grep -i "keepalive" | tail -2)
    if [ -n "$ka_status" ]; then
        echo "$ka_status" | tee -a "$LOG_FILE"
    else
        echo "(nessun log keepalive)" | tee -a "$LOG_FILE"
    fi
    log ""
}

echo "=== watch-stream avviato (intervallo: ${INTERVAL}s) ===" | tee -a "$LOG_FILE"
echo "=== Log: $LOG_FILE ===" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

while true; do
    log "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
    check_container
    check_ffmpeg
    check_zombies
    check_supervisor
    check_keepalive
    check_gopro
    check_rtmp
    check_hls_endpoint
    check_hls_files
    check_hls_disk
    log "--- fine check ---"
    log ""
    sleep "$INTERVAL"
done
