#!/usr/bin/env bash
# Lintea los SKILL.md del catálogo según docs/SKILL-FORMAT.md §5.
# Uso: ./scripts/validate.sh [skills/cat/skill ...]   (sin args = todos)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/validate.py" "$@"
