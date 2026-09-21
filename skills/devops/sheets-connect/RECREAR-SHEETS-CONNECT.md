# Recrear la conexión a Google Sheets en otro repo/proyecto

Guía autocontenida para replicar la capacidad de **leer y escribir Google Sheets** (y `.xlsx`
subidos a Drive) vía la API oficial de Google. Sigue los pasos en orden: al final tendrás el
mismo cliente funcionando en cualquier proyecto.

## Qué hace

Un cliente por línea de comandos con cuatro operaciones:

| Comando | Qué hace |
|---|---|
| `info` | Detecta el tipo real del archivo (Sheet nativo vs `.xlsx`), título y pestañas. |
| `read` | Lee un rango A1 o una pestaña completa → salida JSON o CSV. |
| `write` | Sobrescribe un rango A1 con una matriz de valores (solo Sheets nativos). |
| `append` | Agrega filas al final de una pestaña (Sheets nativos y `.xlsx`). |

Autodetecta por `mimeType`: **Google Sheet nativo** → Sheets API; **`.xlsx` en Drive** → se
descarga con Drive API y se procesa con `openpyxl`.

## Modos de autenticación

| Modo | Cómo | Cuándo |
|---|---|---|
| `impersonate` | Tu usuario genera tokens en nombre de una service account (SA). Requiere `roles/iam.serviceAccountTokenCreator` sobre la SA. No descarga llaves. | Preferido: un admin te dio tokenCreator y puedes compartir archivos con la SA. |
| `key` | Llave JSON de la SA (secreto de larga vida) vía `KEY_FILE`. | No puedes impersonar pero sí compartir con la SA. |
| `user-oauth` | Tu propia identidad con un OAuth Client ID (Desktop) propio. | La política de la organización **impide compartir archivos con SAs externas** (Workspace corporativo típico). |

> El spreadsheet **debe compartirse** (Drive) con el email de la SA — Lector para leer, Editor
> para escribir. En modo `user-oauth` usas lo que tu cuenta ya tiene compartido.

## Estructura de archivos a crear

```
sheets-connect/
├── requirements.txt
├── .gitignore
├── scripts/
│   ├── sheets_io.py        # cliente Python (Sheets/Drive)
│   └── sheets.sh           # wrapper: carga config, resuelve venv, ejecuta
└── proyectos/
    ├── _ejemplo/config.env # plantilla (única versionada)
    └── <tu-proyecto>/config.env  # config real (NO versionar)
```

## Paso 1 — Requisitos en GCP

Habilita en el proyecto GCP:

- `sheets.googleapis.com`
- `drive.googleapis.com`
- `iamcredentials.googleapis.com` (solo para `impersonate`)

Crea la service account (convención: `sheets-connect@<project>.iam.gserviceaccount.com`) y, según
el modo:

- **impersonate:** concédete `roles/iam.serviceAccountTokenCreator` sobre la SA.
- **key:** genera una llave JSON y guárdala **fuera del repo**.
- **user-oauth:** consola GCP → APIs y servicios → Credenciales → Crear credenciales →
  ID de cliente OAuth → tipo **Aplicación de escritorio** → descarga el JSON (fuera del repo).

## Paso 2 — `requirements.txt`

Versiones pinneadas (regla de dependencias: sin rangos abiertos):

```
google-api-python-client==2.149.0
google-auth==2.35.0
google-auth-oauthlib==1.2.1
openpyxl==3.1.5
```

## Paso 3 — venv del skill

```bash
python3 -m venv ~/.config/gcloud/sheets-connect-venv
~/.config/gcloud/sheets-connect-venv/bin/pip install -r requirements.txt
```

El wrapper busca el intérprete en `~/.config/gcloud/sheets-connect-venv/bin/python` (override con
la variable de entorno `SHEETS_CONNECT_VENV`).

## Paso 4 — `.gitignore` (proteger secretos)

```
# Nunca versionar credenciales de service account
*.json
credentials/
# Config de proyectos reales (solo se versiona _ejemplo)
proyectos/*/config.env
!proyectos/_ejemplo/config.env
# venv local del skill (si se crea dentro)
.venv/
__pycache__/
```

## Paso 5 — `proyectos/_ejemplo/config.env` (plantilla)

