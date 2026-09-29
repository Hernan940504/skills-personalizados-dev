"""Orquestación de fuentes: alimentar el second brain invocando otros skills del repo.

Este módulo es un **adaptador delgado guiado por configuración**. NO contiene conocimiento
específico de Drive, Sheets, Langfuse ni de ningún skill concreto: todo el mapeo vive en el
registro de fuentes ``.brain/fuentes.json`` del vault (datos, no código). Así, "cada skill nuevo
del repo es una nueva capacidad del brain" se logra editando ese JSON, sin tocar este código
(Historia 9 del spec).

Formato de una fuente en ``fuentes.json``:

    {
      "name": "drive-proyectos",
      "description": "Descarga material de Drive e ingiere como notas",
      "skill_path": "skills/workspace/google-drive-manager/scripts/drive_cli.py",
      "command": ["download", "<FOLDER_ID>", "./.brain/tmp/drive", "--recursive", "--export", "md"],
      "map": { "content_from": "downloaded", "project": "ciencuadras", "tags": ["drive"] }
    }

- ``skill_path``: ruta (relativa al repo) del CLI del skill fuente.
- ``command``: argumentos que se pasan a ese CLI.
- ``map.content_from``: clave de la salida JSON del skill que contiene la(s) ruta(s) a ingerir.
- ``map.project`` / ``map.tags``: metadatos con los que se ingiere cada archivo.

Solo stdlib (``json``, ``subprocess``). Cumple RNF-1.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("obsidian.sources")


class SourceError(RuntimeError):
    """La fuente no existe, está mal configurada, o su ejecución falló."""


def load_sources(vault) -> dict[str, Any]:
    """Carga el registro de fuentes desde ``<vault>/.brain/fuentes.json``.

    :param vault: instancia de ``VaultClient``.
    :return: dict con la clave ``sources`` (lista). Si no existe el archivo, ``{"sources": []}``.
    :raises SourceError: si el JSON está corrupto.
    """
    from vault import SOURCES_FILE  # import diferido para evitar ciclo en tests

    path = vault.path / SOURCES_FILE
    if not path.exists():
        return {"sources": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SourceError(f"fuentes.json inválido: {exc}") from exc
    if "sources" not in data or not isinstance(data["sources"], list):
        raise SourceError("fuentes.json debe contener una lista 'sources'.")
    return data


def list_sources(vault) -> dict[str, Any]:
    """Lista las fuentes registradas con su descripción y estado (declarada).

    :param vault: instancia de ``VaultClient``.
    :return: dict con ``sources`` (nombre, descripción, skill_path) y ``count``.
    """
    data = load_sources(vault)
    items = [
        {
            "name": s.get("name"),
            "description": s.get("description", ""),
            "skill_path": s.get("skill_path"),
            "status": "declarada",
        }
        for s in data["sources"]
    ]
    return {"sources": items, "count": len(items)}


def sync(
    vault,
    name: str,
    *,
    repo_root: Path,
    dry_run: bool = False,
    runner: Callable[[list[str]], str] | None = None,
) -> dict[str, Any]:
    """Ejecuta una fuente: invoca el CLI del skill y mapea su salida a ``ingest``.

    El fallo de una fuente se reporta pero NO corrompe el vault (Historia 9.5): las excepciones
    de ejecución se envuelven en ``SourceError`` y no dejan escritura parcial.

    :param vault: instancia de ``VaultClient``.
    :param name: nombre de la fuente en ``fuentes.json``.
    :param repo_root: raíz del repo, para resolver ``skill_path``.
    :param dry_run: si ``True``, reporta el plan sin invocar el skill ni ingerir.
    :param runner: función que ejecuta el comando y devuelve stdout (inyectable para tests).
    :return: dict con el resultado de la sincronización (fuente, notas creadas o plan).
    :raises SourceError: si la fuente no existe o su ejecución falla.
    """
    source = _find_source(vault, name)
    skill_path = (repo_root / source["skill_path"]).resolve()
    argv = [sys.executable, str(skill_path), *source.get("command", [])]
    mapping = source.get("map", {})

    if dry_run:
        return {
            "dry_run": True,
            "source": name,
            "would_run": argv,
            "map": mapping,
        }

    runner = runner or _default_runner
    try:
        stdout = runner(argv)
    except Exception as exc:  # noqa: BLE001 — fallo aislado por fuente (Historia 9.5)
        raise SourceError(f"La fuente {name!r} falló al ejecutarse: {exc}") from exc

    payload = _parse_json(stdout, name)
    contents = _extract_contents(payload, mapping.get("content_from"))
    ingested = _ingest_all(vault, contents, mapping)
    return {"source": name, "ingested": ingested, "count": len(ingested)}


# --- Helpers internos --------------------------------------------------------


def _find_source(vault, name: str) -> dict[str, Any]:
    """Devuelve la definición de una fuente por nombre, o levanta ``SourceError``."""
    for source in load_sources(vault)["sources"]:
        if source.get("name") == name:
            return source
    raise SourceError(f"Fuente no encontrada: {name!r}")


def _default_runner(argv: list[str]) -> str:
    """Ejecuta el comando del skill fuente y devuelve su stdout (texto).

    :param argv: comando completo a ejecutar.
    :return: stdout del proceso.
    :raises subprocess.CalledProcessError: si el proceso devuelve código distinto de cero.
    """
    completed = subprocess.run(  # noqa: S603 — argv construido desde config del propio usuario
        argv, capture_output=True, text=True, check=True
    )
    return completed.stdout


def _parse_json(stdout: str, name: str) -> Any:
    """Parsea la salida JSON del skill fuente."""
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SourceError(f"La fuente {name!r} no devolvió JSON válido: {exc}") from exc


def _extract_contents(payload: Any, content_from: str | None) -> list[str]:
    """Extrae la lista de rutas/contenidos a ingerir desde la salida del skill.

    :param payload: salida JSON ya parseada del skill fuente.
    :param content_from: clave que contiene la(s) ruta(s); si es ``None``, intenta heurística.
    :return: lista de rutas locales a ingerir.
    """
    if content_from and isinstance(payload, dict):
        value = payload.get(content_from)
    else:
        value = payload
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _ingest_all(vault, contents: list[str], mapping: dict[str, Any]) -> list[dict[str, Any]]:
    """Ingiere cada ruta con los metadatos del mapping."""
    project = mapping.get("project")
    tags = mapping.get("tags")
    results: list[dict[str, Any]] = []
    for path in contents:
        result = vault.ingest(source_path=path, project=project, tags=tags)
        results.append(result)
    return results
