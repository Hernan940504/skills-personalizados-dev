# Contribuir al repo

Esta guía cubre el **CLI, los adaptadores y la infraestructura**. Para contribuir un
**skill** del catálogo, ver [`docs/CONTRIBUTING-SKILLS.md`](docs/CONTRIBUTING-SKILLS.md).

## Setup

```bash
git clone https://github.com/Hernan940504/skills-personalizados-dev.git
cd skills-personalizados-dev
# Sin dependencias de runtime: el CLI usa solo Node stdlib y python3 para validar.
node bin/skills-cli.js --help
```

## Antes de un PR

```bash
python3 scripts/validate.py     # lint de todos los SKILL.md (SKILL-FORMAT §5)
node --test tests/              # tests de CLI, adaptadores y parser
```

Ambos corren también en CI (`.github/workflows/validate-skills.yml`).

## Estructura

| Ruta | Qué es |
|---|---|
| `bin/skills-cli.js` | Entry point del CLI `skills-dev` |
| `src/commands/` | `add`, `remove`, `list`, `sync`, `new`, `validate` |
| `src/adapters/` | Aplica `adapters/<target>/adapter.yml` (reescribe frontmatter) |
| `src/resolvers/` | Resuelve nombre → ruta en `skills/**/` |
| `src/utils/` | Parser YAML/frontmatter y helpers de fs |
| `scripts/` | `install.sh`, `validate.{sh,py}`, `new-skill.sh` |
| `adapters/<target>/adapter.yml` | Reglas declarativas de transformación por herramienta |
| `skills/_lib/` | Código compartido entre skills (ver `docs/ARCHITECTURE.md §5.3b`) |

## Convenciones

- **Cero dependencias de runtime** en el CLI: si necesitas parsear YAML, usa `src/utils/yaml.js`.
- Las reglas de validación viven en `scripts/validate.py` (fuente de verdad); el CLI las reusa.
- Los adaptadores son **deterministas**: misma entrada → misma salida (hay tests de transformación).
- Commits: `feat(cli): ...`, `fix(adapter): ...`, `docs: ...`, `test: ...`, `chore: ...`.
- Trabaja en `dev`; PRs a `main`.

## Añadir un adaptador o target

1. Crea `adapters/<target>/adapter.yml` (mira `cursor` como referencia).
2. Si el target necesita lógica especial, extiéndela en `src/adapters/index.js`.
3. Añade un test en `tests/adapters.test.js`.
4. Documenta el mapping en `docs/COMPATIBILITY.md`.
