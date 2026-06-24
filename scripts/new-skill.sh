#!/usr/bin/env bash
# Scaffold de un skill nuevo desde templates/skill-template/.
# Uso: ./scripts/new-skill.sh <name> --category <categoria> [--author <handle>]
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$REPO/templates/skill-template"
CATEGORIES="backend frontend devops testing security docs workspace files"

name="" category="" author="${USER:-tu-handle}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --category) category="$2"; shift 2 ;;
    --author)   author="$2";   shift 2 ;;
    -*)         echo "Opción desconocida: $1" >&2; exit 2 ;;
    *)          name="$1";      shift ;;
  esac
done

[[ -n "$name" ]]     || { echo "Falta <name>." >&2; exit 2; }
[[ -n "$category" ]] || { echo "Falta --category. Usa una de: $CATEGORIES" >&2; exit 2; }
[[ "$name" =~ ^[a-z][a-z0-9-]+$ ]] || { echo "name inválido (kebab-case): $name" >&2; exit 2; }
grep -qw "$category" <<<"$CATEGORIES" || { echo "category inválida: $category (usa: $CATEGORIES)" >&2; exit 2; }

dest="$REPO/skills/$category/$name"
[[ -e "$dest" ]] && { echo "Ya existe: skills/$category/$name" >&2; exit 1; }

cp -R "$TEMPLATE" "$dest"
# Sustituir placeholders triviales en SKILL.md y README.md.
for f in "$dest/SKILL.md" "$dest/README.md"; do
  /usr/bin/sed -i '' \
    -e "s/{{name}}/$name/g" \
    -e "s/{{category}}/$category/g" \
    -e "s/{{author}}/$author/g" "$f"
done

echo "✓ Creado skills/$category/$name"
echo "  Edita SKILL.md (description + workflow) y valida con: ./scripts/validate.sh skills/$category/$name"