```bash
# Plantilla de configuración por proyecto para sheets-connect.
# Copia esta carpeta a proyectos/<tu-proyecto>/ y completa los valores.

# Email de la service account que accede a los sheets.
# El o los spreadsheets deben compartirse con este email desde Google Drive.
SA_EMAIL=sheets-connect@<project-id>.iam.gserviceaccount.com

# Modo de autenticación: "impersonate", "key" o "user-oauth".
AUTH_MODE=key

# Solo para AUTH_MODE=key: ruta ABSOLUTA a la llave JSON, FUERA del repo.
KEY_FILE=

# Solo para AUTH_MODE=user-oauth: ruta al client secret JSON (OAuth Desktop), FUERA del repo.
OAUTH_CLIENT_FILE=

# Cache del token de usuario (se crea solo tras el primer login). FUERA del repo.
OAUTH_TOKEN_FILE=

# Proyecto GCP (para quota / referencia). Opcional.
PROJECT_ID=<project-id>
```

Luego, por cada proyecto real:

```bash
cp -r proyectos/_ejemplo proyectos/<tu-proyecto>
# edita proyectos/<tu-proyecto>/config.env con los valores reales
```

## Paso 6 — `scripts/sheets_io.py` (cliente)

```python
#!/usr/bin/env python3
"""Cliente de Google Sheets/Drive para el skill sheets-connect.

Autentica en tres modos:
  - key:         llave JSON de una service account (SA) vía --key-file.
  - impersonate: genera credenciales en nombre de una SA (sin descargar llaves).
  - user-oauth:  flujo OAuth con la identidad del usuario (client ID propio). Útil
                 cuando la política de la organización impide compartir con SAs
                 externas: el usuario lee/escribe lo que ya tiene compartido.

Comandos: info, read, write, append. Diseñado para salida estructurada (JSON/CSV)
consumible por un agente.
"""

import argparse
import csv
import io
import json
import os
import re
import sys
from typing import Any

import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
NATIVE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"

READONLY_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]
READWRITE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_SPREADSHEET_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9_-]+)")
_FILE_ID_RE = re.compile(r"/d/([a-zA-Z0-9_-]+)")


class SheetsError(Exception):
    """Error de negocio del skill; se reporta al cliente como mensaje genérico."""


def extract_spreadsheet_id(id_or_url: str) -> str:
    """Devuelve el ID de un spreadsheet a partir de un ID puro o una URL de Google."""
    value = id_or_url.strip()
    for pattern in (_SPREADSHEET_ID_RE, _FILE_ID_RE):
        match = pattern.search(value)
        if match:
            return match.group(1)
    if "/" not in value and value:
        return value
    raise SheetsError("No se pudo extraer el ID del spreadsheet de la entrada dada.")


def load_user_oauth_credentials(client_secret_file: str, token_file: str, scopes: list[str]):
    """Obtiene credenciales OAuth de usuario, cacheando el token entre ejecuciones."""
    from google_auth_oauthlib.flow import InstalledAppFlow  # import diferido: solo user-oauth

    credentials = None
    if token_file and os.path.exists(token_file):
        credentials = UserCredentials.from_authorized_user_file(token_file, scopes)

    if credentials and credentials.valid:
        return credentials

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    else:
        if not client_secret_file or not os.path.exists(client_secret_file):
            raise SheetsError(
                "AUTH_MODE=user-oauth requiere OAUTH_CLIENT_FILE (client secret JSON) existente."
            )
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
        credentials = flow.run_local_server(port=0)

    if token_file:
        with open(token_file, "w", encoding="utf-8") as handle:
            handle.write(credentials.to_json())
        os.chmod(token_file, 0o600)
    return credentials


def build_credentials(
    auth_mode: str,
    sa_email: str,
    key_file: str,
    writable: bool,
    client_secret_file: str = "",
    token_file: str = "",
):
    """Construye credenciales según el modo de autenticación."""
    scopes = READWRITE_SCOPES if writable else READONLY_SCOPES

    if auth_mode == "key":
        if not key_file:
            raise SheetsError("AUTH_MODE=key requiere KEY_FILE con la ruta a la llave JSON.")
        return service_account.Credentials.from_service_account_file(key_file, scopes=scopes)

    if auth_mode == "impersonate":
        if not sa_email:
            raise SheetsError("AUTH_MODE=impersonate requiere SA_EMAIL.")
        source_credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=sa_email,
            target_scopes=scopes,
            lifetime=600,
        )

    if auth_mode == "user-oauth":
        return load_user_oauth_credentials(client_secret_file, token_file, scopes)

    raise SheetsError(
        f"AUTH_MODE desconocido: {auth_mode!r} (usa 'key', 'impersonate' o 'user-oauth')."
    )


def get_services(credentials):
    """Crea los clientes de Sheets y Drive con las credenciales dadas."""
    sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    return sheets, drive


def get_file_mime(drive, file_id: str) -> tuple[str, str]:
    """Devuelve (nombre, mimeType) de un archivo de Drive."""
    meta = (
        drive.files()
        .get(fileId=file_id, fields="name,mimeType", supportsAllDrives=True)
        .execute()
    )
    return meta.get("name", ""), meta.get("mimeType", "")


def download_xlsx(drive, file_id: str):
    """Descarga los bytes de un .xlsx subido a Drive y devuelve un workbook openpyxl."""
    from openpyxl import load_workbook  # import diferido: solo ruta .xlsx

    request = drive.files().get_media(fileId=file_id, supportsAllDrives=True)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    return load_workbook(buffer, data_only=True)


def cmd_info(sheets, drive, spreadsheet_id: str) -> dict[str, Any]:
    """Devuelve tipo real del archivo (Drive), título y pestañas del spreadsheet."""
    name, mime_type = get_file_mime(drive, spreadsheet_id)
    result: dict[str, Any] = {
        "id": spreadsheet_id,
        "name": name,
        "mime_type": mime_type,
        "is_native_sheet": mime_type == NATIVE_SHEET_MIME,
    }

    if mime_type == NATIVE_SHEET_MIME:
        meta = (
            sheets.spreadsheets()
            .get(spreadsheetId=spreadsheet_id, fields="sheets(properties(title,gridProperties))")
            .execute()
        )
        result["source"] = "sheets-api"
        result["tabs"] = [
            {
                "title": s["properties"]["title"],
                "rows": s["properties"].get("gridProperties", {}).get("rowCount"),
                "cols": s["properties"].get("gridProperties", {}).get("columnCount"),
            }
            for s in meta.get("sheets", [])
        ]
        return result

    if mime_type == XLSX_MIME:
        workbook = download_xlsx(drive, spreadsheet_id)
        result["source"] = "xlsx-drive"
        result["tabs"] = [
            {"title": ws.title, "rows": ws.max_row, "cols": ws.max_column}
            for ws in workbook.worksheets
        ]
        return result

    result["note"] = (
        f"Tipo de archivo no soportado para lectura tabular: {mime_type}. "
        "Se soportan Google Sheets nativos y .xlsx."
    )
    return result


def read_xlsx_range(drive, file_id: str, tab: str | None) -> list[list[Any]]:
    """Lee una pestaña completa de un .xlsx de Drive como matriz de valores."""
    workbook = download_xlsx(drive, file_id)
    worksheet = workbook[tab] if tab else workbook.worksheets[0]
    rows: list[list[Any]] = []
    for row in worksheet.iter_rows(values_only=True):
        rows.append(["" if cell is None else cell for cell in row])
    return rows


def cmd_read(sheets, drive, spreadsheet_id: str, a1_range: str, tab: str | None) -> list[list[Any]]:
    """Lee valores; usa Sheets API si es nativo o openpyxl si es .xlsx de Drive."""
    _, mime_type = get_file_mime(drive, spreadsheet_id)
    if mime_type == XLSX_MIME:
        return read_xlsx_range(drive, spreadsheet_id, tab)
    resp = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=a1_range)
        .execute()
    )
    return resp.get("values", [])


def cmd_write(sheets, spreadsheet_id: str, a1_range: str, values: list[list[Any]]) -> dict[str, Any]:
    """Escribe (sobrescribe) valores en un rango. Devuelve celdas actualizadas."""
    resp = (
        sheets.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=a1_range,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        )
        .execute()
    )
    return {"updated_range": resp.get("updatedRange"), "updated_cells": resp.get("updatedCells")}


def cmd_append(sheets, spreadsheet_id: str, a1_range: str, values: list[list[Any]]) -> dict[str, Any]:
    """Agrega filas al final de la tabla que contiene el rango dado."""
    resp = (
        sheets.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=a1_range,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        )
        .execute()
    )
    updates = resp.get("updates", {})
    return {"updated_range": updates.get("updatedRange"), "updated_cells": updates.get("updatedCells")}


def upload_xlsx(drive, file_id: str, workbook) -> None:
    """Sube (reemplaza) el contenido de un .xlsx en Drive desde un workbook openpyxl."""
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    media = MediaIoBaseUpload(buffer, mimetype=XLSX_MIME, resumable=False)
    drive.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()


def append_xlsx(drive, file_id: str, tab: str | None, values: list[list[Any]]) -> dict[str, Any]:
    """Agrega filas al final de una pestaña de un .xlsx de Drive y lo vuelve a subir."""
    workbook = download_xlsx(drive, file_id)
    worksheet = workbook[tab] if tab else workbook.worksheets[0]
    start_row = worksheet.max_row + 1
    for row in values:
        worksheet.append(row)
    upload_xlsx(drive, file_id, workbook)
    return {
        "source": "xlsx-drive",
        "tab": worksheet.title,
        "appended_rows": len(values),
        "first_new_row": start_row,
    }


def rows_to_csv(rows: list[list[Any]]) -> str:
    """Serializa una matriz de valores a texto CSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    return buffer.getvalue()


def parse_values_json(raw: str) -> list[list[Any]]:
    """Parsea y valida el JSON de valores para write/append (matriz de filas)."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SheetsError(f"--values-json no es JSON válido: {exc}") from exc
    if not isinstance(data, list) or not all(isinstance(row, list) for row in data):
        raise SheetsError("--values-json debe ser una lista de listas (matriz de filas).")
    return data


def resolve_range(tab: str | None, a1_range: str | None) -> str:
    """Determina el rango A1 efectivo a partir de --tab o --range."""
    if a1_range:
        return a1_range
    if tab:
        return tab
    raise SheetsError("Debes indicar --tab o --range.")


def build_arg_parser() -> argparse.ArgumentParser:
    """Configura los argumentos de línea de comandos del cliente."""
    parser = argparse.ArgumentParser(description="Cliente Google Sheets/Drive (skill sheets-connect).")
    parser.add_argument("command", choices=["info", "read", "write", "append"])
    parser.add_argument("target", help="ID o URL del spreadsheet.")
    parser.add_argument("--auth-mode", default="key", choices=["key", "impersonate", "user-oauth"])
    parser.add_argument("--sa-email", default="")
    parser.add_argument("--key-file", default="")
    parser.add_argument("--oauth-client-file", default="", help="Client secret JSON (user-oauth).")
    parser.add_argument("--oauth-token-file", default="", help="Ruta de cache del token de usuario.")
    parser.add_argument("--tab", default=None, help="Nombre de la pestaña (para leer/append de toda la hoja).")
    parser.add_argument("--range", dest="a1_range", default=None, help="Rango en notación A1 (ej. Hoja1!A1:D50).")
    parser.add_argument("--format", default="json", choices=["json", "csv"], help="Formato de salida para read.")
    parser.add_argument("--values-json", default=None, help="Matriz JSON de filas para write/append.")
    return parser


def run(args: argparse.Namespace) -> int:
    """Ejecuta el comando solicitado y escribe el resultado en stdout."""
    writable = args.command in {"write", "append"}
    credentials = build_credentials(
        args.auth_mode,
        args.sa_email,
        args.key_file,
        writable,
        client_secret_file=args.oauth_client_file,
        token_file=args.oauth_token_file,
    )
    sheets, drive = get_services(credentials)
    spreadsheet_id = extract_spreadsheet_id(args.target)

    if args.command == "info":
        print(json.dumps(cmd_info(sheets, drive, spreadsheet_id), ensure_ascii=False, indent=2))
        return 0

    if args.command == "read":
        a1_range = args.a1_range or args.tab or "A:ZZ"
        rows = cmd_read(sheets, drive, spreadsheet_id, a1_range, args.tab)
        if args.format == "csv":
            sys.stdout.write(rows_to_csv(rows))
        else:
            print(json.dumps({"row_count": len(rows), "values": rows}, ensure_ascii=False, indent=2))
        return 0

    if args.command in {"write", "append"}:
        if args.values_json is None:
            raise SheetsError(f"{args.command} requiere --values-json.")
        values = parse_values_json(args.values_json)
        _, mime_type = get_file_mime(drive, spreadsheet_id)

        if mime_type == XLSX_MIME:
            if args.command == "write":
                raise SheetsError(
                    "write por rango A1 no está soportado en archivos .xlsx. "
                    "Usa 'append' (agrega filas a una pestaña) o convierte el archivo a Google Sheet nativo."
                )
            print(json.dumps(append_xlsx(drive, spreadsheet_id, args.tab, values), ensure_ascii=False, indent=2))
            return 0

        a1_range = resolve_range(args.tab, args.a1_range)
        handler = cmd_write if args.command == "write" else cmd_append
        print(json.dumps(handler(sheets, spreadsheet_id, a1_range, values), ensure_ascii=False, indent=2))
        return 0

    return 1


def main() -> int:
    """Punto de entrada: parsea args y traduce errores a mensajes claros."""
    args = build_arg_parser().parse_args()
    try:
        return run(args)
    except SheetsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except HttpError as exc:
        status = getattr(exc, "status_code", None) or getattr(exc.resp, "status", "?")
        print(
            f"Error de la API de Google (HTTP {status}). "
            "Verifica que tu cuenta (o la service account) tenga acceso al archivo y que el rango/pestaña exista.",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    sys.exit(main())
```

