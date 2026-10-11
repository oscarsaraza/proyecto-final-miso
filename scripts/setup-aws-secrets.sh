#!/usr/bin/env bash
# ==============================================================================
# Solventa - Script de Configuración de Secretos de AWS en GitHub Actions
# ==============================================================================
# Este script facilita la configuración de las credenciales de AWS (Usuario IAM)
# como secretos en el repositorio de GitHub mediante GitHub CLI (`gh`).
# ==============================================================================

set -eo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Repositorio por defecto derivado de git remote o fallback
get_default_repo() {
  local remote_url
  remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")
  if [[ "$remote_url" =~ github\.com[:/]([^/]+/[^/.]+)(\.git)?$ ]]; then
    echo "${BASH_REMATCH[1]}"
  else
    echo "oscarsaraza/proyecto-final-miso"
  fi
}

REPO="$(get_default_repo)"
AWS_REGION="us-east-1"
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""

mask_secret() {
  local val="$1"
  local len=${#val}
  if [ "$len" -le 8 ]; then
    echo "********"
  else
    local prefix="${val:0:4}"
    local suffix="${val: -4}"
    echo "${prefix}...${suffix}"
  fi
}

echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "${BLUE}${BOLD}   SOLVENTA: CONFIGURACIÓN DE SECRETOS AWS IAM EN GITHUB ACTIONS      ${NC}"
echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "Repositorio objetivo: ${CYAN}${REPO}${NC}\n"

# Cargar desde perfil de AWS CLI (~/.aws/credentials)
load_from_aws_profile() {
  local profile="${1:-default}"
  echo -e "Leyendo credenciales del perfil de AWS: ${YELLOW}${profile}${NC}..."
  
  if ! command -v aws &>/dev/null; then
    echo -e "${RED}AWS CLI ('aws') no está instalado en el sistema.${NC}"
    return 1
  fi

  AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id --profile "$profile" 2>/dev/null || true)
  AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key --profile "$profile" 2>/dev/null || true)
  local profile_region
  profile_region=$(aws configure get region --profile "$profile" 2>/dev/null || true)
  if [ -n "$profile_region" ]; then
    AWS_REGION="$profile_region"
  fi

  if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo -e "${RED}No se encontraron credenciales válidas en el perfil '${profile}'.${NC}"
    return 1
  fi
  return 0
}

# Selección del método de ingreso
if [ -n "$1" ] && [ "$1" == "--profile" ]; then
  load_from_aws_profile "${2:-default}"
elif [ -n "$ENV_AWS_ACCESS_KEY_ID" ]; then
  AWS_ACCESS_KEY_ID="$ENV_AWS_ACCESS_KEY_ID"
  AWS_SECRET_ACCESS_KEY="$ENV_AWS_SECRET_ACCESS_KEY"
  AWS_REGION="${ENV_AWS_REGION:-us-east-1}"
else
  echo -e "Selecciona el método de obtención de credenciales de AWS:"
  echo -e "  ${BOLD}1)${NC} Ingreso manual interactivo (Access Key y Secret Access Key de IAM)"
  echo -e "  ${BOLD}2)${NC} Cargar desde perfil local de AWS CLI (~/.aws/credentials)"
  read -r -p "Opción [1-2, por defecto 1]: " OPTION
  OPTION="${OPTION:-1}"

  case "$OPTION" in
    1)
      echo ""
      read -r -p "Introduce AWS_ACCESS_KEY_ID (ej. AKIA...): " AWS_ACCESS_KEY_ID
      read -r -s -p "Introduce AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY
      echo ""
      read -r -p "Introduce AWS_REGION [us-east-1]: " INPUT_REGION
      AWS_REGION="${INPUT_REGION:-us-east-1}"
      ;;
    2)
      read -r -p "Nombre del perfil de AWS [default]: " PROFILE_NAME
      PROFILE_NAME="${PROFILE_NAME:-default}"
      load_from_aws_profile "$PROFILE_NAME"
      ;;
    *)
      echo -e "${RED}Opción no válida.${NC}"
      exit 1
      ;;
  esac
fi

# Validación de parámetros mínimos
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo -e "\n${RED}Error: AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY son obligatorios.${NC}"
  exit 1
fi

echo -e "\n${GREEN}Credenciales IAM registradas para configuración:${NC}"
echo -e "  - AWS_REGION:            ${CYAN}${AWS_REGION}${NC}"
echo -e "  - AWS_ACCESS_KEY_ID:     ${CYAN}$(mask_secret "$AWS_ACCESS_KEY_ID")${NC}"
echo -e "  - AWS_SECRET_ACCESS_KEY: ${CYAN}$(mask_secret "$AWS_SECRET_ACCESS_KEY")${NC}"

