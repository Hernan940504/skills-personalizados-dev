# Especificación: formato `SKILL.md`

`SKILL.md` es el **manifest canónico** de cada skill. Es lo que el agente lee para decidir si activarlo y cómo ejecutarlo. Este documento define su estructura, campos obligatorios y reglas de calidad.

> Se basa en el formato oficial de Claude Code (Anthropic) y lo **extiende** con metadata necesaria para empaquetado, versionado y compatibilidad multi-herramienta.

---

## 1. Anatomía de un `SKILL.md`

Un `SKILL.md` válido tiene dos partes:

1. **Frontmatter YAML** — metadata estructurada entre `---`.
2. **Body Markdown** — instrucciones para el agente.

```markdown
---
name: backend-java
description: Crea y refactoriza código Spring Boot...
version: 1.0.0
author: HernanBetancurBolivar01
category: backend
tags: [java, spring-boot, junit, maven]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Edit, Write, Bash, Grep]
---

# Backend Java (Spring Boot)

## Cuándo usar este skill
...

## Convenciones
...

## Workflow
...
```

---

## 2. Frontmatter — referencia de campos

### 2.1 Campos obligatorios

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | string (kebab-case) | Identificador único del skill. Debe coincidir con el nombre de la carpeta. Patrón: `^[a-z][a-z0-9-]+$`. |
| `description` | string (≤ 500 chars) | Resumen denso de **qué hace** y **cuándo usarlo**. Es lo que el modelo lee para decidir si activar el skill. Empieza con un verbo. |
| `version` | semver string | Versión del skill. Sigue `MAJOR.MINOR.PATCH`. Cambios breaking → bump MAJOR. |
| `category` | enum | Una de: `backend`, `frontend`, `devops`, `testing`, `security`, `docs`, `workspace`, `files`. |

### 2.2 Campos recomendados

| Campo | Tipo | Descripción |
|---|---|---|
| `author` | string | GitHub handle o nombre del mantenedor principal. |
| `tags` | array<string> | Etiquetas semánticas (stack, frameworks). Usadas para búsqueda y filtrado. |
| `compatibility` | array<enum> | Herramientas soportadas: `claude-code`, `cursor`, `kiro`, `opencode`. Default: todas. |
| `allowed-tools` | array<string> | Herramientas que el skill puede invocar (Claude Code-specific). Ej. `[Read, Edit, Bash]`. Si se omite, usa todas las disponibles. |

### 2.3 Campos opcionales (avanzados)

| Campo | Tipo | Descripción |
|---|---|---|
| `requires` | array<string> | Otros skills de los que depende. Se instalan transitivamente. |
| `min-cli-version` | semver | Versión mínima del CLI `@hbetancur/skills-dev` requerida. |
| `homepage` | url | Link a documentación extendida. |
| `examples` | array<object> | Ejemplos de prompts que activarían este skill. Útil para testing. |

### 2.4 Ejemplo completo de frontmatter

```yaml
---
name: backend-java
description: Crea y refactoriza código Spring Boot siguiendo convenciones de capas
  (controller/service/repository), genera tests JUnit5 con Mockito y cumple checks
  de SonarQube. Úsalo cuando el usuario trabaje en proyectos Java/Maven/Gradle o
  pida scaffolding de endpoints REST.
version: 1.2.0
author: HernanBetancurBolivar01
category: backend
tags: [java, spring-boot, junit, maven, gradle]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Edit, Write, Bash, Grep, Glob]
requires: [testing-generation]
min-cli-version: 0.1.0
homepage: https://github.com/HernanBetancurBolivar01/skills-personalizados-dev/tree/main/skills/backend/backend-java
examples:
  - prompt: "crea un endpoint REST POST /users con validación"
  - prompt: "genera tests JUnit5 para UserService"
---
```

---

## 3. Body Markdown — secciones esperadas

El body debe ser **denso, accionable y libre de relleno**. El agente lo procesa cada vez que el skill se activa: cada token cuenta.

### 3.1 Estructura recomendada

