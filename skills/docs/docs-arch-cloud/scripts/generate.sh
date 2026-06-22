#!/usr/bin/env bash
# Wrapper para docs-arch-cloud.
# Uso: ./generate.sh <provider> <modelo.json> [salida.drawio]
#   provider ∈ {aws, gcp, onprem}
set -euo pipefail
if [[ $# -lt 2 ]]; then
  echo "Uso: $0 <aws|gcp|onprem> <modelo.json> [salida.drawio]" >&2
  exit 1
fi
PROVIDER="$1"; shift
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RENDER="$SCRIPT_DIR/../../../_lib/drawio/render.py"
python3 "$RENDER" "$PROVIDER" "$@"
