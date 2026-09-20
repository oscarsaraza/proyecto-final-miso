#!/usr/bin/env bash
# setup-iam-user.sh: Crea un usuario IAM con los permisos requeridos para los experimentos de Solventa
set -euo pipefail

USUARIO_IAM="${1:-solventa-experiments}"
POLITICA_ARN="arn:aws:iam::aws:policy/AmazonEC2FullAccess"

echo "============================================================"
echo " CONFIGURACIÓN DE USUARIO IAM PARA EXPERIMENTOS EN AWS"
echo " Usuario a crear: $USUARIO_IAM"
echo "============================================================"

# 1. Verificar que la CLI esté configurada con permisos administrativos (ej. root)
echo "[1/4] Verificando permisos actuales..."
CALLER=$(aws sts get-caller-identity --output json 2>/dev/null || true)
if [ -z "$CALLER" ]; then
  echo "ERROR: No hay credenciales de AWS activas. Configura tus credenciales administrativas con 'aws configure'." >&2
  exit 1
fi

ARN_ACTUAL=$(echo "$CALLER" | python3 -c "import sys, json; print(json.load(sys.stdin).get('Arn', ''))")
echo "  ✓ Ejecutando con identidad: $ARN_ACTUAL"

# 2. Crear usuario IAM si no existe
echo "[2/4] Creando usuario IAM '$USUARIO_IAM'..."
if aws iam get-user --user-name "$USUARIO_IAM" >/dev/null 2>&1; then
  echo "  ✓ El usuario '$USUARIO_IAM' ya existe."
else
  aws iam create-user --user-name "$USUARIO_IAM" >/dev/null
  echo "  ✓ Usuario '$USUARIO_IAM' creado exitosamente."
fi

# 3. Adjuntar la política requerida (AmazonEC2FullAccess)
echo "[3/4] Adjuntando política de permisos requerida (AmazonEC2FullAccess)..."
aws iam attach-user-policy \
  --user-name "$USUARIO_IAM" \
  --policy-arn "$POLITICA_ARN"
echo "  ✓ Política '$POLITICA_ARN' adjuntada."

# 4. Generar clave de acceso (Access Key ID y Secret Access Key)
echo "[4/4] Generando claves de acceso CLI..."
CLAVES=$(aws iam create-access-key --user-name "$USUARIO_IAM" --query 'AccessKey.[AccessKeyId,SecretAccessKey]' --output text)

ACCESS_KEY_ID=$(echo "$CLAVES" | awk '{print $1}')
SECRET_ACCESS_KEY=$(echo "$CLAVES" | awk '{print $2}')

echo ""
echo "============================================================"
echo " ¡USUARIO IAM Y CREDENCIALES GENERADAS CON ÉXITO!"
echo "============================================================"
echo ""
echo "Copia y pega los siguientes comandos en tu terminal para activar"
echo "las credenciales antes de ejecutar 'run-experiments.sh':"
echo ""
echo "export AWS_ACCESS_KEY_ID=\"$ACCESS_KEY_ID\""
echo "export AWS_SECRET_ACCESS_KEY=\"$SECRET_ACCESS_KEY\""
echo "export AWS_DEFAULT_REGION=\"us-east-1\""
echo "unset AWS_SESSION_TOKEN"
echo ""
echo "Para verificar la conexión con este nuevo usuario:"
echo "aws sts get-caller-identity"
echo "============================================================"
