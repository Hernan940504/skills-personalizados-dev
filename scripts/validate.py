#!/usr/bin/env python3
"""Valida los SKILL.md del catálogo según docs/SKILL-FORMAT.md §5.

Sin dependencias externas (parser de frontmatter mínimo, no usa PyYAML).
Uso:
    python3 scripts/validate.py [skills/cat/skill ... | --all]

Salida: lista de errores/warnings por skill. Exit 1 si hay algún ERROR.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / "skills"

CATEGORIES = {"backend", "frontend", "devops", "testing", "security",
              "docs", "workspace", "files"}
COMPAT = {"claude-code", "cursor", "kiro", "opencode"}
# Conjunto permisivo de tools de Claude Code (solo warning si algo no encaja).
KNOWN_TOOLS = {"Read", "Write", "Edit", "Bash", "Grep", "Glob", "WebFetch",
               "WebSearch", "Task", "NotebookEdit", "TodoWrite"}

NAME_RE = re.compile(r"^[a-z][a-z0-9-]+$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+([-+].+)?$")
# Verbos comunes (heurística laxa para warning de description).
VERB_HINT = re.compile(r"^(crea|genera|refactoriza|analiza|eval[uú]a|documenta|"
                       r"revisa|audita|configura|construye|valida|detecta|"
                       r"refresca|produce|escribe|implementa)", re.IGNORECASE)


class Frontmatter:
    """Parser tolerante: key: scalar | [inline list] | bloque '- item' |
    valor plegado multilínea (continuaciones indentadas)."""

    def __init__(self, raw: str):
        self.fields: dict[str, object] = {}
        self.ok = True
        self.error = ""
        self._parse(raw)

    def _parse(self, raw: str) -> None:
        lines = raw.splitlines()
        i = 0
        key = None
        buf: list[str] = []
        block_list: list[str] | None = None

        def flush():
            nonlocal key, buf, block_list
            if key is None:
                return
            if block_list is not None:
                self.fields[key] = block_list
            else:
                val = " ".join(s.strip() for s in buf).strip()
                self.fields[key] = self._coerce(val)
            key, buf, block_list = None, [], None

        while i < len(lines):
            line = lines[i]
            i += 1
            if not line.strip():
                continue
            m = re.match(r"^([a-zA-Z][\w-]*):\s?(.*)$", line)
            if m and not line.startswith(" "):
                flush()
                key = m.group(1)
                rest = m.group(2)
                if rest == "":
                    buf = []  # puede iniciar bloque o valor plegado
                else:
                    buf = [rest]
            elif re.match(r"^\s*-\s+", line):
                if block_list is None:
                    block_list = []
                    buf = []
                block_list.append(re.sub(r"^\s*-\s+", "", line).strip())
            else:
                buf.append(line)  # continuación de valor plegado
        flush()

    @staticmethod
    def _coerce(val: str):
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                return []
            return [x.strip() for x in inner.split(",")]
        return val.strip('"').strip("'")


def extract_frontmatter(text: str):
    if not text.startswith("---"):
        return None, "no empieza con frontmatter '---'"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "frontmatter sin cierre '---'"
    return parts[1], None


def find_referenced_paths(body: str):
    """Rutas en backticks que apuntan a recursos del skill o a _lib."""
    out = set()
    for m in re.finditer(r"`([^`]+)`", body):
        token = m.group(1).split()[0] if m.group(1).split() else ""
        if re.match(r"^(scripts|templates|references)/[\w./-]+$", token):
            out.add(token)
        elif "_lib/" in token and token.endswith(".py"):
            out.add(token)
    return out


def validate_skill(skill_dir: Path):
    errors, warnings = [], []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"falta SKILL.md en {skill_dir}"], []

    text = skill_md.read_text(encoding="utf-8")
    fm_raw, err = extract_frontmatter(text)
    if err:
        return [err], []
    body = text.split("---", 2)[2]
    fm = Frontmatter(fm_raw).fields

    # name
    name = fm.get("name", "")
    if not name:
        errors.append("falta 'name'")
    else:
        if not isinstance(name, str) or not NAME_RE.match(name):
            errors.append(f"'name' inválido (kebab-case): {name!r}")
        if len(str(name)) > 50:
            errors.append("'name' > 50 chars")
        if name != skill_dir.name:
            errors.append(f"'name' ({name}) != carpeta ({skill_dir.name})")

    # description
    desc = fm.get("description", "")
    if not desc:
        errors.append("falta 'description'")
    else:
        if len(str(desc)) > 500:
            errors.append(f"'description' > 500 chars ({len(str(desc))})")
        if not VERB_HINT.match(str(desc).strip()):
            warnings.append("'description' no empieza con verbo (heurística)")

    # version
    ver = fm.get("version", "")
    if not ver:
        errors.append("falta 'version'")
    elif not SEMVER_RE.match(str(ver)):
        errors.append(f"'version' no es semver: {ver!r}")

    # category
    cat = fm.get("category", "")
    if not cat:
        errors.append("falta 'category'")
    elif cat not in CATEGORIES:
        errors.append(f"'category' fuera del enum: {cat!r}")

    # tags
    if "tags" in fm and not isinstance(fm["tags"], list):
        errors.append("'tags' debe ser lista")

    # compatibility
    if "compatibility" in fm:
        comp = fm["compatibility"]
        if not isinstance(comp, list):
            errors.append("'compatibility' debe ser lista")
        else:
            bad = [c for c in comp if c not in COMPAT]
            if bad:
                errors.append(f"'compatibility' valores inválidos: {bad}")

    # allowed-tools (warning)
    if "allowed-tools" in fm and isinstance(fm["allowed-tools"], list):
        bad = [t for t in fm["allowed-tools"] if t not in KNOWN_TOOLS]
        if bad:
            warnings.append(f"'allowed-tools' no reconocidas: {bad}")

    # body: sección Cuándo usar (warning)
    if "## Cuándo usar" not in body:
        warnings.append("falta sección '## Cuándo usar' en el body")

    # archivos referenciados existen (warning)
    for ref in sorted(find_referenced_paths(body)):
        if ref.startswith("skills/"):
            target = REPO / ref                      # ruta desde raíz del repo
        elif "_lib/" in ref:
            target = (skill_dir / ref).resolve()     # ej. ../../_lib/drawio/render.py
        else:
            target = skill_dir / ref                 # scripts/ templates/ references/
        if not target.exists():
            warnings.append(f"recurso referenciado no existe: {ref}")

    return errors, warnings


def discover_skills():
    out = []
    for skill_md in sorted(SKILLS_DIR.glob("*/*/SKILL.md")):
        out.append(skill_md.parent)
    return out


def main(argv):
    args = [a for a in argv[1:] if a != "--all"]
    targets = [Path(a).resolve() for a in args] if args else discover_skills()

    total_err = 0
    total_warn = 0
    for sd in targets:
        errors, warnings = validate_skill(sd)
        rel = sd.relative_to(REPO) if REPO in sd.parents else sd
        if not errors and not warnings:
            print(f"✓ {rel}")
        else:
            mark = "✗" if errors else "⚠"
            print(f"{mark} {rel}")
            for e in errors:
                print(f"    ERROR   {e}")
            for w in warnings:
                print(f"    warning {w}")
        total_err += len(errors)
        total_warn += len(warnings)

    print(f"\n{len(targets)} skills · {total_err} errores · {total_warn} warnings")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
