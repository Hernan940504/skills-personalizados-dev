# obsidian-manager

Skill para construir y mantener un **second brain** en un vault local de **Obsidian** desde un CLI
Python: crear/actualizar notas con frontmatter, tags y wikilinks; buscar; navegar el grafo de
enlaces; ingerir material externo; registrar el día a día, pendientes y contexto de proyectos; y
orquestar otros skills del repo como fuentes de conocimiento.

> Documentación para humanos. Las instrucciones que consume el agente están en `SKILL.md`.

---

## 1. Requisitos

- Python 3.12+.
- **Sin dependencias externas**: el skill usa solo la biblioteca estándar. No hay `pip install`
  ni `requirements.txt` de terceros (política de supply chain: menos superficie, nada que pasar por JFrog).
- (Opcional) La app de Obsidian para abrir el vault visualmente. El skill funciona sin ella.

## 2. El vault (second brain)

Un *vault* de Obsidian es simplemente una carpeta de archivos Markdown (`.md`) más adjuntos. Este
skill trabaja 100% en local sobre esa carpeta; no hace llamadas de red ni usa credenciales.

### 2.1 Dónde vive el vault

La ruta se resuelve en este orden:

1. `--vault <ruta>` pasado al comando.
2. Variable de entorno `OBSIDIAN_VAULT_PATH`.
3. Default: `~/second-brain`.

Configura la variable para no repetir `--vault`:

```bash
export OBSIDIAN_VAULT_PATH="$HOME/second-brain"
```

### 2.2 Inicializar

```bash
python3 scripts/obsidian_cli.py init
# o en una ruta concreta:
python3 scripts/obsidian_cli.py init ~/Documents/second-brain
```

`init` es idempotente y crea esta estructura:

```
<vault>/
├── .obsidian/            # para que Obsidian reconozca el vault (config mínima, no se sobrescribe)
├── .brain/
│   └── fuentes.json      # registro de fuentes (orquestación de skills)
├── .trash/               # papelera reversible (no hay borrado permanente)
├── index.md              # nota raíz / mapa de contenido
├── inbox/                # captura sin clasificar (default de note create / ingest)
├── daily/                # daily notes YYYY-MM-DD.md
├── proyectos/            # proyectos/<slug>/_contexto-<slug>.md
├── referencias/
│   └── adjuntos/         # binarios ingeridos (PDF, imágenes)
├── plantillas/
└── pendientes.md         # tareas globales
```

### 2.3 Abrir en Obsidian

En Obsidian: **Abrir carpeta como vault** → selecciona la carpeta del vault (`$OBSIDIAN_VAULT_PATH`).
Las notas creadas por el CLI aparecen al instante; los wikilinks `[[...]]` y tags se resuelven en el grafo de Obsidian.

## 3. Uso — ejemplos por subcomando

Todos los comandos imprimen **JSON** en stdout. Añade `--pretty` para lectura humana. Los flags
globales (`--pretty`, `--dry-run`, `--yes`, `--vault`, `--log-level`) se aceptan antes o después del subcomando.

### Notas
```bash
python3 scripts/obsidian_cli.py note create "Rightsizing PROD" --body "análisis inicial" --tag infra --project ciencuadras
python3 scripts/obsidian_cli.py note append rightsizing-prod "nueva observación"
python3 scripts/obsidian_cli.py note update rightsizing-prod --frontmatter '{"estado":"revisado"}'
python3 scripts/obsidian_cli.py --yes note update rightsizing-prod --body "cuerpo reemplazado"   # destructivo
```

### Buscar y grafo
```bash
python3 scripts/obsidian_cli.py search --text "rightsizing" --pretty
python3 scripts/obsidian_cli.py search --tag infra
python3 scripts/obsidian_cli.py graph backlinks rightsizing-prod
python3 scripts/obsidian_cli.py graph orphans
```

### Día a día, pendientes y proyectos
```bash
python3 scripts/obsidian_cli.py project create "Ciencuadras" --status activo
python3 scripts/obsidian_cli.py daily --add "avancé en el skill de Obsidian" --project ciencuadras
python3 scripts/obsidian_cli.py task add "validar CIDR de PROD" --project ciencuadras
python3 scripts/obsidian_cli.py task list --pretty
python3 scripts/obsidian_cli.py task done "validar CIDR"
```

### Ingesta
```bash
# Markdown/texto: se convierte en nota, fusionando su frontmatter con el generado.
python3 scripts/obsidian_cli.py ingest ./descargas/informe.md --project ciencuadras --tag drive
# Binario (PDF/imagen): se copia a referencias/adjuntos/ y se crea una nota-índice que lo embebe.
python3 scripts/obsidian_cli.py ingest ./descargas/informe.pdf
# Texto por stdin:
echo "captura rápida" | python3 scripts/obsidian_cli.py ingest - --title "Idea suelta"
```

