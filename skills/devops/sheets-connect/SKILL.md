---
name: sheets-connect
description: Lee y escribe Google Sheets (y hojas de cálculo Excel subidas a Drive) vía la API oficial, autenticando con una service account del proyecto GCP. Soporta impersonation (preferido, sin descargar llaves) o key JSON (fallback). Inspecciona el tipo de archivo con Drive API, lee rangos a JSON/CSV y escribe/actualiza celdas. Úsalo cuando el usuario quiera extraer datos de un Google Sheet compartido, volcar datos a una hoja, o conectar una hoja de cálculo por API de forma reutilizable.
version: 1.0.0
author: Hernan940504
category: devops
tags: [google-sheets, drive, gcp, service-account, impersonation, etl, datos, api]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Bash, Read, Write]
examples:
  - prompt: "lee los datos de este Google Sheet: <url>"
  - prompt: "extrae la hoja 'Ventas' del spreadsheet y pásala a CSV"
  - prompt: "escribe estos datos en el sheet compartido con la service account"
  - prompt: "qué pestañas tiene este spreadsheet"
  - prompt: "conéctate a Sheets con la service account de sandbox-arquitectura"
---

# Sheets Connect

Lee y escribe **Google Sheets** a través de la API oficial de Google, autenticando con una
**service account (SA)** del proyecto GCP. Es el equivalente "datos de hojas de cálculo" a los
skills `gcp-connect` (nube) y `langfuse-connect` (observabilidad): aquí la unidad de trabajo es
un **spreadsheet compartido con la SA**.

La capacidad es **reutilizable**: para cualquier archivo nuevo, basta con compartirlo (en Drive)
con el email de la SA y pasar su ID/URL al script.

## Cuándo usar este skill

- El usuario quiere **leer/extraer** datos de un Google Sheet compartido con su cuenta o con la SA.
- Quiere **escribir/actualizar** celdas o volcar datos a una hoja.
- Necesita **inspeccionar** un spreadsheet: pestañas (tabs), dimensiones, o el tipo real del
  archivo (Sheet nativo vs `.xlsx` subido a Drive).
- Quiere una forma **estable y reutilizable** de conectar hojas de cálculo por API, sin depender
  del client ID por defecto de gcloud (cuyos scopes de Sheets/Drive están siendo bloqueados).

## Cuándo NO usar

- Solo quieres **autenticar gcloud / renovar credenciales** de GCP → usa `gcp-connect`.
- El archivo **no está compartido** con la SA ni con una cuenta que la SA pueda impersonar
  (la API devolverá 403/404). Comparte primero el archivo en Drive.
- Quieres consultar **datos consolidados del Data Lake** → esos se consumen por GraphQL, no por
  Sheets.

## Autenticación: dos modos

La SA se llama, por convención de este repo, `sheets-connect@<project>.iam.gserviceaccount.com`.
El archivo (o carpeta) a leer/escribir **debe compartirse con ese email** desde Google Drive,
igual que se comparte con una persona (Lector para leer, Editor para escribir).

| Modo | Cómo | Cuándo |
|---|---|---|
| **Impersonation** | Tu usuario genera tokens en nombre de la SA. Requiere `roles/iam.serviceAccountTokenCreator` sobre la SA. **No descarga llaves.** | Cuando un admin te concedió tokenCreator sobre la SA y puedes compartir archivos con ella. |
| **Key JSON** | Se usa una llave de la SA vía `KEY_FILE`. Es un secreto de larga vida. | Cuando no puedes impersonar y sí puedes compartir archivos con la SA. |
| **User OAuth** | Usas **tu propia identidad** con un OAuth Client ID propio (Desktop). Lees/escribes lo que ya tienes compartido. | Cuando la **política de la organización impide compartir archivos con service accounts externas** (caso típico en Google Workspace corporativo). |

> **Importante (Workspace corporativo):** muchas organizaciones bloquean compartir archivos con
> dominios externos, y una SA (`*.iam.gserviceaccount.com`) es un dominio externo. En ese caso
> los modos con SA fallan al compartir; usa **User OAuth**, que actúa con tu propia cuenta.

> **Seguridad:** la key JSON nunca se guarda dentro del repo ni se commitea. Se referencia por
> ruta fuera de control de versiones (ej. `~/.config/gcloud/sheets-connect-sa@<project>.json`).
> El `.gitignore` del skill excluye `*.json` de credenciales. Migra a impersonation en cuanto un
> admin te dé `serviceAccountTokenCreator`.

