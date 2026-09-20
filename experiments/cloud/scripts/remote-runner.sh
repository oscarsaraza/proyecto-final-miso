#!/usr/bin/env bash
# remote-runner.sh: Ejecuta la suite de experimentos E1 y E3 en la instancia EC2 de AWS
set -euo pipefail

RAIZ_EXP="/home/ubuntu/solventa/experiments"
DIR_EVIDENCIAS="$RAIZ_EXP/cloud/evidencias"
mkdir -p "$DIR_EVIDENCIAS"

echo "============================================================"
echo " INICIANDO EJECUCIÓN REMOTA DE EXPERIMENTOS EN AWS EC2"
echo " Fecha UTC: $(date -u +'%Y-%m-%d %H:%M:%SZ')"
echo "============================================================"

# 1. Esperar que Docker esté listo
echo "[1/6] Verificando Docker y entorno..."
while ! docker info >/dev/null 2>&1; do
  echo "  Esperando a que Docker inicie..."
  sleep 3
done
echo "  ✓ Docker daemon operativo: $(docker --version)"

# 2. Recolección de Metadatos de Auditoría de la Nube (AWS IMDSv2 y Host)
echo "[2/6] Recolectando metadatos de auditoría en AWS..."
TOKEN=$(curl -s -f -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null || true)

INSTANCE_ID="desconocido"
INSTANCE_TYPE="desconocido"
AMI_ID="desconocido"
AZ="desconocido"

if [ -n "$TOKEN" ]; then
  INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "n/a")
  INSTANCE_TYPE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type 2>/dev/null || echo "n/a")
  AMI_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/ami-id 2>/dev/null || echo "n/a")
  AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone 2>/dev/null || echo "n/a")
fi

cat <<METADATA_EOF > "$DIR_EVIDENCIAS/ec2-metadata.json"
{
  "timestamp_inicio_utc": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "aws": {
    "instance_id": "$INSTANCE_ID",
    "instance_type": "$INSTANCE_TYPE",
    "ami_id": "$AMI_ID",
    "availability_zone": "$AZ"
  },
  "host": {
    "hostname": "$(hostname)",
    "kernel": "$(uname -r)",
    "vcpus": $(nproc),
    "memoria_total_mb": $(free -m | awk '/^Mem:/{print $2}'),
    "docker_version": "$(docker --version | tr -d '\n')",
    "docker_compose_version": "$(docker compose version | tr -d '\n')"
  }
}
METADATA_EOF

lscpu > "$DIR_EVIDENCIAS/lscpu.txt" 2>&1 || true
free -h > "$DIR_EVIDENCIAS/free-memory.txt" 2>&1 || true
echo "  ✓ Metadatos guardados en $DIR_EVIDENCIAS/ec2-metadata.json"

# 3. Iniciar telemetría de consumo de recursos en segundo plano
echo "[3/6] Iniciando telemetría de recursos (docker stats)..."
STATS_LOG="$DIR_EVIDENCIAS/docker-stats.log"
(
  while true; do
    echo "--- $(date -u +'%Y-%m-%dT%H:%M:%SZ') ---" >> "$STATS_LOG"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" >> "$STATS_LOG" 2>/dev/null || true
    sleep 2
  done
) &
STATS_PID=$!
echo "  ✓ Sampler de recursos activo (PID: $STATS_PID)"

# 4. Ejecución del Experimento E1 (Latencia con proveedor degradado)
echo "[4/6] Ejecutando Experimento E1 (Latencia)..."
cd "$RAIZ_EXP/e1-latencia"
mkdir -p resultados/nube && chmod 777 resultados/nube

export DIR_SALIDA=resultados/nube
./run.sh | tee "$DIR_EVIDENCIAS/e1-execution.log"
echo "  ✓ Experimento E1 completado en la nube."

# 5. Ejecución del Experimento E3 (Continuidad ante caída de réplica)
echo "[5/6] Ejecutando Experimento E3 (Continuidad)..."
cd "$RAIZ_EXP/e3-continuidad"
mkdir -p resultados/nube && chmod 777 resultados/nube

export DIR_SALIDA=resultados/nube
# Ejecutar 3 corridas con v1 (línea base pasiva)
for c in 1 2 3; do
  echo "  -> Ejecutando E3 corrida $c con versión v1..."
  ./run.sh "$c" v1 | tee -a "$DIR_EVIDENCIAS/e3-execution.log"
  sleep 5
done

# Ejecutar 3 corridas con v2 (solución propuesta con proxy_next_upstream)
for c in 1 2 3; do
  echo "  -> Ejecutando E3 corrida $c con versión v2..."
  ./run.sh "$c" v2 | tee -a "$DIR_EVIDENCIAS/e3-execution.log"
  sleep 5
done
echo "  ✓ Experimento E3 completado en la nube."

# 6. Detener telemetría y consolidar métricas
echo "[6/6] Finalizando telemetría y consolidando resultados..."
kill "$STATS_PID" 2>/dev/null || true
wait "$STATS_PID" 2>/dev/null || true

cd "$RAIZ_EXP"
python3 resumir.py | tee "$DIR_EVIDENCIAS/resumen-comparativo.txt"

# Empaquetar artefactos para descarga
echo "Empaquetando evidencias..."
tar -czf "$RAIZ_EXP/cloud/evidencias-nube.tar.gz" \
  e1-latencia/resultados/nube \
  e3-continuidad/resultados/nube \
  cloud/evidencias

echo "============================================================"
echo " EJECUCIÓN EN LA NUBE FINALIZADA CON ÉXITO"
echo " Archivo de evidencias: $RAIZ_EXP/cloud/evidencias-nube.tar.gz"
echo "============================================================"
