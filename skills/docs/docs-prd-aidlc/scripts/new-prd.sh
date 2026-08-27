#!/usr/bin/env bash
# Scaffold de un PRD (insumo AI-DLC) a partir de la plantilla del skill.
# Uso: ./new-prd.sh "<nombre-producto>" "<linea-negocio>" [propio|interno]
#   - nombre-producto: se normaliza a kebab-case para el nombre de archivo.
#   - linea-negocio:   carpeta destino bajo lineas_negocio/.
#   - tipo:            propio | interno (default: interno).
# Crea: lineas_negocio/<linea-negocio>/prd-<nombre-producto>.md
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Uso: $0 \"<nombre-producto>\" \"<linea-negocio>\" [propio|interno]" >&2
  exit 1
fi

RAW_NAME="$1"
LINEA="$2"
TIPO="${3:-interno}"

if [[ "$TIPO" != "propio" && "$TIPO" != "interno" ]]; then
  echo "Error: tipo debe ser 'propio' o 'interno' (recibido: '$TIPO')." >&2
  exit 1
fi

# Normaliza a kebab-case: minúsculas, espacios/guiones bajos -> guion, quita el resto.
slug() {
  echo "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | tr ' _' '--' \
    | sed -E 's/[^a-z0-9-]//g; s/-+/-/g; s/^-//; s/-$//'
}

NAME_SLUG="$(slug "$RAW_NAME")"
LINEA_SLUG="$(slug "$LINEA")"

if [[ -z "$NAME_SLUG" || -z "$LINEA_SLUG" ]]; then
  echo "Error: nombre-producto y linea-negocio no pueden quedar vacíos tras normalizar." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
TEMPLATE="$SCRIPT_DIR/../templates/prd-aidlc.md"
OUT_DIR="$REPO_ROOT/lineas_negocio/$LINEA_SLUG"
OUT_FILE="$OUT_DIR/prd-$NAME_SLUG.md"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "Error: no se encontró la plantilla en $TEMPLATE" >&2
  exit 1
fi

if [[ -e "$OUT_FILE" ]]; then
  echo "Error: ya existe $OUT_FILE — no se sobrescribe." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

FECHA="$(date +%F)"

# Sustituye placeholders de cabecera; deja los {{TODO}} para llenado manual.
sed \
  -e "s/{{NOMBRE_PRODUCTO}}/$NAME_SLUG/g" \
  -e "s/{{LINEA_NEGOCIO}}/$LINEA_SLUG/g" \
  -e "s/{{TIPO}}/$TIPO/g" \
  -e "s/{{FECHA}}/$FECHA/g" \
  "$TEMPLATE" > "$OUT_FILE"

echo "PRD creado: $OUT_FILE"
echo "Siguiente paso: completar las 9 secciones + el bloque AI-DLC (§10)."
