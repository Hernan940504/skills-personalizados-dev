#!/usr/bin/env bash
# =====================================================================
# explore-module.sh — Graba interacciones de un módulo YA AUTENTICADO con
# Playwright Codegen, generando código `playwright-test` como punto de partida.
#
# Uso:
#   ./explore-module.sh <DIR_PROYECTO> [RUTA_MODULO] [ARCHIVO_SALIDA]
#     DIR_PROYECTO    Carpeta del proyecto E2E (la creada por setup.sh)
#     RUTA_MODULO     Path relativo del módulo (default: /)
#     ARCHIVO_SALIDA  Dónde volcar el código grabado (default: stdout/editor)
#
# Requiere una sesión guardada (playwright/.auth/user.json). Si no existe, la
# crea corriendo el proyecto `setup`.
# =====================================================================
set -euo pipefail

PROJECT_DIR="${1:?Uso: explore-module.sh <DIR_PROYECTO> [RUTA_MODULO] [ARCHIVO_SALIDA]}"
MODULE_PATH="${2:-/}"
OUTPUT="${3:-}"

cd "$PROJECT_DIR"

# Cargar baseURL desde .env (sin exponer el resto del entorno).
BASE_URL="$(grep -E '^ARKAN_BASE_URL=' .env | head -1 | cut -d= -f2-)"
BASE_URL="${BASE_URL%/}"

AUTH="playwright/.auth/user.json"
if [ ! -f "$AUTH" ]; then
  echo "==> No hay sesión guardada; ejecutando login (proyecto setup)..."
  npx playwright test --project=setup
fi

URL="${BASE_URL}${MODULE_PATH}"
echo "==> Abriendo Codegen autenticado en: $URL"

ARGS=(codegen --load-storage="$AUTH" --target=playwright-test)
[ -n "$OUTPUT" ] && ARGS+=(--output "$OUTPUT")
ARGS+=("$URL")

npx playwright "${ARGS[@]}"
