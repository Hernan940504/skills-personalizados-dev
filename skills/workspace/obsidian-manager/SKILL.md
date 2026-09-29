---
name: obsidian-manager
description: Construye y mantiene un second brain en un vault local de Obsidian vía un CLI Python
  sin dependencias. Crea notas con frontmatter/tags/wikilinks, busca por texto/tag/backlink,
  navega el grafo (backlinks, huérfanas, rotos), ingiere archivos externos como notas, registra
  daily notes, pendientes y contexto de proyectos; orquesta otros skills del repo como fuentes.
  Úsalo cuando el usuario hable de su second brain u Obsidian, notas, registrar el trabajo del día,
  pendientes o ingerir material.
version: 1.0.0
author: Hernan940504
category: workspace
tags: [obsidian, second-brain, markdown, wikilinks, frontmatter, notes, knowledge-base, cli, python]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Bash]
examples:
  - prompt: "inicializa mi second brain de Obsidian"
  - prompt: "crea una nota sobre el rightsizing de Ciencuadras y enlázala al proyecto"
  - prompt: "registra en el diario de hoy que avancé en el skill de Obsidian"
  - prompt: "añade un pendiente: validar el CIDR de PROD"
  - prompt: "ingiere este PDF al vault dentro del proyecto ciencuadras"
  - prompt: "qué notas enlazan a la nota de arquitectura"
  - prompt: "lista las notas huérfanas del vault"
  - prompt: "sincroniza la fuente drive-proyectos"
---

# obsidian-manager — Second brain en un vault de Obsidian

## Cuándo usar este skill

- El usuario quiere capturar, organizar o consultar conocimiento en su vault de Obsidian (notas `.md`).
- Pide crear/actualizar notas, registrar el día a día (daily note), gestionar pendientes o contexto de proyectos.
- Pide ingerir material externo (archivos ya en disco, p. ej. descargados de Drive) como notas del brain.
- Pide navegar enlaces: backlinks, notas huérfanas, enlaces rotos, o buscar por texto/tag.
- Pide alimentar el brain desde otra capacidad del repo (una "fuente" registrada).

## Cuándo NO usar

- Descargar de Google Drive: eso es `google-drive-manager`. Este skill **ingiere** lo que ya está en disco, no descarga.
- Leer/escribir Google Sheets: usar `sheets-connect`.
- Editar la configuración interna de Obsidian (plugins, temas, `.obsidian/`): fuera de alcance.
- Borrado permanente de notas: **no soportado a propósito** (solo `trash`/`restore` reversibles).

## Requisitos previos

- Python 3.12+. **Sin dependencias externas** (solo biblioteca estándar): no requiere `pip install`.
- El vault se resuelve desde `OBSIDIAN_VAULT_PATH` (default `~/second-brain`). Se puede sobreescribir por comando con `--vault <ruta>`.
- Primer uso: ejecutar `init` una vez para crear el vault. Detalles en `README.md`.

## Cómo ejecutar y parsear la salida

Todos los comandos se ejecutan con el CLI y **devuelven JSON en stdout**:

```bash
python3 skills/workspace/obsidian-manager/scripts/obsidian_cli.py <comando> [opciones]
```

- Parsea stdout como JSON. En error, el JSON `{"error": {"type","message"}}` va a **stderr** y el código de salida es != 0.
- Flags globales (`--pretty`, `--dry-run`, `--yes`, `--vault`, `--log-level`) se aceptan **antes o después** del subcomando.
- Añade `--pretty` solo para mostrar al usuario; para uso programático deja el JSON compacto.
- Códigos de salida: `0` ok · `2` uso/ruta insegura · `3` permisos · `4` no encontrado (vault o nota) · `6` conflicto o confirmación requerida.
- Si el código es `4` con mensaje de vault, ejecuta `init`. Si es `6`, es una destructiva sin confirmar: reintenta con `--yes` tras confirmar con el usuario.

## Reglas de seguridad y confirmación (OBLIGATORIAS)

- El skill **solo escribe dentro del vault**: rechaza rutas que lo escapen (código 2).
- **Confirma con el usuario ANTES** de operaciones destructivas y ejecútalas con `--yes`:
  - `note update --body` (reemplaza el cuerpo de una nota).
  - `note create ... --on-conflict overwrite` (sobrescribe una nota existente).
  - `trash` (envía a la papelera del vault).
- El CLI **rechaza** estas operaciones sin `--yes` (código 6). Para previsualizar, usa `--dry-run`.
- Flujo recomendado: corre con `--dry-run`, muestra el plan, y solo tras confirmación explícita repite con `--yes`.
- No hay borrado permanente: `trash` es reversible con `restore`.
- Nunca imprimas el cuerpo completo de notas del usuario si no es necesario; el skill no registra contenido en logs.

## Workflow por subcomando

### Inicializar el vault (una vez)
```bash
python3 scripts/obsidian_cli.py init
# o en una ruta concreta:
python3 scripts/obsidian_cli.py init ~/second-brain
```
Crea `inbox/`, `proyectos/`, `daily/`, `referencias/adjuntos/`, `plantillas/`, `.trash/`, `.brain/fuentes.json`, `.obsidian/` e `index.md`. Es idempotente.

