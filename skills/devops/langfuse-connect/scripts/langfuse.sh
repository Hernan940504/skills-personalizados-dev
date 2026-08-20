#!/bin/bash
# langfuse.sh — Carga la config de un proyecto y ejecuta consultas contra la API de Langfuse.
# Uso:  bash scripts/langfuse.sh <proyecto> <comando> [opciones]
# Ej.:  bash scripts/langfuse.sh mia-ciencuadras validate --days 30
#       bash scripts/langfuse.sh mia-ciencuadras models --days 90 --grep gemini
#
# Precedencia de credenciales: las variables ya presentes en el entorno (p.ej. exportadas
# en ~/.zshrc) GANAN. Solo se completan desde proyectos/<x>/config.env y secret.env los
# valores que falten. Así puedes configurar por .zshrc, por archivos, o mezclar ambos.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJ_DIR="$SKILL_DIR/proyectos"

PROJECT="${1:-mia-ciencuadras}"
shift || true

CONFIG="$PROJ_DIR/$PROJECT/config.env"
SECRET="$PROJ_DIR/$PROJECT/secret.env"

# Completar SOLO lo que falte, sin pisar el entorno ya exportado.
if [ -z "${LANGFUSE_HOST:-}" ] || [ -z "${LANGFUSE_PUBLIC_KEY:-}" ]; then
  if [ -f "$CONFIG" ]; then
    set -a; # shellcheck disable=SC1090
    source "$CONFIG"; set +a
  fi
fi
if [ -z "${LANGFUSE_SECRET_KEY:-}" ] && [ -f "$SECRET" ]; then
  set -a; # shellcheck disable=SC1090
  source "$SECRET"; set +a
fi

# Validar que tengamos lo mínimo (por entorno o por archivos).
MISS=()
[ -z "${LANGFUSE_HOST:-}" ]       && MISS+=("LANGFUSE_HOST")
[ -z "${LANGFUSE_PUBLIC_KEY:-}" ] && MISS+=("LANGFUSE_PUBLIC_KEY")
[ -z "${LANGFUSE_SECRET_KEY:-}" ] && MISS+=("LANGFUSE_SECRET_KEY")
if [ "${#MISS[@]}" -gt 0 ]; then
  echo "⚠️  Faltan credenciales: ${MISS[*]}"
  echo "   Opción A (recomendada aquí): expórtalas en ~/.zshrc y 'source ~/.zshrc'."
  echo "   Opción B: ponlas en $CONFIG (host+public) y $SECRET (secret, gitignored)."
  exit 1
fi

exec python3 "$SCRIPT_DIR/langfuse_query.py" "$@"