## Paso 7 — `scripts/sheets.sh` (wrapper)

```bash
#!/bin/bash
# sheets.sh — Lee/escribe Google Sheets vía service account (skill sheets-connect).
#
# Uso:
#   sheets.sh <proyecto> info   <id-o-url>
#   sheets.sh <proyecto> read   <id-o-url> [--tab NOMBRE | --range A1] [--format json|csv]
#   sheets.sh <proyecto> write  <id-o-url> --range A1 --values-json '[["a","b"]]'
#   sheets.sh <proyecto> append <id-o-url> (--tab NOMBRE | --range A1) --values-json '[["a"]]'

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROYECTOS_DIR="$SKILL_DIR/proyectos"

# venv del skill (con las librerías cliente de Google).
VENV_PY="${SHEETS_CONNECT_VENV:-$HOME/.config/gcloud/sheets-connect-venv}/bin/python"

usage() {
  echo "Uso: sheets.sh <proyecto> <info|read|write|append> <id-o-url> [opciones]"
  echo ""
  echo "Proyectos configurados en proyectos/:"
  local found=0
  for d in "$PROYECTOS_DIR"/*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    case "$name" in _*) continue ;; esac
    echo "  $name"
    found=1
  done
  [ "$found" -eq 0 ] && echo "  (ninguno; copia proyectos/_ejemplo a proyectos/<nombre>)"
  exit 1
}

[ "$#" -lt 3 ] && usage

PROJECT_NAME="$1"; shift
COMMAND="$1"; shift
TARGET="$1"; shift

CONFIG_FILE="$PROYECTOS_DIR/$PROJECT_NAME/config.env"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: no existe $CONFIG_FILE"
  echo "Copia proyectos/_ejemplo/config.env a proyectos/$PROJECT_NAME/config.env y complétalo."
  exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG_FILE"

AUTH_MODE="${AUTH_MODE:-key}"
SA_EMAIL="${SA_EMAIL:-}"
KEY_FILE="${KEY_FILE:-}"
OAUTH_CLIENT_FILE="${OAUTH_CLIENT_FILE:-}"
OAUTH_TOKEN_FILE="${OAUTH_TOKEN_FILE:-$HOME/.config/gcloud/sheets-connect-user-token.json}"

if [ ! -x "$VENV_PY" ]; then
  echo "Error: no se encontró el intérprete del venv en $VENV_PY"
  echo "Créalo con: python3 -m venv ~/.config/gcloud/sheets-connect-venv"
  echo "  y luego: ~/.config/gcloud/sheets-connect-venv/bin/pip install -r $SKILL_DIR/requirements.txt"
  exit 1
fi

if [ "$AUTH_MODE" = "key" ] && { [ -z "$KEY_FILE" ] || [ ! -f "$KEY_FILE" ]; }; then
  echo "Error: AUTH_MODE=key pero KEY_FILE no existe: '${KEY_FILE:-<vacío>}'"
  exit 1
fi

if [ "$AUTH_MODE" = "user-oauth" ] && { [ -z "$OAUTH_CLIENT_FILE" ] || [ ! -f "$OAUTH_CLIENT_FILE" ]; }; then
  echo "Error: AUTH_MODE=user-oauth pero OAUTH_CLIENT_FILE no existe: '${OAUTH_CLIENT_FILE:-<vacío>}'"
  echo "Descarga el client secret JSON (OAuth Desktop) y pon su ruta en OAUTH_CLIENT_FILE."
  exit 1
fi

exec "$VENV_PY" "$SCRIPT_DIR/sheets_io.py" \
  "$COMMAND" "$TARGET" \
  --auth-mode "$AUTH_MODE" \
  --sa-email "$SA_EMAIL" \
  --key-file "$KEY_FILE" \
  --oauth-client-file "$OAUTH_CLIENT_FILE" \
  --oauth-token-file "$OAUTH_TOKEN_FILE" \
  "$@"
```