# Verificación de credenciales con AWS STS (si aws cli está disponible)
if command -v aws &>/dev/null; then
  echo -e "\n${YELLOW}Validando credenciales en AWS STS...${NC}"
  set +e
  CALLER_ID=$(
    AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    AWS_DEFAULT_REGION="$AWS_REGION" \
    aws sts get-caller-identity 2>&1
  )
  STS_STATUS=$?
  set -e
  if [ $STS_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ Autenticación exitosa en AWS:${NC}"
    echo "$CALLER_ID" | grep -E "(Arn|Account|UserId)" || echo "$CALLER_ID"
  else
    echo -e "${YELLOW}Advertencia: No se pudo verificar la identidad con STS:${NC}"
    echo -e "$CALLER_ID"
    read -r -p "¿Deseas continuar configurando estos secretos en GitHub de todos modos? (s/n) [s]: " PROCEED_ANYWAY
    PROCEED_ANYWAY="${PROCEED_ANYWAY:-s}"
    if [[ ! "$PROCEED_ANYWAY" =~ ^[sSyY]$ ]]; then
      echo -e "${RED}Operación cancelada.${NC}"
      exit 1
    fi
  fi
fi

# Verificar GitHub CLI
echo -e "\n${YELLOW}Verificando estado de GitHub CLI (gh)...${NC}"
GH_READY=false
if command -v gh &>/dev/null; then
  if gh auth status &>/dev/null; then
    GH_READY=true
  else
    echo -e "${YELLOW}GitHub CLI está instalado pero no está autenticado.${NC}"
    read -r -p "¿Deseas autenticarte ahora con 'gh auth login'? (s/n) [s]: " LOGIN_NOW
    LOGIN_NOW="${LOGIN_NOW:-s}"
    if [[ "$LOGIN_NOW" =~ ^[sSyY]$ ]]; then
      gh auth login
      if gh auth status &>/dev/null; then
        GH_READY=true
      fi
    fi
  fi
fi

# Configuración de secretos
if [ "$GH_READY" = true ]; then
  echo -e "\n${BOLD}Configurando secretos en GitHub (${REPO})...${NC}"

  echo -n "  -> Configurando AWS_ACCESS_KEY_ID... "
  echo -n "$AWS_ACCESS_KEY_ID" | gh secret set AWS_ACCESS_KEY_ID -R "$REPO"
  echo -e "${GREEN}OK${NC}"

  echo -n "  -> Configurando AWS_SECRET_ACCESS_KEY... "
  echo -n "$AWS_SECRET_ACCESS_KEY" | gh secret set AWS_SECRET_ACCESS_KEY -R "$REPO"
  echo -e "${GREEN}OK${NC}"

  echo -n "  -> Configurando AWS_REGION... "
  echo -n "$AWS_REGION" | gh secret set AWS_REGION -R "$REPO"
  echo -e "${GREEN}OK${NC}"

  echo -e "\n${GREEN}${BOLD}¡Secretos configurados exitosamente en GitHub Actions!${NC}\n"

  # Opción para relanzar el pipeline
  read -r -p "¿Deseas re-ejecutar el pipeline de despliegue a AWS ('CD - Despliegue a AWS') ahora? (s/n) [s]: " RERUN
  RERUN="${RERUN:-s}"
  if [[ "$RERUN" =~ ^[sSyY]$ ]]; then
    echo -e "Buscando la última ejecución del workflow 'deploy.yml'..."
    LAST_RUN_ID=$(gh run list --workflow=deploy.yml -R "$REPO" --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || true)
    if [ -n "$LAST_RUN_ID" ] && [ "$LAST_RUN_ID" != "null" ]; then
      echo -e "Re-ejecutando run ID: ${CYAN}${LAST_RUN_ID}${NC}..."
      gh run rerun "$LAST_RUN_ID" -R "$REPO" --failed
      echo -e "${GREEN}✓ Despliegue reiniciado. Puedes monitorearlo con:${NC}"
      echo -e "  ${CYAN}gh run watch ${LAST_RUN_ID} -R ${REPO}${NC}"
    else
      echo -e "No se encontró ejecución previa fallida para re-ejecutar. Despachando nuevo workflow..."
      gh workflow run deploy.yml -R "$REPO" --ref main 2>/dev/null || echo -e "El workflow se ejecutará automáticamente ante el próximo push a 'main'."
    fi
  fi

else
  echo -e "\n${YELLOW}----------------------------------------------------------------------${NC}"
  echo -e "${BOLD}INSTRUCCIONES ALTERNATIVAS (GitHub CLI no disponible o sin sesión activa)${NC}"
  echo -e "${YELLOW}----------------------------------------------------------------------${NC}"
  echo -e "Puedes configurar los secretos ejecutando los siguientes comandos tras iniciar sesión con ${CYAN}gh auth login${NC}:"
  echo ""
  echo -e "  ${CYAN}echo -n \"$AWS_ACCESS_KEY_ID\" | gh secret set AWS_ACCESS_KEY_ID -R $REPO${NC}"
  echo -e "  ${CYAN}echo -n \"$AWS_SECRET_ACCESS_KEY\" | gh secret set AWS_SECRET_ACCESS_KEY -R $REPO${NC}"
  echo -e "  ${CYAN}echo -n \"$AWS_REGION\" | gh secret set AWS_REGION -R $REPO${NC}"
  echo ""
  echo -e "O manualmente desde la consola web de GitHub:"
  echo -e "  1. Navega a: ${CYAN}https://github.com/${REPO}/settings/secrets/actions${NC}"
  echo -e "  2. Haz clic en ${BOLD}'New repository secret'${NC} y registra:"
  echo -e "     - ${BOLD}AWS_ACCESS_KEY_ID${NC}:     $AWS_ACCESS_KEY_ID"
  echo -e "     - ${BOLD}AWS_SECRET_ACCESS_KEY${NC}: [tu secreto]"
  echo -e "     - ${BOLD}AWS_REGION${NC}:            $AWS_REGION"
  echo -e "  3. Una vez guardados, ve a ${CYAN}https://github.com/${REPO}/actions${NC}"
  echo -e "     y re-ejecuta el workflow ${BOLD}'CD - Despliegue a AWS'${NC} (Re-run failed jobs)."
  echo -e "${YELLOW}----------------------------------------------------------------------${NC}\n"
fi
