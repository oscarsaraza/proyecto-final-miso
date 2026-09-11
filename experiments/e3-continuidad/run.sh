#!/usr/bin/env bash
# Carga constante de 50 req/s durante 3 min. A los 45 s se detiene la réplica A y a los 165 s se restaura.
# Uso: ./run.sh <numero-de-corrida> [v1|v2]
set -euo pipefail
cd "$(dirname "$0")"
CORRIDA="${1:?indique el número de corrida}"
VERSION="${2:-v2}"
RED=e3-continuidad_default

case "$VERSION" in
  v1) export NGINX_CONF=./nginx-v1-pasivo.conf ;;
  v2) export NGINX_CONF=./nginx.conf ;;
  *)  echo "versión inválida, use v1 o v2" >&2; exit 1 ;;
esac

docker compose build --quiet
mkdir -p resultados && chmod 777 resultados

echo "== Corrida $CORRIDA con la configuración $VERSION =="
docker compose up -d --force-recreate
sleep 8

(
  sleep 45
  echo "  [$(date +%T)] deteniendo replica-A"
  docker stop --time 0 e3-api-a >/dev/null
  sleep 120
  echo "  [$(date +%T)] restaurando replica-A"
  docker start e3-api-a >/dev/null
) &
guion=$!

docker run --rm -i --network "$RED" -v "$PWD/k6:/scripts" -v "$PWD/resultados:/salida" \
  -e NOMBRE_SALIDA=$VERSION-corrida-$CORRIDA grafana/k6 run --quiet /scripts/carga.js

wait $guion
docker logs e3-nginx > "resultados/$VERSION-nginx-$CORRIDA.log" 2>&1 || true
docker compose down >/dev/null 2>&1
echo "Corrida $CORRIDA lista"
