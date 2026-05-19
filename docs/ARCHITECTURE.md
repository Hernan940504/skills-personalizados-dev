# Arquitectura

Este documento describe la **topología del monorepo**, el **flujo de instalación** y las **decisiones de diseño** detrás de `skills-personalizados-dev`.

---

## 1. Objetivos de diseño

| # | Objetivo | Implicación de diseño |
|---|---|---|
| 1 | Una sola fuente de verdad para cada skill | `SKILL.md` canónico + adaptadores por herramienta |
| 2 | Instalación trivial (`npx ... add <skill>`) | CLI publicado en npm con resolución por nombre |
| 3 | Desarrollo activo sin reinstalar tras cada edit | Modo `--mode=link` con symlinks |
| 4 | Compatibilidad con Claude Code, Cursor, Kiro, OpenCode | Adaptadores que reescriben frontmatter, no body |
| 5 | Crecimiento sostenible sin acoplar skills entre sí | Cada skill es autocontenido (sin imports cruzados) |
| 6 | CI valida calidad antes de mergear | Workflow `validate-skills.yml` lintea todo PR |

---

## 2. Topología completa del repo

```
skills-personalizados-dev/
│
├── README.md                       # Visión + catálogo + quickstart
├── LICENSE                         # MIT
├── CONTRIBUTING.md                 # Cómo contribuir al repo (no a un skill)
├── package.json                    # Metadata npm + scripts CLI
│
├── bin/
│   └── skills-cli.js               # Entry point ejecutable de @hbetancur/skills-dev
│
├── src/                            # Implementación del CLI
│   ├── commands/                   # add, remove, list, sync, new, validate
│   ├── adapters/                   # Lógica de transformación por target
│   ├── resolvers/                  # Resuelve nombre → ruta en skills/
│   └── utils/
│
├── skills/                         # ★ CATÁLOGO — fuente de verdad
│   ├── backend/
│   │   ├── backend-java/
│   │   ├── backend-node/
│   │   ├── backend-python/
│   │   └── backend-go/
│   ├── frontend/
│   │   ├── frontend-react/
│   │   ├── frontend-vue/
│   │   └── frontend-angular/
│   ├── devops/
│   │   ├── devops-docker/
│   │   ├── devops-kubernetes/
│   │   ├── devops-terraform/
│   │   └── devops-cicd-gha/
│   ├── testing/
│   │   ├── testing-generation/
│   │   └── testing-coverage/
│   ├── security/
│   │   ├── security-owasp/
│   │   └── security-deps-audit/
│   ├── docs/
│   │   ├── docs-adr/
│   │   └── docs-readme/
│   ├── workspace/
│   │   ├── workspace-git-flow/
│   │   └── workspace-monorepo/
│   └── files/
│       ├── files-pdf/
│       └── files-csv/
│
├── adapters/                       # ★ Definiciones declarativas (no código)
│   ├── claude-code/
│   │   └── adapter.yml             # mapping de frontmatter → SKILL.md nativo
│   ├── cursor/
│   │   └── adapter.yml             # → .cursor/rules/*.mdc
│   ├── kiro/
│   │   └── adapter.yml             # → .kiro/steering/*.md
│   └── opencode/
│       └── adapter.yml
│
├── templates/
│   └── skill-template/             # Copiado por `skills new`
│       ├── SKILL.md
│       ├── README.md
│       ├── scripts/.gitkeep
│       ├── templates/.gitkeep
│       └── references/.gitkeep
│
├── scripts/
│   ├── install.sh                  # Symlinks rápidos a ~/.claude/skills/
│   ├── new-skill.sh                # Atajo bash de `skills new`
│   └── validate.sh                 # Atajo bash de `skills validate`
│
├── docs/                           # Documentación del proyecto
│   ├── ARCHITECTURE.md             # (este archivo)
│   ├── SKILL-FORMAT.md
│   ├── COMPATIBILITY.md
│   └── CONTRIBUTING-SKILLS.md
│
├── tests/
│   ├── skill-validation.test.js    # Valida SKILL.md de cada skill
│   ├── cli.test.js                 # Tests del CLI
│   └── adapters.test.js            # Tests de transformación
│
└── .github/
    ├── workflows/
    │   ├── validate-skills.yml     # CI por PR
    │   └── release.yml             # Publica a npm en tag vX.Y.Z
    ├── ISSUE_TEMPLATE/
    │   ├── new-skill-request.md
    │   └── bug.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 3. Estructura interna de un skill

Cada skill es una carpeta autocontenida bajo `skills/<categoria>/<skill>/`:

```
skills/backend/backend-java/
├── SKILL.md                # Manifest + instrucciones (lo que el agente lee)
├── README.md               # Documentación humana
├── scripts/                # Scripts ejecutables (bash, python) opcionales
│   ├── generate-controller.sh
│   └── add-test.sh
├── templates/              # Plantillas de código copiables
│   ├── controller.java.tmpl
│   ├── service.java.tmpl
│   └── test-junit5.java.tmpl
└── references/             # Material que el agente lee bajo demanda
    ├── spring-conventions.md
    ├── junit5-patterns.md
    └── sonarqube-rules.md
