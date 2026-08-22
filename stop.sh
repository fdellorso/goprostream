#!/bin/bash
# GoPro Streaming Server — Stop
# Ferma tutti i container.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== GoPro Streaming Server — Stop ==="
echo ""

podman-compose down 2>/dev/null || docker-compose down

echo ""
echo "=== Container fermati ==="
echo ""
