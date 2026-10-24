#!/usr/bin/env bash
# Compila un APK de debug que apunta al backend local a través de un túnel temporal de Cloudflare.
# Requisitos: backend corriendo en local y cloudflared instalado. Puerto por defecto 8000; otro con PORT=8001.
# La dirección del túnel cambia cada vez: si se cierra, hay que volver a correr el script e instalar el APK nuevo.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$(mktemp)"
PORT="${PORT:-8000}"
CLOUDFLARED="${CLOUDFLARED:-cloudflared}"
BACKEND="http://127.0.0.1:$PORT"

curl -sf "$BACKEND/health" >/dev/null || {
  echo "El backend no responde en $BACKEND. Levántelo primero."
  exit 1
}

"$CLOUDFLARED" tunnel --no-autoupdate --url "$BACKEND" >"$LOG" 2>&1 &
TUNNEL_PID=$!
trap 'kill $TUNNEL_PID 2>/dev/null || true' EXIT INT TERM

echo "Abriendo el túnel..."
URL=""
for _ in $(seq 1 30); do
  URL="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG" | head -1 || true)"
  [ -n "$URL" ] && break
  sleep 1
done
if [ -z "$URL" ]; then
  echo "No se obtuvo la dirección del túnel:"
  cat "$LOG"
  exit 1
fi

for _ in $(seq 1 30); do
  curl -sf "$URL/health" >/dev/null && break
  sleep 2
done

echo "Compilando el APK contra $URL/api/v1/ ..."
(cd "$ROOT/movil" && ./gradlew assembleDebug -q -PapiBaseUrl="$URL/api/v1/")
DEST="$HOME/Downloads/solventa-local.apk"
cp "$ROOT/movil/app/build/outputs/apk/debug/app-debug.apk" "$DEST"

echo
echo "APK listo: $DEST"
echo "Backend por el túnel: $URL"
echo "Deje esta ventana abierta mientras prueba. Ctrl+C cierra el túnel."
wait $TUNNEL_PID