Dale permisos de ejecución:

```bash
chmod +x scripts/sheets.sh
```

## Paso 8 — Compartir el spreadsheet

En Google Drive, comparte el archivo con el email de la SA (`SA_EMAIL`):

- **Lector** para `info`/`read`.
- **Editor** para `write`/`append`.

En modo `user-oauth`, basta con que tu propia cuenta tenga acceso al archivo.

## Uso

```bash
# Inspeccionar: tipo real, título y pestañas
bash scripts/sheets.sh <tu-proyecto> info <spreadsheet-id-o-url>

# Leer una pestaña completa a JSON
bash scripts/sheets.sh <tu-proyecto> read <id-o-url> --tab "Hoja1"

# Leer un rango A1 a CSV
bash scripts/sheets.sh <tu-proyecto> read <id-o-url> --range "Hoja1!A1:D50" --format csv

# Escribir/actualizar un rango (solo Sheets nativos)
bash scripts/sheets.sh <tu-proyecto> write <id-o-url> --range "Hoja1!A1" --values-json '[["a","b"],["1","2"]]'

# Agregar filas al final de una pestaña
bash scripts/sheets.sh <tu-proyecto> append <id-o-url> --tab "Hoja1" --values-json '[["nueva","fila"]]'
```

## Tipos de archivo

