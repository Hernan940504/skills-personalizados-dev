# Cómo contribuir un skill nuevo

Esta guía explica el proceso end-to-end para añadir un skill al catálogo: desde el scaffolding hasta el PR aceptado.

> Si quieres contribuir al **CLI** o a los **adaptadores**, ver `CONTRIBUTING.md` en la raíz del repo.

---

## 1. Antes de empezar — checklist

- [ ] He revisado el [catálogo en el README](../README.md#catálogo-de-skills) y mi skill **no existe** ya.
- [ ] He identificado en qué **categoría** encaja: `backend`, `frontend`, `devops`, `testing`, `security`, `docs`, `workspace`, `files`.
- [ ] Puedo describir en una oración **qué hace** y **cuándo debe activarse**.
- [ ] El skill resuelve **un problema concreto**, no es un "asistente genérico".

Si tu skill no encaja en ninguna categoría existente, **abre primero un issue** proponiendo una nueva categoría antes de codear.

---

## 2. Scaffold del skill

```bash
npx @hbetancur/skills-dev new <name> --category <categoria>
```

Esto crea `skills/<categoria>/<name>/` desde `templates/skill-template/`:

```
skills/backend/backend-rust/
├── SKILL.md          # con placeholders {{TODO}}
├── README.md         # con placeholders {{TODO}}
├── scripts/
│   └── .gitkeep
├── templates/
│   └── .gitkeep
└── references/
    └── .gitkeep
```

---

## 3. Editar `SKILL.md`

Es el archivo más importante. Lee primero [`SKILL-FORMAT.md`](SKILL-FORMAT.md) en detalle.

**Mínimo viable:**

```yaml
---
name: backend-rust
description: <escribir un description denso siguiendo las reglas de SKILL-FORMAT §4>
version: 0.1.0
author: <tu github handle>
category: backend
tags: [rust, axum, tokio]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Edit, Write, Bash, Grep]
---

# Backend Rust (Axum)

## Cuándo usar este skill
- Cuando el repo tiene `Cargo.toml` y un crate con dependencia `axum`.
- Cuando el usuario pide "crear endpoint", "handler", "router".
- ...

## Cuándo NO usar
- Para CLIs Rust sin servidor HTTP → otro skill.
- ...

## Convenciones
- ...

## Workflow
1. ...

## Recursos
- `scripts/cargo-add-route.sh` — añade ruta al router
- `templates/handler.rs.tmpl` — handler con estado compartido
- `references/axum-extractors.md` — guía de extractors

## Anti-patrones
- ...
```

---

## 4. Llenar `README.md`

El README es para **humanos** (el `SKILL.md` es para el agente). Debe incluir:

- Propósito del skill (1 párrafo).
- Pre-requisitos del entorno (versiones de runtime, herramientas).
- Ejemplos de prompts que activan el skill.
- Cómo extender o ajustar localmente.

---

## 5. Añadir `scripts/`, `templates/`, `references/` según necesidad

| Carpeta | Usar cuando… |
|---|---|
| `scripts/` | El skill ejecuta una acción determinística (formato, scaffolding, run de comando). Reduce tokens y riesgo de errores. |
| `templates/` | El skill copia/adapta un bloque de código recurrente. Usar marcadores `{{placeholder}}`. |
| `references/` | Hay documentación larga (convenciones, patrones) que el agente solo necesita en algunos casos. Mantiene el `SKILL.md` corto. |

> Regla: si una sección del SKILL.md supera ~80 líneas, considera mover el detalle a `references/`.

---

## 6. Validar localmente

```bash
# Lintea el frontmatter y la estructura
npx @hbetancur/skills-dev validate

# Instala el skill en modo dev (symlink) y pruébalo en Claude Code
npx @hbetancur/skills-dev add <name> --mode=link
```

Prueba al menos:

- [ ] El skill se activa con un prompt esperado.
- [ ] El skill **no** se activa con un prompt fuera de su scope.
- [ ] Los scripts/templates referenciados se invocan correctamente.

---

## 7. Calidad: checklist antes de PR

| Criterio | Cómo verificar |
|---|---|
| `description` cumple reglas de §4 de SKILL-FORMAT | manual + lint |
| `name` coincide con carpeta | lint |
| Versión es `0.1.0` para skill nuevo | manual |
| Body tiene sección `## Cuándo usar` y `## Cuándo NO usar` | manual |
| Todos los archivos referenciados existen | lint |
| No duplica funcionalidad de un skill existente | revisión del catálogo |
| Probado en al menos `claude-code` | manual |
| README.md tiene ejemplos de prompts | manual |
| Sin secretos, paths absolutos del autor, ni datos personales | manual |

---

## 8. Workflow Git

```bash
git checkout -b skill/<name>
# … hacer cambios …
git add skills/<categoria>/<name>/
git commit -m "feat(skill): add <name>"
git push origin skill/<name>
gh pr create --title "feat(skill): add <name>" --body "<descripción>"
```

**Convenciones de commit:**

| Tipo | Cuándo |
|---|---|
| `feat(skill): add <name>` | Nuevo skill |
| `feat(skill): <name> add <feature>` | Mejora a skill existente |
| `fix(skill): <name> <bug>` | Bugfix en un skill |
| `docs(skill): <name> <cambio>` | Solo doc del skill |
| `chore(skill): <name> bump version` | Subir version |

---

## 9. CI automático

Al abrir el PR, el workflow `validate-skills.yml` ejecuta:

1. `skills-dev validate` sobre todos los skills.
2. Tests de snapshot de adaptadores afectados.
3. Verificación de naming y estructura.

Si falla, revisa la salida del job — los errores son específicos por archivo.

---

## 10. Después del merge

- Tu skill aparece en el catálogo del README en el próximo release.
- Bump de versión menor del repo (`v0.X.0 → v0.X+1.0`) si añade un skill nuevo.
- Si quieres mantenerlo, añade tu handle al campo `author` — recibirás menciones en issues.

---

## 11. Buenas prácticas de diseño de skills

Lecciones de los repos referencia (`anthropics/skills`, `obra/superpowers`):

1. **Un skill = un problema concreto, no un dominio entero.** "backend-java" es OK porque el stack es coherente; "backend" solo no lo es.
2. **El `description` es marketing para el modelo.** Optimiza activación, no estética.
3. **Prefiere scripts deterministas a explicaciones largas.** Si el modelo va a ejecutar siempre los mismos pasos, codifícalos.
4. **Los `references/` son archivos de lectura bajo demanda.** No los menciones en el body principal salvo cuando sean relevantes.
5. **Testea anti-patrones explícitamente.** Un skill que se activa cuando no debe es peor que uno que no se activa cuando debe.
