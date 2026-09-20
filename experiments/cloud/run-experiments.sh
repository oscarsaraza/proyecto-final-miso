#!/usr/bin/env bash
# run-experiments.sh: Orquestador local de experimentos de arquitectura en AWS Cloud
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ_PROYECTO="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIR_TERRAFORM="$SCRIPT_DIR/terraform"
DIR_EVIDENCIAS="$SCRIPT_DIR/evidencias"
mkdir -p "$DIR_EVIDENCIAS"

CLEANUP_DONE=0

cleanup() {
  if [ "$CLEANUP_DONE" -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo " [SALVAGUARDA DE COSTOS] Ejecutando terraform destroy..."
    echo "============================================================"
    cd "$DIR_TERRAFORM"
    if [ -f "terraform.tfstate" ]; then
      DESTROY_LOG="$DIR_EVIDENCIAS/terraform-destroy-$(date +%Y%m%d_%H%M%S).log"
      terraform destroy -auto-approve 2>&1 | tee "$DESTROY_LOG" || true
      echo "✓ Recursos destruidos. Registro guardado en $DESTROY_LOG"
    fi
    CLEANUP_DONE=1
  fi
}
trap cleanup EXIT INT TERM

echo "============================================================"
echo " SOLVENTA · ORQUESTADOR DE EXPERIMENTOS EN AWS CLOUD (E1, E3)"
echo "============================================================"

# 1. Comprobación de herramientas locales requeridas
echo "[1/7] Comprobando herramientas locales..."
for cmd in aws terraform ssh scp rsync python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: La herramienta '$cmd' no está instalada o no está en el PATH." >&2
    exit 1
  fi
done
echo "  ✓ Herramientas encontradas: aws, terraform, ssh, scp, rsync, python3"

# 2. Comprobación de credenciales activas de AWS
echo "[2/7] Verificando sesión en AWS..."
if ! CALLER_ID=$(aws sts get-caller-identity --output json 2>/dev/null); then
  echo "" >&2
  echo "ERROR: Las credenciales de AWS no son válidas o han expirado." >&2
  echo "Por favor, exporta o configura tus credenciales antes de continuar:" >&2
  echo "  export AWS_ACCESS_KEY_ID='tu_access_key'" >&2
  echo "  export AWS_SECRET_ACCESS_KEY='tu_secret_key'" >&2
  echo "  export AWS_DEFAULT_REGION='us-east-1'" >&2
  echo "  # (Si usas credenciales temporales STS / ASIA..., exporta también: export AWS_SESSION_TOKEN='...')" >&2
  echo "O ejecuta: aws configure" >&2
  exit 1

fi

ACCOUNT_ID=$(echo "$CALLER_ID" | python3 -c "import sys, json; print(json.load(sys.stdin).get('Account', ''))")
ARN=$(echo "$CALLER_ID" | python3 -c "import sys, json; print(json.load(sys.stdin).get('Arn', ''))")
echo "  ✓ Conectado a AWS Cuenta: $ACCOUNT_ID (Identidad: $ARN)"

# 3. Detección de IP pública del operador para seguridad
echo "[3/7] Detectando IP pública del operador para restringir SSH..."
OPERATOR_IP=$(curl -s https://checkip.amazonaws.com 2>/dev/null || curl -s https://ifconfig.me 2>/dev/null || echo "")
if [ -n "$OPERATOR_IP" ]; then
  OPERATOR_CIDR="${OPERATOR_IP}/32"
  echo "  ✓ Acceso SSH restringido a la IP del operador: $OPERATOR_CIDR"
else
  OPERATOR_CIDR="0.0.0.0/0"
  echo "  ! No se pudo detectar la IP pública, usando 0.0.0.0/0"
fi

# 4. Aprovisionamiento con Terraform
echo "[4/7] Aprovisionando infraestructura efímera en AWS con Terraform..."
cd "$DIR_TERRAFORM"
terraform init -upgrade
terraform apply -auto-approve -var="operator_cidr=$OPERATOR_CIDR"

INSTANCE_IP=$(terraform output -raw instance_public_ip)
INSTANCE_ID=$(terraform output -raw instance_id)
SSH_KEY="$DIR_TERRAFORM/id_rsa_experiments.pem"
chmod 600 "$SSH_KEY"

echo "  ✓ Instancia aprovisionada:"
echo "      ID: $INSTANCE_ID"
echo "      IP Pública: $INSTANCE_IP"

# 5. Esperar a que la instancia complete cloud-init y Docker
echo "[5/7] Esperando inicialización de la instancia y Docker (cloud-init)..."
MAX_ATTEMPTS=60
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@"$INSTANCE_IP" "test -f /home/ubuntu/.cloud-init-ready" >/dev/null 2>&1; then
    echo "  ✓ Instancia lista y aprovisionada con Docker CE."
    break
  fi
  ATTEMPT=$((ATTEMPT + 1))
  echo "  Esperando configuración de paquetes y Docker ($ATTEMPT/$MAX_ATTEMPTS)..."
  sleep 5
done

if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
  echo "ERROR: La instancia no respondió a tiempo durante el inicio." >&2
  exit 1
fi

# 6. Sincronizar experimentos y ejecutar suite remota
echo "[6/7] Sincronizando repositorio y ejecutando suite de experimentos en AWS..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@"$INSTANCE_IP" "mkdir -p /home/ubuntu/solventa/experiments"

rsync -avz -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
  --exclude '.terraform' \
  --exclude '*.pem' \
  --exclude '*.tfstate*' \
  --exclude '__pycache__' \
  --exclude 'resultados/nube' \
  "$RAIZ_PROYECTO/experiments/" ubuntu@"$INSTANCE_IP":/home/ubuntu/solventa/experiments/

echo "  -> Iniciando ejecución de remote-runner.sh en la instancia..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@"$INSTANCE_IP" \
  "bash /home/ubuntu/solventa/experiments/cloud/scripts/remote-runner.sh"

# 7. Descargar paquete de evidencias y extraer
echo "[7/7] Descargando evidencias de auditoría desde la nube..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
  ubuntu@"$INSTANCE_IP":/home/ubuntu/solventa/experiments/cloud/evidencias-nube.tar.gz \
  "$SCRIPT_DIR/evidencias-nube.tar.gz"

echo "  -> Extrayendo evidencias en el repositorio..."
tar -xzf "$SCRIPT_DIR/evidencias-nube.tar.gz" -C "$RAIZ_PROYECTO/experiments/"
rm -f "$SCRIPT_DIR/evidencias-nube.tar.gz"

echo "  -> Procesando comparativa local vs nube con resumir.py..."
cd "$RAIZ_PROYECTO/experiments"
python3 resumir.py

# Destrucción controlada de recursos
echo ""
echo "============================================================"
echo " Desmantelando infraestructura efímera en AWS..."
echo "============================================================"
cd "$DIR_TERRAFORM"
DESTROY_LOG="$DIR_EVIDENCIAS/terraform-destroy-$(date +%Y%m%d_%H%M%S).log"
terraform destroy -auto-approve 2>&1 | tee "$DESTROY_LOG"
CLEANUP_DONE=1

echo ""
echo "============================================================"
echo " EJECUCIÓN EN LA NUBE COMPLETADA CON ÉXITO"
echo " Evidencias locales:"
echo "   - E1 Nube: experiments/e1-latencia/resultados/nube/"
echo "   - E3 Nube: experiments/e3-continuidad/resultados/nube/"
echo "   - Auditoría: experiments/cloud/evidencias/"
echo "   - Constancia destrucción: $DESTROY_LOG"
echo "============================================================"