```

| Carpeta | Cuándo usarla |
|---|---|
| `scripts/` | Acciones determinísticas que el agente puede ejecutar (`bash`, `node`, `python`). Reducen tokens y errores. |
| `templates/` | Bloques de código que el skill copia o adapta. Marcadores `{{placeholder}}` |
| `references/` | Documentación detallada (convenciones, patrones, ejemplos largos) que el agente consulta solo si la necesita. Evita inflar el contexto. |

---

## 4. Flujo de instalación

```
┌────────────────────────────────────────────────────────────────┐
│  npx @hbetancur/skills-dev add backend-java --target cursor    │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌──────────────────────────────┐
              │  src/resolvers/findSkill.js  │  busca en skills/**/ por name
              └──────────────────────────────┘
                              │
                              ▼
              ┌──────────────────────────────┐
              │   carga skills/backend/      │
              │       backend-java/          │
              │         SKILL.md             │
              └──────────────────────────────┘
                              │
                              ▼
              ┌──────────────────────────────┐
              │  adapters/cursor/adapter.yml │  reglas de transformación
              └──────────────────────────────┘
                              │
                              ▼
              ┌──────────────────────────────┐
              │  src/adapters/cursor.js      │  reescribe frontmatter
              │  (mantiene body intacto)     │
              └──────────────────────────────┘
                              │
                              ▼
              ┌──────────────────────────────┐
              │  ~/.cursor/rules/            │  symlink o copia
              │     backend-java.mdc         │  según --mode
              └──────────────────────────────┘
```

Para `--mode=link` el adaptador escribe el archivo transformado a una caché local (`.skills-build/`) y luego hace symlink. Las ediciones posteriores requieren `skills-dev sync` (o un watcher opcional).

---

## 5. Decisiones de diseño explicadas

### 5.1 ¿Por qué un solo formato canónico (`SKILL.md`)?

Mantener un único formato evita drift entre versiones de un skill por herramienta. Los adaptadores son **idempotentes** y **deterministas**: misma entrada → misma salida.

### 5.2 ¿Por qué carpetas por categoría en vez de tags?

La navegación humana en GitHub es el caso de uso principal. Las categorías son rápidas de explorar; los tags pueden añadirse como metadata en el frontmatter para búsquedas semánticas.

### 5.3 ¿Por qué `scripts/`, `templates/`, `references/` separados?

Mismo patrón que usa Anthropic en su repo oficial: optimiza el uso de contexto del agente. El `SKILL.md` queda corto y enfocado; el material pesado se carga **bajo demanda**.

### 5.4 ¿Por qué un CLI propio en vez de solo `git clone`?

Tres razones:

1. Permite **resolución por nombre** (`add backend-java` sin saber la ruta).
2. Habilita **targeting multi-herramienta** transparente.
3. Permite **versionado** futuro (instalar `backend-java@1.2.0`).

### 5.5 ¿Por qué symlinks por default en dev local?

El usuario es el autor; quiere iterar rápido sobre skills sin reinstalar. Symlinks reflejan cambios al instante. Para usuarios finales el default cambia a `--mode=copy` por seguridad (no romper si mueven el repo).

---

## 6. Naming y convenciones

| Elemento | Convención | Ejemplo |
|---|---|---|
| Nombre de skill | `categoria-stack[-enfoque]`, kebab-case | `backend-java`, `frontend-react-testing` |
| Carpeta | igual al nombre | `skills/backend/backend-java/` |
| Branch para nuevo skill | `skill/<name>` | `skill/backend-java` |
| Commit que añade skill | `feat(skill): add <name>` | `feat(skill): add backend-java` |
| Tag de release | `vMAJOR.MINOR.PATCH` | `v0.3.0` |

---

## 7. Roadmap arquitectónico

| Fase | Entregable | Estado |
|---|---|---|
| 0 — Diseño documental | README + 4 docs core | ✅ esta sesión |
| 1 — Bootstrap estructural | Carpetas `skills/`, `adapters/`, `templates/`, `scripts/install.sh` | ⏳ |
| 2 — Golden path | `backend-java` completo como referencia | ⏳ |
| 3 — CLI v0 | `add`, `list`, `sync` para target `claude-code` | ⏳ |
| 4 — Adaptadores | `cursor`, `kiro`, `opencode` | ⏳ |
| 5 — Catálogo MVP | 8 skills MVP completos | ⏳ |
| 6 — Publicación npm | `@hbetancur/skills-dev` v0.1.0 | ⏳ |

---

Ver también:
- [`SKILL-FORMAT.md`](SKILL-FORMAT.md) — especificación del manifest
- [`COMPATIBILITY.md`](COMPATIBILITY.md) — detalles por herramienta
- [`CONTRIBUTING-SKILLS.md`](CONTRIBUTING-SKILLS.md) — guía para crear skills