```markdown
# <Título humano>

## Cuándo usar este skill
<2-4 bullets describiendo señales claras de activación>

## Cuándo NO usar
<2-3 bullets describiendo casos límite donde otro skill encaja mejor>

## Convenciones del stack
<Reglas concretas. Una por línea. Sin párrafos largos.>

## Workflow
<Pasos numerados. Idealmente con referencias a scripts/ y templates/>

## Recursos
- `scripts/...` — qué hace
- `templates/...` — qué genera
- `references/...` — qué consultar cuándo

## Anti-patrones
<Errores comunes a evitar>
```

### 3.2 Reglas de oro para el body

| Regla | Por qué |
|---|---|
| Empezar siempre con **"Cuándo usar"** | Es lo segundo que decide la activación tras el `description`. |
| Usar bullets sobre prosa | Más fácil de escanear, menos tokens. |
| Referenciar `scripts/`, `templates/`, `references/` por ruta relativa | El agente sabe dónde buscar. |
| Incluir ejemplos de código solo si son **plantillas reales** | Si el ejemplo no es ejecutable, va en `references/`. |
| Evitar duplicar lo que ya está en `README.md` | El README es para humanos; el SKILL.md para el agente. |

---

## 4. Reglas de calidad sobre `description`

`description` es el campo más crítico. Si está mal escrito, el skill nunca se activa.

**Checklist:**

- [ ] Empieza con un verbo en infinitivo: "Crea…", "Genera…", "Refactoriza…".
- [ ] Menciona el **stack/herramienta** explícito: `Spring Boot`, `React`, `Terraform`.
- [ ] Incluye una cláusula `Úsalo cuando…` que describa **señales de activación**.
- [ ] ≤ 500 caracteres. Ideal: 150-300.
- [ ] Sin emojis, sin markdown, sin saltos de línea raros.

**Ejemplos**

✅ Bueno:
> "Crea y refactoriza código Spring Boot siguiendo convenciones de capas (controller/service/repository), genera tests JUnit5 con Mockito y cumple checks de SonarQube. Úsalo cuando el usuario trabaje en proyectos Java/Maven/Gradle o pida scaffolding de endpoints REST."

❌ Malo (vago, sin señales de activación):
> "Skill para Java."

❌ Malo (no dice cuándo usarlo):
> "Genera código Spring Boot bien estructurado y con buenas prácticas."

---

## 5. Validación

El CLI lintea cada `SKILL.md` con `skills-dev validate`. Reglas aplicadas:

| Regla | Severidad |
|---|---|
| Frontmatter parseable como YAML | error |
| `name` presente, kebab-case, ≤ 50 chars | error |
| `name` coincide con nombre de carpeta | error |
| `description` presente y ≤ 500 chars | error |
| `description` empieza con verbo (heurística) | warning |
| `version` es semver válido | error |
| `category` es un valor del enum | error |
| `tags`, si presente, es array de strings | error |
| `compatibility`, si presente, contiene solo valores del enum | error |
| `allowed-tools`, si presente, contiene tools válidas de Claude Code | warning |
| Body contiene sección `## Cuándo usar` | warning |
| Archivos referenciados en body existen en `scripts/`, `templates/`, `references/` | warning |

---

## 6. Versionado de un skill

Cada skill versiona **de forma independiente** al CLI.

| Tipo de cambio | Bump |
|---|---|
| Mejora de wording sin cambiar comportamiento esperado | PATCH (`1.2.0` → `1.2.1`) |
| Añadir nuevo workflow, script o template sin romper los existentes | MINOR (`1.2.0` → `1.3.0`) |
| Cambiar el nombre del skill, eliminar comportamiento, renombrar scripts | MAJOR (`1.2.0` → `2.0.0`) |

El campo `version` en el frontmatter es la fuente de verdad. El CHANGELOG por skill es opcional (recomendado para skills con mucho uso).

---

## 7. Equivalentes en otras herramientas

Los adaptadores transforman este formato. Ver [`COMPATIBILITY.md`](COMPATIBILITY.md) para el mapping campo a campo.

| Campo SKILL.md | Cursor (`.mdc`) | Kiro (steering) | OpenCode |
|---|---|---|---|
| `name` | `description` (slug) | filename | `name` |
| `description` | `description` | `inclusion` description | `description` |
| `category`, `tags` | (en `globs`/`alwaysApply`) | (en frontmatter custom) | `tags` |
| `allowed-tools` | n/a | n/a | `tools` |
| Body | Body MDC | Body markdown | Body markdown |
