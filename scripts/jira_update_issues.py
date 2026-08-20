"""
Script para buscar worklogs en el issue TASD-1 de Jira que contengan
"[TASD-1](VIP)Incapacidad" en su descripción (comment), y actualizar
la referencia de TASD-1 a TASD-4.

Solo procesa worklogs creados desde el 1 de mayo de 2026.

Uso:
    export JIRA_DOMAIN="jirasegurosbolivar.atlassian.net"
    export JIRA_USERNAME="tu_usuario@segurosbolivar.com"
    export JIRA_API_TOKEN="tu_token_aqui"
    python scripts/jira_update_issues.py
"""

import copy
import os
import re
import sys
from base64 import b64encode
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json


def load_env_from_zshrc() -> None:
    """Lee variables de entorno exportadas en ~/.zshrc como fallback.

    Busca líneas con formato: export VARIABLE="valor" o export VARIABLE='valor'
    y las carga en os.environ si no están ya definidas.
    """
    zshrc_path = Path.home() / ".zshrc"
    if not zshrc_path.exists():
        return

    content = zshrc_path.read_text(encoding="utf-8")
    pattern = re.compile(r'^export\s+(\w+)=["\']?([^"\'\n]+)["\']?', re.MULTILINE)

    for match in pattern.finditer(content):
        key, value = match.group(1), match.group(2)
        if key not in os.environ:
            os.environ[key] = value


# Cargar variables desde ~/.zshrc si no están en el entorno
load_env_from_zshrc()

# --- Configuración desde variables de entorno ---

JIRA_DOMAIN = os.environ.get("JIRA_DOMAIN")
JIRA_USERNAME = os.environ.get("JIRA_USERNAME")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")

SEARCH_TEXT = "Incapacidad"
REPLACEMENT_TEXT = "[TASD-4](VIP)Incapacidad"
SOURCE_ISSUE_KEY = "TASD-1"
DATE_FROM = datetime(2026, 5, 1, tzinfo=timezone.utc)


def validate_environment() -> None:
    """Valida que las variables de entorno requeridas estén configuradas."""
    missing = []
    if not JIRA_DOMAIN:
        missing.append("JIRA_DOMAIN")
    if not JIRA_USERNAME:
        missing.append("JIRA_USERNAME")
    if not JIRA_API_TOKEN:
        missing.append("JIRA_API_TOKEN")

    if missing:
        print(f"Error: Variables de entorno faltantes: {', '.join(missing)}")
        print("\nConfigura las variables así:")
        print('  export JIRA_DOMAIN="jirasegurosbolivar.atlassian.net"')
        print('  export JIRA_USERNAME="tu_usuario@segurosbolivar.com"')
        print('  export JIRA_API_TOKEN="tu_token_aqui"')
        sys.exit(1)


def get_auth_header() -> str:
    """Genera el header de autenticación Basic Auth."""
    credentials = f"{JIRA_USERNAME}:{JIRA_API_TOKEN}"
    encoded = b64encode(credentials.encode("utf-8")).decode("utf-8")
    return f"Basic {encoded}"


