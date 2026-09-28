---
name: google-drive-manager
description: Descarga, sube, actualiza y organiza archivos en Google Drive (Mi unidad y
  unidades compartidas) vía un CLI Python sobre la Drive API v3. Exporta Google
  Docs/Sheets/Slides a docx/xlsx/pptx/pdf/csv/md, sube archivos grandes con resumable,
  mueve/renombra/copia y envía a papelera con confirmación. Úsalo cuando el usuario diga
  "sube este archivo a Drive", "descarga la carpeta X de la unidad compartida Y", "exporta
  este Doc como PDF", "organiza/mueve en Drive" o "lista mis unidades compartidas".
version: 1.0.0
author: Hernan940504
category: workspace
tags: [google-drive, google-workspace, oauth2, shared-drives, upload, download, cli, python]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Bash]
examples:
  - prompt: "sube este archivo a la carpeta Contratos de Drive"
  - prompt: "descarga la carpeta Contratos de la unidad compartida Legal como PDF"
  - prompt: "exporta este Google Doc como docx"
  - prompt: "mueve todos los PDF de la carpeta X a X/PDF"
  - prompt: "renombra este archivo en Drive"
  - prompt: "lista las unidades compartidas a las que tengo acceso"
  - prompt: "busca en mi Drive los archivos modificados después de enero"
---

# google-drive-manager — Operar Google Drive (Mi unidad + Shared Drives)

## Cuándo usar este skill

- El usuario pide subir, descargar, exportar, actualizar o reorganizar archivos en Google Drive.
- Menciona unidades compartidas (Shared Drives), "Mi unidad", carpetas por nombre o rutas legibles.
- Pide exportar Google Docs/Sheets/Slides a un formato ofimático (docx/xlsx/pptx/pdf/csv/md).
- Pide listar sus unidades compartidas o buscar archivos por nombre, tipo, fecha o propietario.

## Cuándo NO usar

- Operaciones que no son de archivos (Gmail, Calendar, Docs API de edición de contenido).
- Borrado permanente o vaciar la papelera: **no está soportado a propósito** (solo `trash`/`restore`).
- Compartir/permisos (ACL) o gestión de miembros de una Shared Drive: fuera de alcance de este skill.

## Requisitos previos

- Python 3.12+ y dependencias instaladas: `pip install -r requirements.txt` (ver README).
- Credenciales OAuth configuradas. Rutas por variables de entorno, fuera del repo:
  - `GDRIVE_CREDENTIALS_PATH` (default `~/.config/gdrive-skill/credentials.json`)
  - `GDRIVE_TOKEN_PATH` (default `~/.config/gdrive-skill/token.json`)
  - `GDRIVE_SCOPES` (default `https://www.googleapis.com/auth/drive`)
- Primer uso: ejecutar `auth` una vez para el login OAuth. El setup completo está en `README.md`.

## Cómo ejecutar y parsear la salida

Todos los comandos se ejecutan con el CLI y **devuelven JSON en stdout**:

```bash
python3 skills/workspace/google-drive-manager/scripts/drive_cli.py <comando> [opciones]
```

- Parsea stdout como JSON. En caso de error, el JSON `{"error": {"type", "message"}}` va a **stderr**
  y el **código de salida** es distinto de cero.
- Los flags globales (`--pretty`, `--dry-run`, `--yes`, `--log-level`) se aceptan **antes o después**
  del subcomando indistintamente.
- Añade `--pretty` solo si vas a mostrar el resultado al usuario; para uso programático deja el JSON compacto.
- `search` devuelve hasta **200 resultados por defecto** y marca `"truncated": true` si hay más; usa
  `--limit N` para ajustar o `--all` para traer todo (puede ser lento en Drives grandes).
- Códigos de salida: `0` ok · `2` uso · `3` permisos · `4` no encontrado · `5` cuota · `6` conflicto · `7` auth requerida.
- Si el código es `7`, ejecuta `auth` y reintenta. Si es `3`, informa al usuario que no tiene permisos sobre el recurso.

## Reglas de seguridad y confirmación (OBLIGATORIAS)

- **Confirma con el usuario ANTES** de ejecutar operaciones destructivas o masivas:
  - `organize trash` (enviar a papelera).
  - `update --content` (reemplaza el contenido de un archivo).
  - `upload` con `--on-conflict replace|version` (sobrescribe/versiona un existente).
  - `move`/`rename` de más de 10 archivos (regla por lote).
- El CLI **rechaza** estas operaciones si no pasas `--yes` (devuelve código 6). Para previsualizar sin ejecutar, usa `--dry-run`.
- Flujo recomendado del agente: primero corre el comando con `--dry-run`, muestra el plan al usuario, y solo tras su confirmación explícita repite con `--yes`.
- Nunca imprimas ni registres tokens ni contenido de archivos. No hay borrado permanente disponible.

