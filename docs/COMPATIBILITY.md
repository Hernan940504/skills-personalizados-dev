# Compatibilidad multi-herramienta

Este documento describe cómo el formato canónico `SKILL.md` se transforma para cada herramienta agéntica soportada, qué funciona y qué tiene limitaciones conocidas.

> **Nota:** este repo cubre cuatro targets de primer nivel (Claude Code, Cursor, Kiro, OpenCode). Las APIs y formatos de estas herramientas evolucionan rápido — verifica la versión soportada en `package.json` antes de reportar bugs.

---

## 1. Matriz de soporte

| Herramienta | Versión mínima | Destino | Formato resultante | Estado |
|---|---|---|---|---|
| **Claude Code** | 2.0+ | `~/.claude/skills/<name>/` o `.claude/skills/<name>/` | `SKILL.md` nativo (carpeta completa) | ✅ nativo |
| **Cursor** | 0.45+ | `~/.cursor/rules/<name>.mdc` o `.cursor/rules/` | `.mdc` con frontmatter MDC | ✅ adaptado |
| **Kiro** | 0.1+ | `.kiro/steering/<name>.md` | Markdown con front-matter de steering | ✅ adaptado |
| **OpenCode** | 0.1+ | `~/.config/opencode/agents/<name>.md` | Markdown + frontmatter custom | ✅ adaptado |

---

## 2. Claude Code (nativo)

### 2.1 Cómo se instala

Se copia/symlinka la carpeta completa del skill a:

- Global: `~/.claude/skills/<name>/`
- Por proyecto: `<proyecto>/.claude/skills/<name>/`

```
~/.claude/skills/backend-java/
├── SKILL.md
├── scripts/
├── templates/
└── references/
```

### 2.2 Transformación

**Ninguna.** Claude Code consume `SKILL.md` directamente. El adapter solo copia/symlinka.

### 2.3 Capacidades soportadas

- ✅ `description` discovery automático.
- ✅ `allowed-tools` respetado por la CLI.
- ✅ `scripts/`, `templates/`, `references/` accesibles desde el agente.
- ✅ Skills por proyecto (sobrescriben los globales).

---

## 3. Cursor

### 3.1 Cómo se instala

Cada skill se transforma en un archivo `.mdc` (Markdown con frontmatter MDC) en:

- Global: `~/.cursor/rules/<name>.mdc`
- Por proyecto: `<proyecto>/.cursor/rules/<name>.mdc`

> Cursor no tiene noción de "skill con carpeta auxiliar". Los archivos en `scripts/`, `templates/`, `references/` se inlinean o se referencian por ruta relativa al repo del usuario.

### 3.2 Transformación de frontmatter

| SKILL.md (canónico) | `.mdc` (Cursor) | Notas |
|---|---|---|
| `name: backend-java` | (filename: `backend-java.mdc`) | El nombre va en el filename. |
| `description: ...` | `description: ...` | Igual. |
| `tags: [java, spring-boot]` | `globs: ["**/*.java", "pom.xml", "build.gradle"]` | Tags se mapean a globs heurísticamente. Editable en `adapter.yml`. |
| `category: backend` | (descartado o como comentario) | Cursor no tiene categorías. |
| `allowed-tools: [...]` | n/a | Cursor no permite restringir tools por rule. |
| Body | Body | Igual, sin transformación. |

Ejemplo `.mdc` generado:

```mdc
---
description: Crea y refactoriza código Spring Boot...
globs: ["**/*.java", "**/pom.xml", "**/build.gradle"]
alwaysApply: false
---

# Backend Java (Spring Boot)
...
```

### 3.3 Limitaciones

- `allowed-tools` no tiene equivalente; Cursor expone todas sus tools al modelo.
- `scripts/` y `templates/` no se ejecutan automáticamente; el rule debe instruir al modelo para invocarlos vía terminal.
- Cursor no recarga rules automáticamente: el usuario debe reiniciar el editor tras un `skills-dev sync`.

---

## 4. Kiro

### 4.1 Cómo se instala

Cada skill se transforma en un steering file:

- Por proyecto: `<proyecto>/.kiro/steering/<name>.md`

> Kiro es orientado a proyecto; no tiene equivalente global directo.

### 4.2 Transformación de frontmatter

| SKILL.md (canónico) | Steering (Kiro) | Notas |
|---|---|---|
| `name` | filename | `backend-java.md` |
| `description` | `inclusion: <description>` | Define cuándo aplicar el steering. |
| `tags` | (comentario o atributo) | Sin equivalente directo. |
| `allowed-tools` | n/a | |
| Body | Body | Igual. |

### 4.3 Limitaciones

- Sin scope global; cada proyecto recibe su copia.
- Sin ejecución directa de scripts (depende del agente que use Kiro).

---

## 5. OpenCode

### 5.1 Cómo se instala

Como agent file en:

- `~/.config/opencode/agents/<name>.md`

### 5.2 Transformación de frontmatter

| SKILL.md (canónico) | OpenCode | Notas |
|---|---|---|
| `name` | `name` | Igual. |
| `description` | `description` | Igual. |
| `allowed-tools` | `tools` | Mapping directo de nombres si existen en OpenCode. |
| `tags` | `tags` | Igual. |
| Body | Body | Igual. |

### 5.3 Limitaciones

- Algunas tools de Claude Code no tienen equivalente en OpenCode (ej. `TaskCreate`). El adaptador las elimina silenciosamente y emite warning.

---

## 6. Resumen de capacidades por target

| Capacidad | Claude Code | Cursor | Kiro | OpenCode |
|---|---|---|---|---|
| Activación por `description` | ✅ | ✅ | ✅ (vía `inclusion`) | ✅ |
| Restricción de tools | ✅ | ❌ | ❌ | ⚠️ parcial |
| `scripts/` ejecutables | ✅ | ⚠️ manual | ⚠️ manual | ⚠️ manual |
| `templates/` accesibles | ✅ | ⚠️ por ruta | ⚠️ por ruta | ⚠️ por ruta |
| `references/` bajo demanda | ✅ | ⚠️ inline | ⚠️ inline | ⚠️ inline |
| Scope global | ✅ | ✅ | ❌ | ✅ |
| Scope por proyecto | ✅ | ✅ | ✅ | ⚠️ |
| Hot-reload | ✅ | ❌ reiniciar | ✅ | ⚠️ |

---

## 7. Reglas de transformación: `adapter.yml`

Cada adaptador en `adapters/<target>/adapter.yml` define declarativamente el mapping:

```yaml
target: cursor
output:
  path: "~/.cursor/rules/{{name}}.mdc"
  format: mdc

frontmatter:
  description: "{{description}}"
  globs: "{{tags | toGlobs}}"
  alwaysApply: false

drop:
  - category
  - version
  - allowed-tools
  - compatibility

warnings:
  - field: allowed-tools
    message: "Cursor no soporta restricción de tools; ignorado."
```

Esto permite ajustar la transformación sin tocar código del CLI — útil cuando las herramientas evolucionan su formato.

---

## 8. Estrategia ante drift de formatos

Las herramientas agénticas cambian rápido. El proyecto adopta:

1. **Tests de snapshot por target** — `tests/adapters.test.js` valida que la transformación produzca exactamente lo esperado.
2. **Pinning de versión soportada** en `package.json` → `peerDependenciesMeta` informativo.
3. **CHANGELOG por adapter** documentando rupturas (`adapters/cursor/CHANGELOG.md`).
4. **Issue template específico** para reportar incompatibilidades nuevas.
