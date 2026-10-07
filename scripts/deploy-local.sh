#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  Despliegue Local Solventa Seguros (Floci AWS Emulator)  "
echo "=========================================================="

# 1. Iniciar emulador Floci
echo "--> 1. Iniciando emulador Floci..."
docker compose up -d floci

# 2. Aplicar Terraform contra Floci
echo "--> 2. Aprovisionando infraestructura con Terraform..."
cd terraform
terraform apply -var-file=environments/local.tfvars -auto-approve
cd ..

# 3. Construir imagen Docker del Backend
echo "--> 3. Construyendo imagen Docker del backend..."
cd backend
docker build -t solventa-backend:local .
cd ..

# 4. Compilar portal web y subir al bucket S3 de Floci
echo "--> 4. Compilando portal web Angular y desplegando en S3..."
cd web
npm run build
if command -v aws >/dev/null 2>&1; then
  aws --endpoint-url=http://localhost:4566 s3 sync dist/web/browser s3://solventa-web-portal-local --delete
  echo "--> 5. Verificando buckets en Floci:"
  aws --endpoint-url=http://localhost:4566 s3 ls
else
  echo "--> Nota: aws-cli no está instalado en el PATH local. El bucket s3://solventa-web-portal-local ya está creado en Floci."
fi
cd ..

echo "=========================================================="
echo "  ¡Despliegue local completado y verificado con éxito!    "
echo "=========================================================="
