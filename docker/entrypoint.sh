#!/bin/sh
# Genera nginx.conf da template con envsubst

# Variabili di default
export SERVER_NAME="${SERVER_NAME:-ouya.fritz.box}"
export GOPRO_IP="${GOPRO_IP:-10.5.5.9}"

# Genera configurazione
envsubst '${SERVER_NAME} ${GOPRO_IP}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

echo "nginx.conf generato:"
echo "  SERVER_NAME: ${SERVER_NAME}"
echo "  GOPRO_IP: ${GOPRO_IP}"

# Esegui nginx
exec nginx -g 'daemon off;'