- **Google Sheet nativo** → Sheets API. Soporta rangos A1 y `write`.
- **`.xlsx` subido a Drive** → se descarga con Drive API y se procesa con `openpyxl`.
  `read` opera por **pestaña completa** (`--tab`); `append` agrega filas; `write` por rango A1
  **no** está soportado (convierte a Sheet nativo: Archivo → Guardar como Google Sheets).

`info` reporta en `source` la ruta usada (`sheets-api` o `xlsx-drive`).

## Seguridad y anti-patrones

- **No commitear** llaves JSON de la SA ni `config.env` con rutas a secretos reales (el
  `.gitignore` ya los excluye; solo se versiona `_ejemplo`).
- No usar el ADC del client ID por defecto de gcloud con scopes de Sheets/Drive: Google los está
  bloqueando; por eso se usa una SA propia.
- No compartir el spreadsheet como "cualquiera con el enlace" para evadir compartir con la SA:
  compártelo explícitamente con el email de la SA (least privilege).
- Pide solo el scope necesario: `*.readonly` cuando solo lees (el cliente ya lo hace según el
  comando).
- La key JSON es un secreto de larga vida: migra a `impersonate` en cuanto un admin te dé
  `serviceAccountTokenCreator`.

## Solución de problemas

| Síntoma | Causa probable | Acción |
|---|---|---|
| `HTTP 403 / 404` | El archivo no está compartido con la SA/tu cuenta, o el ID es incorrecto. | Comparte el archivo con `SA_EMAIL`; verifica el ID/URL. |
| `no se encontró el intérprete del venv` | Falta crear el venv o la ruta difiere. | Crea el venv (Paso 3) o exporta `SHEETS_CONNECT_VENV`. |
| `AUTH_MODE=key pero KEY_FILE no existe` | Ruta a la llave vacía o incorrecta. | Ajusta `KEY_FILE` a la ruta absoluta de la llave (fuera del repo). |
| `write ... no está soportado en archivos .xlsx` | El archivo es `.xlsx`, no Sheet nativo. | Usa `append` o convierte a Google Sheet nativo. |
| Scopes de Sheets/Drive bloqueados con gcloud ADC | Uso del client ID por defecto. | Usa la SA (`key`/`impersonate`) o `user-oauth` con client propio. |