## Requisitos previos

En el proyecto GCP deben estar habilitadas estas APIs (en `sandbox-arquitectura` ya lo están):

- `sheets.googleapis.com`
- `drive.googleapis.com`
- `iamcredentials.googleapis.com` (solo para el modo impersonation)

Y las librerías cliente en el venv del skill:

- `google-api-python-client`
- `google-auth`

## Workflow

### 1. Configurar el proyecto

Copia `proyectos/_ejemplo/config.env` a `proyectos/<tu-proyecto>/config.env` (o usa el ya creado
`proyectos/sandbox-arquitectura/`) y completa según el modo:

- `AUTH_MODE=impersonate|key` → fija `SA_EMAIL` y (si `key`) `KEY_FILE`.
- `AUTH_MODE=user-oauth` → fija `OAUTH_CLIENT_FILE` (client secret JSON de un OAuth Desktop
  client, fuera del repo). El token de usuario se cachea solo tras el primer login en
  `OAUTH_TOKEN_FILE` (por defecto `~/.config/gcloud/sheets-connect-user-token.json`).

Para crear el OAuth Desktop client: consola GCP → APIs y servicios → Credenciales →
Crear credenciales → ID de cliente de OAuth → tipo **Aplicación de escritorio** → Descargar JSON.

### 2. Probar conexión / inspeccionar un archivo

```bash
bash scripts/sheets.sh sandbox-arquitectura info <spreadsheet-id-o-url>
```

Muestra el tipo real (Sheet nativo vs `.xlsx`), el título y las pestañas.

### 3. Leer datos

```bash
# Toda una pestaña a JSON
bash scripts/sheets.sh sandbox-arquitectura read <id-o-url> --tab "Hoja1"
# Un rango en A1 a CSV
bash scripts/sheets.sh sandbox-arquitectura read <id-o-url> --range "Hoja1!A1:D50" --format csv
```

### 4. Escribir datos

```bash
# Escribir/actualizar un rango desde un JSON de filas
bash scripts/sheets.sh sandbox-arquitectura write <id-o-url> --range "Hoja1!A1" --values-json '[["a","b"],["1","2"]]'
# Agregar filas al final
bash scripts/sheets.sh sandbox-arquitectura append <id-o-url> --tab "Hoja1" --values-json '[["nueva","fila"]]'
```

## Recursos

- `scripts/sheets_io.py` — cliente Sheets/Drive (info/read/write/append; Sheets nativos + .xlsx). Requiere el venv.
- `scripts/sheets.sh` — wrapper que carga la config del proyecto, resuelve el venv y ejecuta.
- `proyectos/<x>/config.env` — SA_EMAIL, AUTH_MODE, KEY_FILE por proyecto.
- `proyectos/_ejemplo/config.env` — plantilla documentada.

## Notas sobre tipos de archivo

El skill soporta **dos tipos** de forma transparente (auto-detecta por `mimeType`):

- **Google Sheet nativo** → se lee/escribe con la **Sheets API** (soporta rangos A1 y `write`).
- **`.xlsx` subido a Drive** (`...spreadsheetml.sheet`) → se descarga vía **Drive API** y se procesa
  con **openpyxl**. Para `.xlsx`: `read` opera por **pestaña completa** (`--tab`), `append` agrega
  filas a una pestaña, y `write` por rango A1 **no** está soportado (convierte a Sheet nativo si lo
  necesitas: Archivo → Guardar como Google Sheets).

`info` indica en `source` qué ruta se usó (`sheets-api` o `xlsx-drive`) y lista las pestañas con
sus dimensiones en ambos casos.

## Anti-patrones

- **No commitear** llaves JSON de la SA ni `config.env` con rutas a secretos reales (el
  `.gitignore` ya excluye credenciales; solo se versiona `_ejemplo`).
- No usar el ADC del client ID por defecto de gcloud con scopes de Sheets/Drive: Google los está
  bloqueando; por eso este skill usa una SA.
- No compartir el spreadsheet como "cualquiera con el enlace" para evadir el compartir con la SA:
  comparte explícitamente con el email de la SA (least privilege).
- No pedir más scope del necesario: usa `drive.readonly`/`spreadsheets.readonly` cuando solo lees.