## 4. Puente con otros skills (fuentes)

El objetivo del second brain es que **cada capacidad nueva del repo sea una fuente**. La ingesta es
agnóstica del origen; la orquestación vive en `<vault>/.brain/fuentes.json` (datos, no código):
registrar una fuente nueva **no requiere modificar el skill**.

### 4.1 Puente manual con Google Drive

```bash
# 1) Descargar material de un proyecto con google-drive-manager (exportando a Markdown)
python3 skills/workspace/google-drive-manager/scripts/drive_cli.py \
  download <FOLDER_ID> ./.brain/tmp/drive --recursive --export md

# 2) Ingerir lo descargado al vault, asociándolo a un proyecto
python3 skills/workspace/obsidian-manager/scripts/obsidian_cli.py \
  ingest ./.brain/tmp/drive/<archivo>.md --project ciencuadras --tag drive
```

### 4.2 Fuente automatizada (`fuentes.json`)

Declara la fuente una vez en `<vault>/.brain/fuentes.json`:

```json
{
  "sources": [
    {
      "name": "drive-proyectos",
      "description": "Descarga material de proyectos desde Google Drive e ingiere como notas",
      "skill_path": "skills/workspace/google-drive-manager/scripts/drive_cli.py",
      "command": ["download", "<FOLDER_ID>", "./.brain/tmp/drive", "--recursive", "--export", "md"],
      "map": { "content_from": "downloaded", "project": "ciencuadras", "tags": ["drive", "ingesta"] }
    }
  ]
}
```

Luego:

```bash
python3 scripts/obsidian_cli.py sources list
python3 scripts/obsidian_cli.py --dry-run sources sync drive-proyectos   # muestra qué ejecutaría
python3 scripts/obsidian_cli.py sources sync drive-proyectos             # invoca el skill e ingiere
```

Campos de una fuente:

| Campo | Descripción |
|---|---|
| `name` | Identificador de la fuente. |
| `skill_path` | Ruta (relativa al repo) del CLI del skill fuente. |
| `command` | Argumentos que se pasan a ese CLI. |
| `map.content_from` | Clave de la salida JSON del skill que contiene la(s) ruta(s) a ingerir. |
| `map.project` | Proyecto al que asociar las notas ingeridas (opcional). |
| `map.tags` | Tags para las notas ingeridas (opcional). |

> El fallo de una fuente se reporta de forma aislada y **no corrompe el vault**.

## 5. Códigos de salida

| Código | Significado |
|---|---|
| 0 | Éxito |
| 2 | Error de uso/argumentos o ruta insegura (fuera del vault) |
| 3 | Permisos insuficientes sobre el vault |
| 4 | No encontrado (vault o nota; si es el vault, ejecuta `init`) |
| 6 | Conflicto de nombre o confirmación requerida (usa `--yes` o `--dry-run`) |

## 6. Seguridad

- El skill **solo escribe dentro del vault**: canonicaliza cada ruta (`realpath`) y rechaza las que
  lo escapen (`..` o absolutas).
- **Sin red y sin secretos**: operación 100% local; no lee credenciales. `sources sync` solo invoca
  otros CLIs del repo por su ruta (cada skill fuente gestiona su propia auth).
- **Sin borrado permanente**: `trash` mueve a `.trash/` (reversible con `restore`).
- **Confirmación explícita** (`--yes`) o `--dry-run` en operaciones destructivas: reemplazo de cuerpo,
  sobrescritura de nota y envío a papelera.
- **Escritura atómica** (archivo temporal + `os.replace`): el vault nunca queda a medias.
- Logging estructurado **sin contenido de notas**.

## 7. Pruebas

Los tests corren sin red y sobre un vault temporal; no tocan tu vault real:

```bash
python3 -m pytest tests/ -q
```

## 8. Estructura

```
obsidian-manager/
├── SKILL.md              # Instrucciones para el agente
├── README.md             # Esta guía
├── scripts/
│   ├── obsidian_cli.py   # CLI con subcomandos
│   ├── vault.py          # Cliente del vault (notas, búsqueda, grafo, daily, tareas, proyectos, ingesta)
│   ├── frontmatter.py    # Frontmatter YAML mínimo (round-trip, sin dependencias)
│   ├── markdown_index.py # Wikilinks/tags y grafo (backlinks/huérfanas/rotos)
│   └── sources.py        # Orquestación de fuentes (invoca otros skills)
└── tests/                # Tests sobre vault temporal (sin red ni dependencias)
```

## Autores

- Hernan940504
