#!/usr/bin/env bash
# Wrapper: scaffold del proyecto (captura) usando el harness compartido _lib/playwright.
# Uso: ./setup.sh [DIR_DESTINO] [--no-deps]   (default DIR_DESTINO: arkan-e2e)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTSTRAP="$SCRIPT_DIR/../../../_lib/playwright/bootstrap.sh"
bash "$BOOTSTRAP" "$@"
