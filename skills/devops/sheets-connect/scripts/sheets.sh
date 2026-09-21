#!/bin/bash
# sheets.sh — Lee/escribe Google Sheets vía service account (skill sheets-connect).
#
# Uso:
#   sheets.sh <proyecto> info   <id-o-url>
#   sheets.sh <proyecto> read   <id-o-url> [--tab NOMBRE | --range A1] [--format json|csv]
#   sheets.sh <proyecto> write  <id-o-url> --range A1 --values-json '[["a","b"]]'
#   sheets.sh <proyecto> append <id-o-url> (--tab NOMBRE | --range A1) --values-json '[["a"]]'
#
# Cada proyecto tiene su carpeta en proyectos/<proyecto>/config.env con:
#   SA_EMAIL, AUTH_MODE (key|impersonate), KEY_FILE (si AUTH_MODE=key), PROJECT_ID.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROYECTOS_DIR="$SKILL_DIR/proyectos"

# venv del skill (con las librerías cliente de Google).
VENV_PY="${SHEETS_CONNECT_VENV:-$HOME/.config/gcloud/sheets-connect-venv}/bin/python"

usage() {
  echo "Uso: sheets.sh <proyecto> <info|read|write|append> <id-o-url> [opciones]"
  echo ""
  echo "Proyectos configurados en proyectos/:"
  local found=0
  for d in "$PROYECTOS_DIR"/*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    case "$name" in _*) continue ;; esac
    echo "  $name"
    found=1
  done
  [ "$found" -eq 0 ] && echo "  (ninguno; copia proyectos/_ejemplo a proyectos/<nombre>)"
  exit 1
}

[ "$#" -lt 3 ] && usage

PROJECT_NAME="$1"; shift
COMMAND="$1"; shift
TARGET="$1"; shift

CONFIG_FILE="$PROYECTOS_DIR/$PROJECT_NAME/config.env"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: no existe $CONFIG_FILE"
  echo "Copia proyectos/_ejemplo/config.env a proyectos/$PROJECT_NAME/config.env y complétalo."
  exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG_FILE"

AUTH_MODE="${AUTH_MODE:-key}"
SA_EMAIL="${SA_EMAIL:-}"
KEY_FILE="${KEY_FILE:-}"
OAUTH_CLIENT_FILE="${OAUTH_CLIENT_FILE:-}"
OAUTH_TOKEN_FILE="${OAUTH_TOKEN_FILE:-$HOME/.config/gcloud/sheets-connect-user-token.json}"

if [ ! -x "$VENV_PY" ]; then
  echo "Error: no se encontró el intérprete del venv en $VENV_PY"
  echo "Créalo con: python3 -m venv ~/.config/gcloud/sheets-connect-venv"
  echo "  y luego: ~/.config/gcloud/sheets-connect-venv/bin/pip install -r $SKILL_DIR/requirements.txt"
  exit 1
fi

if [ "$AUTH_MODE" = "key" ] && { [ -z "$KEY_FILE" ] || [ ! -f "$KEY_FILE" ]; }; then
  echo "Error: AUTH_MODE=key pero KEY_FILE no existe: '${KEY_FILE:-<vacío>}'"
  exit 1
fi

if [ "$AUTH_MODE" = "user-oauth" ] && { [ -z "$OAUTH_CLIENT_FILE" ] || [ ! -f "$OAUTH_CLIENT_FILE" ]; }; then
  echo "Error: AUTH_MODE=user-oauth pero OAUTH_CLIENT_FILE no existe: '${OAUTH_CLIENT_FILE:-<vacío>}'"
  echo "Descarga el client secret JSON (OAuth Desktop) y pon su ruta en OAUTH_CLIENT_FILE."
  exit 1
fi

exec "$VENV_PY" "$SCRIPT_DIR/sheets_io.py" \
  "$COMMAND" "$TARGET" \
  --auth-mode "$AUTH_MODE" \
  --sa-email "$SA_EMAIL" \
  --key-file "$KEY_FILE" \
  --oauth-client-file "$OAUTH_CLIENT_FILE" \
  --oauth-token-file "$OAUTH_TOKEN_FILE" \
  "$@"
