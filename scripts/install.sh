#!/usr/bin/env bash
# Instala skills en Claude Code (~/.claude/skills/<name>/).
#
# Uso:
#   ./scripts/install.sh <skill> [<skill>...] [--mode=link|copy] [--category=<cat>] [--all]
#   ./scripts/install.sh --all --mode=copy
#
# Modos:
#   link (default)  symlink al repo — editas y se refleja al instante.
#                   El motor compartido skills/_lib/ se resuelve vía el repo.
#   copy            copia independiente. Si el skill usa skills/_lib/, se
#                   vendoriza en <dest>/_lib y se reescribe el wrapper.
#
# Otros targets (cursor/kiro/opencode) los maneja el CLI: `skills-dev add <s> --target <t>`.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$REPO/skills"
DEST_ROOT="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

mode="link"
category=""
want_all=false
names=()

for arg in "$@"; do
  case "$arg" in
    --mode=*)     mode="${arg#*=}" ;;
    --category=*) category="${arg#*=}" ;;
    --all)        want_all=true ;;
    --*)          echo "Opción desconocida: $arg" >&2; exit 2 ;;
    *)            names+=("$arg") ;;
  esac
done

[[ "$mode" == "link" || "$mode" == "copy" ]] || { echo "mode inválido: $mode (link|copy)" >&2; exit 2; }

# Resuelve un nombre de skill → ruta de carpeta (busca en skills/*/<name>).
resolve_skill() {
  local n="$1" hit
  hit="$(find "$SKILLS_DIR" -mindepth 2 -maxdepth 2 -type d -name "$n" 2>/dev/null | head -1)"
  [[ -n "$hit" && -f "$hit/SKILL.md" ]] && { echo "$hit"; return 0; }
  return 1
}

# Lista de skills a instalar.
declare -a SRC_DIRS=()
if $want_all; then
  while IFS= read -r d; do SRC_DIRS+=("$d"); done \
    < <(find "$SKILLS_DIR" -mindepth 2 -maxdepth 2 -type d -not -name '_lib' \
          -exec test -f '{}/SKILL.md' ';' -print | sort)
elif [[ -n "$category" ]]; then
  while IFS= read -r d; do SRC_DIRS+=("$d"); done \
    < <(find "$SKILLS_DIR/$category" -mindepth 1 -maxdepth 1 -type d \
          -exec test -f '{}/SKILL.md' ';' -print 2>/dev/null | sort)
  [[ ${#SRC_DIRS[@]} -gt 0 ]] || { echo "Sin skills en categoría: $category" >&2; exit 1; }
else
  [[ ${#names[@]} -gt 0 ]] || { echo "Indica <skill>, --category=<cat> o --all." >&2; exit 2; }
  for n in "${names[@]}"; do
    if src="$(resolve_skill "$n")"; then SRC_DIRS+=("$src"); else
      echo "No encontrado: $n" >&2; exit 1
    fi
  done
fi

mkdir -p "$DEST_ROOT"

# ¿El skill depende del motor compartido _lib?
needs_lib() { grep -rqs "_lib/" "$1/SKILL.md" "$1/scripts" 2>/dev/null; }

install_lib_copy() {
  # Copia skills/_lib una sola vez al destino (vendorizado a nivel raíz).
  local dest="$DEST_ROOT/_lib"
  rm -rf "$dest"
  cp -R "$SKILLS_DIR/_lib" "$dest"
  find "$dest" -name '__pycache__' -type d -prune -exec rm -rf '{}' + 2>/dev/null || true
}

for src in "${SRC_DIRS[@]}"; do
  name="$(basename "$src")"
  dest="$DEST_ROOT/$name"
  rm -rf "$dest" 2>/dev/null || true

  if [[ "$mode" == "link" ]]; then
    ln -s "$src" "$dest"
    # En link, _lib se resuelve por el repo (el symlink apunta al árbol real).
    echo "↳ link  $name → $dest"
  else
    cp -R "$src" "$dest"
    find "$dest" -name '__pycache__' -type d -prune -exec rm -rf '{}' + 2>/dev/null || true
    if needs_lib "$src"; then
      install_lib_copy
      # Layout plano: <dest>/scripts está a 2 niveles de <DEST_ROOT>/_lib
      # (en repo eran 3). Reescribe el wrapper de la COPIA, no del fuente.
      if [[ -d "$dest/scripts" ]]; then
        find "$dest/scripts" -type f -name '*.sh' -exec \
          /usr/bin/sed -i '' 's#\.\./\.\./\.\./_lib/#../../_lib/#g' '{}' + 2>/dev/null || true
      fi
      echo "↳ copy  $name → $dest  (+ _lib vendorizado)"
    else
      echo "↳ copy  $name → $dest"
    fi
  fi
done

echo "✓ ${#SRC_DIRS[@]} skill(s) instalado(s) en $DEST_ROOT (modo: $mode)"