def make_request(url: str, method: str = "GET", data: dict | None = None) -> dict:
    """Realiza una petición HTTP a la API de Jira.

    Args:
        url: URL completa del endpoint.
        method: Método HTTP (GET, PUT, POST).
        data: Payload JSON para enviar en el body.

    Returns:
        Respuesta parseada como diccionario.

    Raises:
        HTTPError: Si la API responde con error.
        URLError: Si hay problemas de conexión.
    """
    headers = {
        "Authorization": get_auth_header(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    body = json.dumps(data).encode("utf-8") if data else None
    request = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8")
            if response_body:
                return json.loads(response_body)
            return {}
    except HTTPError as error:
        error_body = error.read().decode("utf-8")
        print(f"Error HTTP {error.code}: {error_body}")
        raise
    except URLError as error:
        print(f"Error de conexión: {error.reason}")
        raise


def extract_text_from_adf(adf_node: dict | str | None) -> str:
    """Extrae texto plano de un nodo ADF (Atlassian Document Format).

    Args:
        adf_node: Nodo ADF o texto plano.

    Returns:
        Texto plano extraído.
    """
    if adf_node is None:
        return ""
    if isinstance(adf_node, str):
        return adf_node

    text_parts = []

    if adf_node.get("type") == "text":
        text_parts.append(adf_node.get("text", ""))

    for child in adf_node.get("content", []):
        text_parts.append(extract_text_from_adf(child))

    return "".join(text_parts)


def replace_text_in_adf(adf_node: dict, old: str, new: str) -> dict:
    """Reemplaza texto dentro de un nodo ADF recursivamente.

    Args:
        adf_node: Nodo ADF a modificar.
        old: Texto a buscar.
        new: Texto de reemplazo.

    Returns:
        Nodo ADF con el texto reemplazado.
    """
    node = copy.deepcopy(adf_node)

    if node.get("type") == "text" and "text" in node:
        node["text"] = node["text"].replace(old, new)

    if "content" in node:
        node["content"] = [replace_text_in_adf(child, old, new) for child in node["content"]]

    return node


def parse_jira_datetime(date_str: str) -> datetime:
    """Parsea un datetime de Jira a objeto datetime.

    Args:
        date_str: Fecha en formato ISO de Jira (e.g. "2026-05-13T08:00:00.000+0000").

    Returns:
        Objeto datetime con timezone.
    """
    # Jira puede devolver formatos como "2026-05-13T08:00:00.000+0000"
    # Normalizar el offset: +0000 → +00:00
    if re.search(r'[+-]\d{4}$', date_str):
        date_str = date_str[:-2] + ":" + date_str[-2:]
    return datetime.fromisoformat(date_str)


def get_worklogs(issue_key: str) -> list[dict]:
    """Obtiene todos los worklogs de un issue.

    Args:
        issue_key: Key del issue (e.g. "TASD-1").

    Returns:
        Lista de worklogs.
    """
    url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/worklog"
    print(f"Obteniendo worklogs de {issue_key}...")

    all_worklogs = []
    start_at = 0
    max_results = 100

    while True:
        paginated_url = f"{url}?startAt={start_at}&maxResults={max_results}"
        result = make_request(paginated_url)

        worklogs = result.get("worklogs", [])
        all_worklogs.extend(worklogs)

        total = result.get("total", 0)
        start_at += max_results

        if start_at >= total:
            break

    print(f"  Total de worklogs encontrados: {len(all_worklogs)}")
    return all_worklogs


def filter_worklogs(worklogs: list[dict], debug: bool = False) -> list[dict]:
    """Filtra worklogs que contengan el texto buscado y sean desde la fecha indicada.

    Args:
        worklogs: Lista de worklogs del issue.
        debug: Si True, imprime los primeros worklogs recientes para diagnóstico.

    Returns:
        Worklogs que cumplen los criterios.
    """
    matching = []
    recent_worklogs = []

    for worklog in worklogs:
        # Filtrar por fecha (started >= 2026-05-01)
        started = worklog.get("started", "")
        if started:
            worklog_date = parse_jira_datetime(started)
            if worklog_date < DATE_FROM:
                continue

        # Guardar para debug
        comment = worklog.get("comment")
        comment_text = extract_text_from_adf(comment)

        if debug and len(recent_worklogs) < 5:
            recent_worklogs.append({
                "id": worklog.get("id"),
                "started": started[:10],
                "comment_text": comment_text[:100] if comment_text else "(vacío)",
                "comment_type": type(comment).__name__,
                "comment_raw_keys": list(comment.keys()) if isinstance(comment, dict) else None,
            })

        if SEARCH_TEXT in comment_text:
            worklog_id = worklog.get("id")
            author = worklog.get("author", {}).get("displayName", "desconocido")
            time_spent = worklog.get("timeSpent", "?")
            print(f"  ✓ Worklog {worklog_id} | Fecha: {started[:10]} | {time_spent} | {author} | \"{comment_text[:80]}\"")
            matching.append(worklog)

    if debug and recent_worklogs:
        print("\n  [DEBUG] Primeros 5 worklogs desde mayo 2026:")
        for wl in recent_worklogs:
            print(f"    ID: {wl['id']} | Fecha: {wl['started']} | Tipo comment: {wl['comment_type']}")
            print(f"    Texto: \"{wl['comment_text']}\"")
            if wl['comment_raw_keys']:
                print(f"    Keys ADF: {wl['comment_raw_keys']}")
            print()

    print(f"\n  {len(matching)} worklogs contienen '{SEARCH_TEXT}' desde {DATE_FROM.strftime('%Y-%m-%d')}")
    return matching


def update_worklog(issue_key: str, worklog: dict) -> bool:
    """Actualiza el comment de un worklog reemplazando TASD-1 por TASD-4.

    Args:
        issue_key: Key del issue al que pertenece el worklog.
        worklog: Diccionario del worklog a actualizar.

    Returns:
        True si la actualización fue exitosa.
    """
    worklog_id = worklog.get("id")
    comment = worklog.get("comment")

    if comment is None:
        print(f"  ⚠ Worklog {worklog_id}: Sin comment, omitiendo")
        return False

    # Construir nuevo comment
    if isinstance(comment, dict):
        new_comment = replace_text_in_adf(comment, "TASD-1", "TASD-4")
    elif isinstance(comment, str):
        new_comment = comment.replace("TASD-1", "TASD-4")
    else:
        print(f"  ⚠ Worklog {worklog_id}: Formato de comment no reconocido")
        return False

    # Payload para actualizar el worklog
    payload = {
        "comment": new_comment,
    }

    url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/worklog/{worklog_id}"

    try:
        make_request(url, method="PUT", data=payload)
        print(f"  ✓ Worklog {worklog_id}: Actualizado correctamente")
        return True
    except HTTPError:
        print(f"  ✗ Worklog {worklog_id}: Error al actualizar")
        return False


def main() -> None:
    """Punto de entrada principal del script."""
    print("=" * 60)
    print("Jira Worklog Updater")
    print(f"Issue fuente: {SOURCE_ISSUE_KEY}")
    print(f"Buscar: '{SEARCH_TEXT}'")
    print(f"Reemplazar por: '{REPLACEMENT_TEXT}'")
    print(f"Desde: {DATE_FROM.strftime('%Y-%m-%d')}")
    print("=" * 60)
    print()

    validate_environment()

    # Obtener worklogs del issue
    worklogs = get_worklogs(SOURCE_ISSUE_KEY)

    if not worklogs:
        print("No se encontraron worklogs en el issue.")
        return

    # Filtrar worklogs que coincidan
    print("\nFiltrando worklogs...")
    matching_worklogs = filter_worklogs(worklogs, debug=True)

    if not matching_worklogs:
        print("Ningún worklog coincide con los criterios.")
        return

    # Confirmar antes de actualizar
    print(f"\n¿Actualizar {len(matching_worklogs)} worklog(s)? (s/n): ", end="")
    confirmation = input().strip().lower()

    if confirmation not in ("s", "si", "sí", "y", "yes"):
        print("Operación cancelada.")
        return

    # Ejecutar actualizaciones
    print("\nActualizando worklogs...")
    success_count = 0
    for worklog in matching_worklogs:
        if update_worklog(SOURCE_ISSUE_KEY, worklog):
            success_count += 1

    print(f"\nResultado: {success_count}/{len(matching_worklogs)} worklogs actualizados.")


if __name__ == "__main__":
    main()