## Workflow por subcomando

### Autenticar (una vez)
```bash
python3 scripts/drive_cli.py auth
```

### Listar unidades compartidas
```bash
python3 scripts/drive_cli.py drives
# -> {"drives": [{"id": "...", "name": "Legal"}, ...]}
```
Usa el `id` devuelto para acotar búsquedas y resolver rutas dentro de esa unidad.

### Buscar / listar
```bash
python3 scripts/drive_cli.py search --scope all --name-contains "informe" --mime-type application/pdf
python3 scripts/drive_cli.py search --drive <DRIVE_ID> --parent <FOLDER_ID>
python3 scripts/drive_cli.py search --scope mydrive --modified-after 2026-01-01T00:00:00
```
`--scope` es `all` (default) o `mydrive`. `--drive <id>` acota a una Shared Drive concreta.

### Descargar / exportar
```bash
# Binario o Google (auto-detecta). --export elige formato para tipos Google.
python3 scripts/drive_cli.py download <FILE_ID> ./destino --export pdf
# Carpeta completa conservando estructura
python3 scripts/drive_cli.py download <FOLDER_ID> ./salida --recursive --export pdf
```
Para "descarga la carpeta Contratos de la unidad compartida Legal como PDF":
1. `drives` → localizar el `id` de "Legal".
2. Resolver la ruta "Contratos" a un `FOLDER_ID` (usa `search --drive <id> --name Contratos`).
3. `download <FOLDER_ID> ./Contratos --recursive --export pdf`.

### Subir
```bash
python3 scripts/drive_cli.py upload ./archivo.pdf <PARENT_ID>
python3 scripts/drive_cli.py upload ./hoja.csv <PARENT_ID> --convert          # a Google Sheet
python3 scripts/drive_cli.py upload ./doc.docx <PARENT_ID> --on-conflict version
```
Elige subida simple/resumable automáticamente por tamaño (umbral 5 MB). Si hay conflicto de
nombre y no pasas `--on-conflict`, devuelve código 6: pregunta al usuario `new`/`replace`/`version`.

### Actualizar
```bash
# Reemplazo de contenido (destructivo -> requiere --yes)
python3 scripts/drive_cli.py --yes update <FILE_ID> --content ./nueva-version.pdf
# Metadatos (no destructivo)
python3 scripts/drive_cli.py update <FILE_ID> --name "Nuevo nombre" --description "..."
```

### Organizar
```bash
python3 scripts/drive_cli.py organize mkdir "Proyectos/2026/Q3" --root <PARENT_ID>
python3 scripts/drive_cli.py organize move <FILE_ID> <DEST_FOLDER_ID>
python3 scripts/drive_cli.py organize rename <FILE_ID> "nuevo-nombre.pdf"
python3 scripts/drive_cli.py organize copy <FILE_ID> --name "copia.pdf" --parent <DEST_ID>
python3 scripts/drive_cli.py --yes organize trash <FILE_ID>     # destructivo
python3 scripts/drive_cli.py organize restore <FILE_ID>
```

### Regla por lote (ej.: mover todos los PDF de X a X/PDF)
1. `search --parent <X_ID> --mime-type application/pdf` → obtener la lista de ids.
2. Si son más de 10, confirma con el usuario (o corre cada `move` con `--dry-run` primero).
3. `organize mkdir "PDF" --root <X_ID>` para asegurar el destino.
4. Un `organize move <FILE_ID> <PDF_FOLDER_ID>` por cada archivo.

## Anti-patrones

- No ejecutar `trash`, `update --content` o `replace` sin confirmación del usuario.
- No asumir el `id` de una Shared Drive: resuélvelo con `drives` primero.
- No elegir arbitrariamente ante rutas con nombres duplicados: el CLI devuelve código 4 con candidatos; pide desambiguar.
- No imprimir tokens ni contenido de archivos en la conversación.
- No intentar borrado permanente: no existe en este skill por diseño.

## Recursos

- `scripts/drive_cli.py` — CLI con subcomandos (punto de entrada del agente).
- `scripts/drive_client.py` — wrapper de la Drive API (paginación, reintentos, operaciones).
- `scripts/auth.py` — credenciales/token OAuth y scopes.
- `scripts/mime_map.py` — mapeo de export/conversión de tipos Google.
- `README.md` — setup GCP/OAuth paso a paso y ejemplos por subcomando.
- `requirements.txt` — dependencias pinneadas (instalar desde el mirror JFrog).
