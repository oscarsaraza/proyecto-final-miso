#!/usr/bin/env bash
# Ejecuta E1 tres veces: fase base (proveedor a 50 ms) y fase degradada (900 ms + 20% de error).
set -euo pipefail
cd "$(dirname "$0")"
RED=e1-latencia_default

docker compose build --quiet
DIR_SALIDA="${DIR_SALIDA:-resultados}"
mkdir -p "$DIR_SALIDA" && chmod 777 "$DIR_SALIDA"

for corrida in 1 2 3; do
  echo "== Corrida $corrida · fase base (proveedor 50 ms) =="
  LATENCY_MS=50 ERROR_RATE=0 docker compose up -d --force-recreate
  sleep 5
  docker run --rm -i --network "$RED" -v "$PWD/k6:/scripts" -v "$PWD/$DIR_SALIDA:/salida" \
    -e ITERACIONES=100 -e NOMBRE_SALIDA=base-$corrida grafana/k6 run /scripts/cotizacion.js

  echo "== Corrida $corrida · fase degradada (proveedor 900 ms, 20% error) =="
  LATENCY_MS=900 ERROR_RATE=0.2 docker compose up -d --force-recreate provider-sim
  docker compose restart api   # limpia la caché para que la fase degradada golpee al proveedor
  sleep 5
  docker run --rm -i --network "$RED" -v "$PWD/k6:/scripts" -v "$PWD/$DIR_SALIDA:/salida" \
    -e ITERACIONES=500 -e NOMBRE_SALIDA=degradada-$corrida grafana/k6 run /scripts/cotizacion.js
done

docker compose logs api > "$DIR_SALIDA/api-logs.txt"
docker compose down
echo "Listo. Resultados en $DIR_SALIDA/"

