#!/bin/bash
# gcp-connect.sh — Conecta/activa un proyecto de GCP como configuración de gcloud
# Uso: gcp-connect.sh [--adc] <nombre-proyecto> [nombre2] ...
# Ejemplo: gcp-connect.sh archibol
#          gcp-connect.sh --adc ciencuadras
#
# Cada línea de negocio tiene su carpeta en proyectos/<nombre>/config.env con
# PROJECT_ID, ACCOUNT, REGION, ZONE, CONFIG_NAME y (opcional) KEY_FILE.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROYECTOS_DIR="$SKILL_DIR/proyectos"

# ── 0. Verificar gcloud ──────────────────────────────────────────────────────
if ! command -v gcloud >/dev/null 2>&1; then
  echo "Error: gcloud no está instalado."
  echo "Instala Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# ── Parseo de flags y posicionales ───────────────────────────────────────────
ADC=0
POS=()
for a in "$@"; do
  case "$a" in
    --adc) ADC=1 ;;
    --*)   echo "Flag desconocido: $a"; exit 1 ;;
    *)     POS+=("$a") ;;
  esac
done

if [ "${#POS[@]}" -eq 0 ]; then
  echo "Uso: gcp-connect.sh [--adc] <nombre-proyecto> [nombre2 ...]"
  echo ""
  echo "Proyectos configurados en proyectos/:"
  found=0
  for d in "$PROYECTOS_DIR"/*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    case "$name" in _*) continue ;; esac
    pid="$(grep -E '^PROJECT_ID=' "$d/config.env" 2>/dev/null | head -1 | cut -d= -f2-)"
    printf '  %-22s %s\n' "$name" "${pid:-(sin configurar → descubrimiento)}"
    found=1
  done
  [ "$found" -eq 0 ] && echo "  (ninguno; pasa un nombre nuevo y el script lo descubre)"
  exit 1
fi

TARGETS=("${POS[@]}")

# ── 1. Asegurar autenticación ────────────────────────────────────────────────
# Solo forzamos login de usuario si algún target NO usa service account (KEY_FILE).
ACTIVE_ACCOUNT=""

needs_user_login() {
  local name kf
  for name in "${TARGETS[@]}"; do
    kf="$(grep -E '^KEY_FILE=' "$PROYECTOS_DIR/$name/config.env" 2>/dev/null | head -1 | cut -d= -f2-)"
    if [ -z "$kf" ] || [ ! -f "$kf" ]; then
      return 0   # este target necesita cuenta de usuario
    fi
  done
  return 1
}

ensure_user_auth() {
  ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true)"

  if [ -z "$ACTIVE_ACCOUNT" ]; then
    echo "No hay cuenta de GCP autenticada. Abriendo login en el navegador..."
    echo "(en una máquina sin navegador usa: gcloud auth login --no-launch-browser)"
    gcloud auth login
    ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true)"
  fi

  # La política de sesión de la organización puede forzar reautenticación
  # aunque exista una cuenta "activa": si el token no refresca, re-logueamos.
  if ! gcloud auth print-access-token >/dev/null 2>&1; then
    echo "El token de '${ACTIVE_ACCOUNT:-tu cuenta}' expiró o requiere reautenticación. Abriendo login..."
    gcloud auth login
    ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true)"
  fi
}

if needs_user_login; then
  echo "Autenticando cuenta de GCP..."
  ensure_user_auth
  echo "✓ Cuenta activa: $ACTIVE_ACCOUNT"
fi

# ── 2. Conectar cada proyecto ────────────────────────────────────────────────
FIRST_CONFIG=""
FIRST_PROJECT_ID=""

for NAME in "${TARGETS[@]}"; do
  echo ""
  echo "── Proyecto: $NAME ──"

  CONFIG_FILE="$PROYECTOS_DIR/$NAME/config.env"
  PROJECT_ID=""
  ACCOUNT=""
  REGION=""
  ZONE=""
  CONFIG_NAME=""
  KEY_FILE=""

  if [ -f "$CONFIG_FILE" ]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"
  fi

  # Nombre de la configuración de gcloud: derivado del folder si no se fijó.
  CONFIG_NAME="$(echo "${CONFIG_NAME:-$NAME}" | tr '[:upper:]_' '[:lower:]-')"
  if ! echo "$CONFIG_NAME" | grep -Eq '^[a-z][a-z0-9-]*$'; then
    echo "Error: nombre de configuración inválido '$CONFIG_NAME'."
    echo "Debe empezar por letra y contener solo minúsculas, dígitos y guiones."
    echo "Ajusta CONFIG_NAME en $CONFIG_FILE."
    exit 1
  fi

  # ── 2a. Descubrimiento interactivo si falta PROJECT_ID ─────────────────────
  if [ -z "$PROJECT_ID" ]; then
    echo "Primera vez para '$NAME'. Descubriendo proyectos accesibles con ${ACTIVE_ACCOUNT:-la cuenta activa}..."

    PROJECTS_JSON="$(gcloud projects list --format=json)"
    COUNT="$(echo "$PROJECTS_JSON" | python3 -c 'import sys,json; print(len(json.load(sys.stdin)))')"

    if [ "$COUNT" -eq 0 ]; then
      echo "La cuenta activa no tiene proyectos accesibles. Verifica permisos o cambia de cuenta con: gcloud auth login"
      exit 1
    fi

    echo ""
    echo "$PROJECTS_JSON" | python3 -c "
import sys, json
projs = sorted(json.load(sys.stdin), key=lambda p: p['projectId'])
for i, p in enumerate(projs, 1):
    print(f'  [{i}] {p[\"projectId\"]:35s} {p.get(\"name\", \"\")}')
"
    read -rp "Selecciona el número de proyecto para '$NAME': " SEL

    if ! [[ "$SEL" =~ ^[0-9]+$ ]] || [ "$SEL" -lt 1 ] || [ "$SEL" -gt "$COUNT" ]; then
      echo "Selección inválida."
      exit 1
    fi

    PROJECT_ID="$(echo "$PROJECTS_JSON" | python3 -c "
import sys, json
projs = sorted(json.load(sys.stdin), key=lambda p: p['projectId'])
print(projs[$((SEL - 1))]['projectId'])
")"

    ACCOUNT="${ACCOUNT:-$ACTIVE_ACCOUNT}"

    mkdir -p "$PROYECTOS_DIR/$NAME"
    cat > "$CONFIG_FILE" <<EOF
PROJECT_ID=$PROJECT_ID
ACCOUNT=$ACCOUNT
CONFIG_NAME=$CONFIG_NAME
REGION=$REGION
ZONE=$ZONE
KEY_FILE=$KEY_FILE
EOF
    echo "Configuración guardada en $CONFIG_FILE"
  fi

  # ── 2b. Crear/activar la configuración de gcloud ───────────────────────────
  if ! gcloud config configurations describe "$CONFIG_NAME" >/dev/null 2>&1; then
    gcloud config configurations create "$CONFIG_NAME" --no-activate >/dev/null
    echo "Configuración de gcloud creada: $CONFIG_NAME"
  fi
  gcloud config configurations activate "$CONFIG_NAME" >/dev/null

  # ── 2c. Fijar cuenta (service account o usuario) ───────────────────────────
  if [ -n "$KEY_FILE" ] && [ -f "$KEY_FILE" ]; then
    gcloud auth activate-service-account --key-file="$KEY_FILE" >/dev/null
    SA_EMAIL="$(python3 -c "import json; print(json.load(open('$KEY_FILE'))['client_email'])" 2>/dev/null || true)"
    if [ -n "$SA_EMAIL" ]; then
      gcloud config set account "$SA_EMAIL" >/dev/null 2>&1 || true
      echo "Cuenta de servicio activada: $SA_EMAIL"
    fi
  elif [ -n "$ACCOUNT" ]; then
    gcloud config set account "$ACCOUNT" >/dev/null 2>&1 || true
  fi

  # ── 2d. Fijar proyecto, región y zona ──────────────────────────────────────
  gcloud config set project "$PROJECT_ID" >/dev/null
  [ -n "$REGION" ] && gcloud config set compute/region "$REGION" >/dev/null 2>&1 || true
  [ -n "$ZONE" ]   && gcloud config set compute/zone   "$ZONE"   >/dev/null 2>&1 || true

  # ── 2e. Verificar acceso ───────────────────────────────────────────────────
  CUR_ACCOUNT="$(gcloud config get-value account 2>/dev/null || true)"
  if gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
    echo "✓ Conectado a $PROJECT_ID  |  config: $CONFIG_NAME  |  cuenta: $CUR_ACCOUNT"
  else
    echo "⚠ Configuración '$CONFIG_NAME' lista (proyecto $PROJECT_ID), pero no se pudo verificar acceso."
    echo "  Puede faltar el permiso resourcemanager.projects.get o el proyecto no existe."
  fi

  if [ -z "$FIRST_CONFIG" ]; then
    FIRST_CONFIG="$CONFIG_NAME"
    FIRST_PROJECT_ID="$PROJECT_ID"
  fi
done

# ── 3. Dejar activo el primer proyecto solicitado ────────────────────────────
gcloud config configurations activate "$FIRST_CONFIG" >/dev/null

# ── 4. Application Default Credentials (opcional, para SDKs locales) ──────────
if [ "$ADC" -eq 1 ]; then
  echo ""
  echo "Configurando Application Default Credentials (ADC) para SDKs locales..."
  gcloud auth application-default login
  gcloud auth application-default set-quota-project "$FIRST_PROJECT_ID" >/dev/null 2>&1 || true
  echo "✓ ADC configurado con quota-project $FIRST_PROJECT_ID"
fi

echo ""
echo "Configuración activa: $FIRST_CONFIG (proyecto $FIRST_PROJECT_ID)"
echo "Listo."
