# Tasks — Skill `obsidian-manager`

Cada tarea incluye sus tests, que corren sin red y sobre un vault temporal (`tmp_path`), sin tocar
el vault real del usuario. Se implementa tarea por tarea; ninguna se marca completada hasta que sus
tests pasen. Sin dependencias externas (solo stdlib).

- [ ] 1. Scaffolding del skill
  - Crear `skills/workspace/obsidian-manager/` con `scripts/` y `tests/`.
  - Añadir patrones al `.gitignore` del repo si aplica (p. ej. vaults locales de prueba, `.brain/tmp/`).
  - Sin `requirements.txt` de terceros (design §9); documentar la política stdlib.
  - _Requisitos: RNF-1, RNF-3_

- [ ] 2. `frontmatter.py` — parseo/serialización round-trip
  - `parse(text)`, `dump(fm, body)`, `merge(base, updates)`; parser YAML mínimo (escalares, listas bloque/inline, fechas ISO); fallo explícito ante YAML fuera de alcance.
  - Tests: round-trip preserva campos y valores; merge une tags sin duplicar; archivo sin frontmatter → `{}` + body intacto; YAML no soportado falla claro.
  - _Requisitos: 2.5, 2.7, RNF-1, RNF-4_

- [ ] 3. `markdown_index.py` — wikilinks, tags, grafo
  - `extract_wikilinks`, `extract_tags` (frontmatter + inline `#tag`, ignorando code fences), `build_index`, `resolve_link` (por nombre y alias, marca `broken`).
  - Tests: extrae `[[a]]` y `[[a|alias]]`; ignora `#` en code; backlinks invertidos correctos; alias resuelve; enlace roto se marca.
  - _Requisitos: 3.2, 3.3, 4.1–4.4_

- [ ] 4. `vault.py` — resolución, seguridad y escritura
  - `VaultClient(vault_path)`, `_safe_path` (anti path-traversal), `_atomic_write`, `slugify` (colisiones con sufijo).
  - Tests: `..`/absoluta fuera del vault → `UnsafePathError`; escritura atómica no deja `.tmp`; slug evita colisión.
  - _Requisitos: RNF-3, RNF-4_

- [ ] 5. `vault.py` — `init` del vault
  - Crea estructura (design §3): `inbox/`, `proyectos/`, `daily/`, `referencias/adjuntos/`, `plantillas/`, `.trash/`, `.brain/fuentes.json`, `.obsidian/` mínimo, `index.md`, `pendientes.md`. Idempotente.
  - Resolución desde `OBSIDIAN_VAULT_PATH` (default `~/second-brain`).
  - Tests: init crea todo; segundo init es idempotente (no sobrescribe); operación sin vault → `NotFoundError`.
  - _Requisitos: 1.1–1.5_

- [ ] 6. `vault.py` — notas: create/append/update
  - `create_note` (frontmatter + slug + estrategia de colisión new/skip/overwrite), `append_note`, `update_frontmatter` (merge), `update_body` (destructivo).
  - Tests: create genera frontmatter y slug; colisión ofrece estrategia; append no toca frontmatter; update_frontmatter conserva cuerpo; update_body sin `--yes` se bloquea (a nivel CLI, ver tarea 12).
  - _Requisitos: 2.1–2.7_

- [ ] 7. `vault.py` — búsqueda
  - `search` por texto (cuerpo/frontmatter), por tag, por `--links-to` (backlinks), filtro `--folder`, `--limit` con `truncated`.
  - Tests: texto devuelve fragmento; tag encuentra frontmatter e inline; links-to usa el índice; cero resultados → lista vacía código 0; truncado marca flag.
  - _Requisitos: 3.1–3.5_

- [ ] 8. `vault.py` — grafo
  - `backlinks`, `outlinks` (marca rotos), `orphans`.
  - Tests: backlinks correctos; outlinks distingue roto; orphans detecta nota sin entradas ni salidas.
  - _Requisitos: 4.1–4.4_

- [ ] 9. `vault.py` — ingesta
  - `ingest` de archivo texto/markdown (fusiona frontmatter, registra `source`), de binario (copia a `referencias/adjuntos/` + nota-índice con embed), y por stdin; `--project` y `--link`; `--dry-run`.
  - Tests: md preserva contenido y fusiona frontmatter; binario se copia y se crea nota-índice; stdin crea nota; `--project` enlaza a contexto; dry-run no escribe.
  - _Requisitos: 5.1–5.6_

- [ ] 10. `vault.py` — daily y tareas
  - `daily`/`daily_add` (secciones base, timestamp, `--date`, `--project`), `task_add`/`task_list`/`task_done` (checkbox, recolección global, filtro por proyecto/estado).
  - Tests: daily crea secciones y no sobrescribe; add inserta con timestamp; task_list recolecta `- [ ]` de todo el vault; done marca `- [x]` conservando texto; filtros por proyecto.
  - _Requisitos: 6.1–6.4, 7.1–7.4_

- [ ] 11. `vault.py` — proyectos + `sources.py`
  - `project_create`/`project_note`/`project_list` (contexto con secciones, estado en frontmatter, autolink de notas con `--project`).
  - `sources.py`: `load_sources`, `sync` (invoca CLI del skill fuente vía `subprocess`, mapea salida→`ingest`, fallo aislado por fuente), `list`.
  - Tests: project create genera `_contexto.md`; note añade entrada fechada; list lee estado; sync con skill fuente **mockeado** (subprocess parcheado) crea notas sin lógica específica del skill; fuente fallida se reporta sin corromper el vault.
  - _Requisitos: 8.1–8.4, 9.1–9.5_

- [ ] 12. `obsidian_cli.py` — capa CLI
  - Subparsers de todos los comandos; parser padre con flags globales `--pretty/--dry-run/--yes/--log-level` (antes o después del subcomando); serialización JSON; códigos de salida (design §5); bloqueo de destructivas sin `--yes`/`--dry-run`.
  - Tests: dispatch de subcomandos, JSON vs `--pretty`, exit codes por tipo de error, dry-run no ejecuta, `update --body`/`overwrite` sin confirmación se rechaza (código 6).
  - _Requisitos: 2.3, 2.6, RNF-2, RNF-3_

- [ ] 13. `SKILL.md`
  - Frontmatter (`name: obsidian-manager`, `description` con frases de activación, `version: 1.0.0`, `category: workspace`, `tags`, `compatibility`, `allowed-tools: [Read, Bash]`, `examples`).
  - Body: cuándo usar / cuándo no, workflow por subcomando, cómo parsear la salida JSON, orquestación de fuentes, reglas de seguridad/confirmación, anti-patrones.
  - _Requisitos: objetivo global, criterios de aceptación_

- [ ] 14. `README.md` (setup humano)
  - Qué es el second brain, cómo `init` el vault, variable `OBSIDIAN_VAULT_PATH`, estructura del vault, ejemplos por subcomando, cómo registrar una fuente en `fuentes.json` (ejemplo Drive), notas de seguridad, cómo abrir el vault en Obsidian.
  - _Requisitos: criterios de aceptación globales_

- [ ] 15. Verificación final
  - Ejecutar toda la suite sin red ni dependencias externas; confirmar exit codes, ausencia de borrado permanente y del test de path traversal; inicializar un vault real de demostración y validar `SKILL.md` contra las reglas del repo.
  - _Requisitos: RNF-5, criterios de aceptación globales_
