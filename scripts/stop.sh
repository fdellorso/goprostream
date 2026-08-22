#!/bin/bash
# GoPro Streaming Server — Stop
# Ferma tutti i container.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

COMPOSE="podman-compose -f docker/docker-compose.yml"

echo "=== GoPro Streaming Server — Stop ==="
echo ""

$COMPOSE down

echo ""
echo "=== Container fermati ==="
echo ""
