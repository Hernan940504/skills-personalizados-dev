#!/usr/bin/env bash
# Valida un archivo OpenAPI 3.0 (YAML o JSON).
# Uso: ./validate-openapi.sh [ruta-al-spec]
# Default: busca openapi.yaml, openapi.json, swagger.yaml en el directorio actual.

set -euo pipefail

SPEC_FILE="${1:-}"

# Busca el spec si no se especificó
if [ -z "$SPEC_FILE" ]; then
  for candidate in openapi.yaml openapi.json swagger.yaml swagger.json api/openapi.yaml docs/openapi.yaml; do
    if [ -f "$candidate" ]; then
      SPEC_FILE="$candidate"
      break
    fi
  done
fi

if [ -z "$SPEC_FILE" ] || [ ! -f "$SPEC_FILE" ]; then
  echo "[docs-openapi] ERROR: No se encontró spec OpenAPI. Pasa la ruta como argumento." >&2
  echo "  Uso: ./validate-openapi.sh ruta/al/openapi.yaml" >&2
  exit 1
fi

echo "[docs-openapi] Validando: $SPEC_FILE"

# Intenta con @redocly/cli (preferido)
if command -v redocly &>/dev/null; then
  redocly lint "$SPEC_FILE"
  echo "[docs-openapi] ✓ Validado con Redocly CLI"
  exit 0
fi

# Intenta con npx @redocly/cli
if command -v npx &>/dev/null; then
  echo "[docs-openapi] Ejecutando npx @redocly/cli lint (puede tardar la primera vez)..."
  npx --yes @redocly/cli lint "$SPEC_FILE"
  echo "[docs-openapi] ✓ Validado con @redocly/cli"
  exit 0
fi

# Fallback: python-jsonschema si está disponible y el spec es JSON
if command -v python3 &>/dev/null && [[ "$SPEC_FILE" == *.json ]]; then
  python3 -c "
import json, sys
with open('$SPEC_FILE') as f:
    spec = json.load(f)
required = {'openapi', 'info', 'paths'}
missing = required - spec.keys()
if missing:
    print(f'ERROR: Faltan campos obligatorios: {missing}')
    sys.exit(1)
print('JSON válido. Campos OpenAPI básicos presentes.')
print('Para validación completa instalar: npm install -g @redocly/cli')
"
  exit 0
fi

echo "[docs-openapi] AVISO: No se encontró ningún validador (redocly, npx)."
echo "  Para instalar: npm install -g @redocly/cli"
echo "  Validación básica: el archivo existe y tiene nombre correcto."
exit 0
