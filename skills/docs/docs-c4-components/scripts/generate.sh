#!/usr/bin/env bash
# Wrapper: invoca el motor compartido con flavor c4.
# Uso: ./generate.sh <modelo.json> [salida.drawio]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RENDER="$SCRIPT_DIR/../../../_lib/drawio/render.py"
python3 "$RENDER" c4 "$@"
