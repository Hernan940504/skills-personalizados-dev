# skills-personalizados-dev

> Fábrica de **skills agénticos** para desarrollo de software, multi-herramienta y de código abierto.

Catálogo curado de skills (instrucciones especializadas para agentes de IA) organizados por categoría y enfoque, distribuibles con un solo comando y compatibles con las principales herramientas agénticas del mercado: **Claude Code, Cursor, Kiro y OpenCode**.

Inspirado en [`anthropics/skills`](https://github.com/anthropics/skills), pensado para uso local intensivo y para compartir con el ecosistema.

---

## Índice

- [Filosofía](#filosofía)
- [Instalación rápida](#instalación-rápida)
- [Catálogo de skills](#catálogo-de-skills)
- [Compatibilidad multi-herramienta](#compatibilidad-multi-herramienta)
- [CLI: `@hbetancur/skills-dev`](#cli-hbetancurskills-dev)
- [Estructura del repo](#estructura-del-repo)
- [Documentación](#documentación)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

---

## Filosofía

Un **skill** es una unidad reutilizable de capacidad para un agente: instrucciones, plantillas, scripts y referencias que el agente carga bajo demanda para resolver un tipo concreto de tarea (ej. "scaffolding de un controlador Spring Boot con tests JUnit5").

Este repo se construye sobre 4 principios:

1. **Una sola fuente de verdad** — el `SKILL.md` es canónico; los formatos de otras herramientas se generan vía adaptadores.
2. **Especialización por categoría y stack** — `backend-java` ≠ `backend-node`. Cada skill resuelve bien una cosa.
3. **Documentación primero** — todo skill incluye `README.md` humano + `SKILL.md` para el agente.
4. **Instalación trivial** — un comando lo deja listo en tu IDE favorito.

---

## Instalación rápida

### Opción A — usuario final (recomendada)

```bash
# Instalar un skill en Claude Code (default)
npx @hbetancur/skills-dev add backend-java

# Instalar varios
npx @hbetancur/skills-dev add backend-java backend-node

# Toda una categoría
npx @hbetancur/skills-dev add --category devops

# Targetear otra herramienta
npx @hbetancur/skills-dev add backend-java --target cursor
```

### Opción B — desarrollo activo (clonando el repo)

```bash
git clone https://github.com/HernanBetancurBolivar01/skills-personalizados-dev.git
cd skills-personalizados-dev
./scripts/install.sh --mode=link    # symlinks a ~/.claude/skills/
```

Con `--mode=link` editas en el repo y los cambios se reflejan al instante.

---

## Catálogo de skills

> **Estado:** MVP en construcción. Los skills marcados ✅ están disponibles; ⏳ están planificados.

### Backend

| Skill | Stack | Estado | Descripción corta |
|---|---|---|---|
| `backend-java` | Java + Spring Boot | ⏳ | Scaffolding REST por capas, JUnit5 + Mockito, convenciones SonarQube |
| `backend-node` | Node + NestJS/Express | ⏳ | Módulos NestJS, controllers/services, tests con Vitest |
| `backend-python` | Python + FastAPI | ⏳ | Endpoints async, Pydantic, pytest + fixtures |
| `backend-go` | Go + Gin/Echo | ⏳ | Handlers idiomáticos, middlewares, testing estándar |

### Frontend

| Skill | Stack | Estado | Descripción corta |
|---|---|---|---|
| `frontend-react` | React + TS | ⏳ | Componentes funcionales, hooks, RTL + Vitest |
| `frontend-vue` | Vue 3 + TS | ⏳ | Composition API, Pinia, Vitest + Testing Library |
| `frontend-angular` | Angular + TS | ⏳ | Standalone components, signals, Jest |

### DevOps / Infra

| Skill | Stack | Estado | Descripción corta |
|---|---|---|---|
| `devops-docker` | Docker | ⏳ | Dockerfiles multi-stage, docker-compose, optimización de capas |
| `devops-kubernetes` | K8s | ⏳ | Manifests, Helm charts básicos, sondas y recursos |
| `devops-terraform` | Terraform | ⏳ | Módulos reutilizables, state remoto, naming consistente |
| `devops-cicd-gha` | GitHub Actions | ⏳ | Workflows reutilizables, matrix builds, caching |

### Testing

| Skill | Estado | Descripción corta |
|---|---|---|
| `testing-generation` | ⏳ | Genera tests unitarios e integración a partir de código existente |
| `testing-coverage` | ⏳ | Analiza coverage y propone tests faltantes con razonamiento |

### Security

| Skill | Estado | Descripción corta |
|---|---|---|
| `security-owasp` | ⏳ | Review estilo OWASP Top 10 sobre el diff actual |
| `security-deps-audit` | ⏳ | Audita dependencias y propone upgrades seguros |

### Docs

| Skill | Estado | Descripción corta |
|---|---|---|
| `docs-adr` | ⏳ | Crea Architectural Decision Records bien estructurados |
| `docs-readme` | ⏳ | Genera/actualiza README desde el estado real del repo |

### Workspace

| Skill | Estado | Descripción corta |
|---|---|---|
| `workspace-git-flow` | ⏳ | Convenciones de branches, conventional commits, PR templates |
| `workspace-monorepo` | ⏳ | Comandos cross-paquete, dependency graphs, Nx/Turbo patterns |

### Files

| Skill | Estado | Descripción corta |
|---|---|---|
| `files-pdf` | ⏳ | Lectura/extracción/manipulación de PDFs |
| `files-csv` | ⏳ | Procesamiento de CSV grandes con streaming |

---

## Compatibilidad multi-herramienta

| Herramienta | Destino | Formato | Adapter |
|---|---|---|---|
| Claude Code | `~/.claude/skills/<name>/` | SKILL.md nativo | `adapters/claude-code/` |
| Cursor | `.cursor/rules/<name>.mdc` | MDC con frontmatter | `adapters/cursor/` |
| Kiro | `.kiro/steering/<name>.md` | Markdown steering | `adapters/kiro/` |
| OpenCode | `~/.config/opencode/agents/<name>.md` | Markdown + frontmatter | `adapters/opencode/` |

Ver [`docs/COMPATIBILITY.md`](docs/COMPATIBILITY.md) para las reglas de transformación y limitaciones por herramienta.

---

## CLI: `@hbetancur/skills-dev`

```bash
# Catálogo
npx @hbetancur/skills-dev list                       # Todo el catálogo
npx @hbetancur/skills-dev list --installed           # Solo lo instalado
npx @hbetancur/skills-dev list --category backend

# Instalación
npx @hbetancur/skills-dev add <skill> [<skill>...]
npx @hbetancur/skills-dev add --category <cat>
npx @hbetancur/skills-dev add --all
npx @hbetancur/skills-dev add <skill> --target cursor
npx @hbetancur/skills-dev add <skill> --mode link    # symlink (dev)
npx @hbetancur/skills-dev add <skill> --mode copy    # copia (default usuarios)

# Gestión
npx @hbetancur/skills-dev remove <skill>
npx @hbetancur/skills-dev sync                       # re-aplica instalaciones
npx @hbetancur/skills-dev update                     # git pull + sync

# Desarrollo
npx @hbetancur/skills-dev new <skill> --category backend
npx @hbetancur/skills-dev validate                   # lint de SKILL.md
```

---

## Estructura del repo

```
skills-personalizados-dev/
├── skills/              # Catálogo agrupado por categoría
├── adapters/            # Transforma SKILL.md al formato de cada IDE
├── templates/           # Template base para crear skills nuevos
├── bin/                 # Entry point del CLI
├── scripts/             # install.sh, new-skill.sh, validate.sh
├── docs/                # Arquitectura, formato, compatibilidad
├── tests/               # Validación de skills
└── .github/workflows/   # CI: validate + release
```

Detalle completo en [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Documentación

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — topología del monorepo y flujo de adaptadores
- [`docs/SKILL-FORMAT.md`](docs/SKILL-FORMAT.md) — especificación del `SKILL.md`
- [`docs/COMPATIBILITY.md`](docs/COMPATIBILITY.md) — matriz multi-herramienta
- [`docs/CONTRIBUTING-SKILLS.md`](docs/CONTRIBUTING-SKILLS.md) — cómo crear y aportar un skill

---

## Contribuir

```bash
# Scaffold de un nuevo skill
npx @hbetancur/skills-dev new mi-skill --category backend

# Valida el formato
npx @hbetancur/skills-dev validate
```

Antes de abrir un PR revisa [`docs/CONTRIBUTING-SKILLS.md`](docs/CONTRIBUTING-SKILLS.md).

---

## Inspiración y créditos

Repos que sirvieron de referencia:

- [`anthropics/skills`](https://github.com/anthropics/skills) — formato canónico
- [`obra/superpowers`](https://github.com/obra/superpowers) — skills meta de alta calidad
- [`wshobson/agents`](https://github.com/wshobson/agents) — biblioteca de subagents
- [`davila7/claude-code-templates`](https://github.com/davila7/claude-code-templates) — CLI similar
- [`VoltAgent/awesome-claude-code-subagents`](https://github.com/VoltAgent/awesome-claude-code-subagents) — listas curadas

---

## Licencia

MIT © Hernán Betancur