### Crear / actualizar notas
```bash
python3 scripts/obsidian_cli.py note create "Título de la nota" --body "contenido" --tag infra --project ciencuadras
python3 scripts/obsidian_cli.py note append <nota> "línea a añadir"
python3 scripts/obsidian_cli.py note update <nota> --frontmatter '{"estado":"activo"}'
python3 scripts/obsidian_cli.py --yes note update <nota> --body "nuevo cuerpo"   # destructivo
```
`<nota>` acepta el nombre de archivo (slug) o una ruta relativa. Con `--project`, la nota se enlaza al contexto del proyecto, el contexto la registra y el slug del proyecto se agrega automáticamente como tag canónico de la línea de negocio (sin duplicar, va primero) para que los grupos de color del grafo coloreen la nota por su dominio. Aplica igual en `note create` e `ingest`.

### Buscar
```bash
python3 scripts/obsidian_cli.py search --text "rightsizing"
python3 scripts/obsidian_cli.py search --tag infra
python3 scripts/obsidian_cli.py search --links-to <nota>       # backlinks
python3 scripts/obsidian_cli.py search --folder proyectos --limit 50
```

### Grafo
```bash
python3 scripts/obsidian_cli.py graph backlinks <nota>
python3 scripts/obsidian_cli.py graph outlinks <nota>          # separa enlaces rotos
python3 scripts/obsidian_cli.py graph orphans
```
Los wikilinks apuntan al **nombre de archivo (slug)** de la nota destino; si no existe, el enlace se reporta como roto.

### Ingesta de material externo
```bash
python3 scripts/obsidian_cli.py ingest ./descargas/informe.md --project ciencuadras --tag drive
python3 scripts/obsidian_cli.py ingest ./descargas/informe.pdf   # binario -> copia a adjuntos + nota-índice
echo "captura rápida" | python3 scripts/obsidian_cli.py ingest - --title "Idea"
```
Puente con Drive: primero `google-drive-manager download ... --export md`, luego `ingest` de los archivos descargados.

### Daily note (día a día)
```bash
python3 scripts/obsidian_cli.py daily                              # crea/abre la de hoy
python3 scripts/obsidian_cli.py daily --add "avancé en X" --project ciencuadras
python3 scripts/obsidian_cli.py daily --add "nota de ayer" --date 2026-09-24
```

### Pendientes / tareas
```bash
python3 scripts/obsidian_cli.py task add "validar CIDR" --project ciencuadras
python3 scripts/obsidian_cli.py task list                          # todas las abiertas del vault
python3 scripts/obsidian_cli.py task list --project ciencuadras --include-done
python3 scripts/obsidian_cli.py task done "validar CIDR"
```

### Contexto de proyectos
```bash
python3 scripts/obsidian_cli.py project create "Ciencuadras" --status activo
python3 scripts/obsidian_cli.py project note ciencuadras "decisión: /21 de CIDR" --section Decisiones
python3 scripts/obsidian_cli.py project list
```

### Orquestación de fuentes (cada skill nuevo = nueva capacidad)
```bash
python3 scripts/obsidian_cli.py sources list
python3 scripts/obsidian_cli.py --dry-run sources sync drive-proyectos
python3 scripts/obsidian_cli.py sources sync drive-proyectos
```
Las fuentes se declaran en `<vault>/.brain/fuentes.json` (datos, no código): nombre, `skill_path`, `command` y `map`. Registrar una fuente nueva NO requiere tocar el código del skill. Ver `README.md`.

### Papelera (reversible)
```bash
python3 scripts/obsidian_cli.py --dry-run trash <nota>
python3 scripts/obsidian_cli.py --yes trash <nota>
python3 scripts/obsidian_cli.py restore <nombre-en-papelera>
```

## Anti-patrones

- No usar este skill para descargar de Drive/Sheets: solo ingiere lo que ya está en disco.
- No ejecutar `trash`, `note update --body` ni `overwrite` sin confirmación del usuario (`--yes`).
- No generar wikilinks al título con espacios/mayúsculas: usar el slug del archivo destino, o quedará como enlace roto.
- No codificar lógica específica de una fuente en el skill: se declara en `.brain/fuentes.json`.
- No asumir que el vault existe: si un comando da código 4 por vault ausente, ejecutar `init`.
- No escribir fuera del vault: el skill lo rechaza por diseño.

## Recursos

- `scripts/obsidian_cli.py` — CLI con subcomandos (punto de entrada del agente).
- `scripts/vault.py` — cliente del vault (notas, búsqueda, grafo, daily, tareas, proyectos, ingesta, papelera).
- `scripts/frontmatter.py` — parseo/serialización de frontmatter YAML mínimo (round-trip, sin dependencias).
- `scripts/markdown_index.py` — extracción de wikilinks/tags y construcción del grafo (backlinks/huérfanas/rotos).
- `scripts/sources.py` — orquestación de fuentes: invoca otros skills del repo y mapea su salida a `ingest`.
- `README.md` — setup del vault, `OBSIDIAN_VAULT_PATH`, estructura, registro de fuentes y cómo abrirlo en Obsidian.
