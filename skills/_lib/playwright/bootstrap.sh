#!/usr/bin/env bash
# =====================================================================
# bootstrap.sh — Scaffold idempotente de un proyecto Playwright E2E.
#
# Copia el harness compartido (template/) a un directorio destino, crea el
# `.env` con credenciales (desde el `.env` real del harness si existe, o desde
# `.env.example`), instala dependencias y descarga el navegador Chromium.
#
# Uso:
#   bootstrap.sh [DIR_DESTINO] [--no-deps]
#     DIR_DESTINO   Carpeta del proyecto E2E (default: arkan-e2e)
#     --no-deps     No ejecuta `npm install` ni `npx playwright install`
#
# Idempotente: nunca sobrescribe archivos existentes (cp -n). Re-ejecutar es seguro.
# =====================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/template"
HARNESS_ENV="$SCRIPT_DIR/.env"

TARGET_DIR="arkan-e2e"
INSTALL_DEPS=1
for arg in "$@"; do
  case "$arg" in
    --no-deps) INSTALL_DEPS=0 ;;
    -*)        echo "Opción desconocida: $arg" >&2; exit 2 ;;
    *)         TARGET_DIR="$arg" ;;
  esac
done

echo "==> Scaffolding harness Playwright en: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

# Copiar el árbol del template SIN sobrescribir lo que ya exista (incluye dotfiles).
cp -Rn "$TEMPLATE_DIR"/. "$TARGET_DIR"/ 2>/dev/null || cp -Rn "$TEMPLATE_DIR"/. "$TARGET_DIR"/ || true

# Garantizar el .env del proyecto (credenciales). Prioridad:
#   1. Ya existe en destino -> respetar.
#   2. Existe el .env real del harness -> copiarlo (uso inmediato).
#   3. Caer en .env.example -> el usuario lo rellena.
if [ -f "$TARGET_DIR/.env" ]; then
  echo "==> .env ya existe en el destino (se respeta)."
elif [ -f "$HARNESS_ENV" ]; then
  cp "$HARNESS_ENV" "$TARGET_DIR/.env"
  echo "==> .env copiado desde el harness (credenciales listas)."
else
  cp "$TARGET_DIR/.env.example" "$TARGET_DIR/.env"
  echo "==> .env creado desde .env.example — RELLENA las credenciales antes de correr."
fi

if [ "$INSTALL_DEPS" -eq 1 ]; then
  echo "==> Instalando dependencias (npm install)..."
  ( cd "$TARGET_DIR" && npm install )
  echo "==> Descargando navegador Chromium (npx playwright install)..."
  ( cd "$TARGET_DIR" && npx playwright install chromium )
else
  echo "==> --no-deps: omito npm install / playwright install."
fi

cat <<EOF

==> Listo. Proyecto E2E en '$TARGET_DIR'.
    Siguientes pasos:
      cd $TARGET_DIR
      npm run auth      # login una vez -> guarda la sesión
      npm test          # corre la suite E2E
      npm run report    # abre el reporte HTML
      npm run manual    # captura las pantallas del manual
EOF
