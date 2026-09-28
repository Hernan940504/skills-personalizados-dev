"""CLI de google-drive-manager.

Capa de presentación: parseo de argumentos, serialización JSON (o ``--pretty``),
confirmaciones de operaciones destructivas/masivas, ``--dry-run`` y códigos de salida.
No contiene lógica de la Drive API: delega en ``drive_client.DriveClient``.

Contrato de salida:

- Éxito: JSON en stdout. Con ``--pretty``, JSON indentado.
- Error: JSON ``{"error": {"type", "message"}}`` en stderr y código de salida != 0.

Códigos de salida:
    0 éxito · 2 uso · 3 permisos · 4 no encontrado · 5 cuota · 6 conflicto · 7 auth
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

import auth
import drive_client as dc
import mime_map

# Códigos de salida.
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_PERMISSION = 3
EXIT_NOT_FOUND = 4
EXIT_QUOTA = 5
EXIT_CONFLICT = 6
EXIT_AUTH = 7


def _configure_logging(level: str) -> None:
    """Configura logging estructurado sin contenido sensible.

    :param level: nivel de logging (``DEBUG``/``INFO``/``WARNING``/...).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.WARNING),
        format="ts=%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s",
    )


def _emit(data: Any, pretty: bool) -> None:
    """Imprime un resultado como JSON en stdout.

    :param data: estructura serializable.
    :param pretty: si ``True``, indenta para lectura humana.
    """
    if pretty:
        print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(data, ensure_ascii=False))


def _fail(exc_type: str, message: str, code: int) -> int:
    """Imprime un error JSON en stderr y devuelve el código de salida.

    :param exc_type: nombre del tipo de error.
    :param message: mensaje legible (sin datos sensibles).
    :param code: código de salida a retornar.
    :return: el mismo ``code``.
    """
    print(json.dumps({"error": {"type": exc_type, "message": message}}, ensure_ascii=False),
          file=sys.stderr)
    return code


def _build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos con todos los subcomandos.

    :return: parser configurado.
    """
    # Flags globales en un parser "padre" reutilizable: así se aceptan tanto ANTES
    # del subcomando (`drive_cli --pretty drives`) como DESPUÉS (`drive_cli drives --pretty`).
    # default=SUPPRESS: el flag solo aparece en el namespace si el usuario lo pasa. Así,
    # al repetirse en el subparser (parents), un valor dado ANTES del subcomando no se pisa
    # con el default del subparser. Los defaults reales se aplican en run() con getattr.
    global_flags = argparse.ArgumentParser(add_help=False)
    global_flags.add_argument("--pretty", action="store_true", default=argparse.SUPPRESS,
                              help="salida JSON legible")
    global_flags.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS,
                              help="muestra el plan sin ejecutar")
    global_flags.add_argument("--yes", action="store_true", default=argparse.SUPPRESS,
                              help="confirma operaciones destructivas")
    global_flags.add_argument("--log-level", default=argparse.SUPPRESS, help="nivel de logging")

    parser = argparse.ArgumentParser(
        prog="drive_cli", description="Gestor de Google Drive", parents=[global_flags]
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("auth", help="autentica vía OAuth 2.0 (installed app)", parents=[global_flags])
    sub.add_parser("drives", help="lista unidades compartidas accesibles", parents=[global_flags])

    p_search = sub.add_parser("search", help="busca/lista archivos", parents=[global_flags])
    p_search.add_argument("--scope", choices=[dc.SCOPE_ALL, dc.SCOPE_MYDRIVE], default=dc.SCOPE_ALL)
    p_search.add_argument("--drive", help="id de Shared Drive")
    p_search.add_argument("--name")
    p_search.add_argument("--name-contains")
    p_search.add_argument("--parent")
    p_search.add_argument("--mime-type")
    p_search.add_argument("--modified-after")
    p_search.add_argument("--modified-before")
    p_search.add_argument("--owner")
    p_search.add_argument("--limit", type=int, default=200,
                          help="máximo de resultados (default 200)")
    p_search.add_argument("--all", action="store_true",
                          help="trae todos los resultados (ignora --limit; puede ser lento)")

    p_dl = sub.add_parser("download", help="descarga o exporta un archivo/carpeta", parents=[global_flags])
    p_dl.add_argument("file_id")
    p_dl.add_argument("dest")
    p_dl.add_argument("--export", help="formato de export para tipos Google")
    p_dl.add_argument("--recursive", action="store_true", help="descarga recursiva de carpeta")

    p_up = sub.add_parser("upload", help="sube un archivo (simple/resumable)", parents=[global_flags])
    p_up.add_argument("local_path")
    p_up.add_argument("parent")
    p_up.add_argument("--name")
    p_up.add_argument("--convert", action="store_true")
    p_up.add_argument("--on-conflict", choices=[dc.CONFLICT_NEW, dc.CONFLICT_REPLACE, dc.CONFLICT_VERSION])
    p_up.add_argument("--drive", help="id de Shared Drive destino")

    p_upd = sub.add_parser("update", help="actualiza contenido o metadatos", parents=[global_flags])
    p_upd.add_argument("file_id")
    p_upd.add_argument("--content", help="ruta de nuevo contenido")
    p_upd.add_argument("--name")
    p_upd.add_argument("--description")

    p_org = sub.add_parser("organize", help="operaciones de organización", parents=[global_flags])
    org_sub = p_org.add_subparsers(dest="action", required=True)
    o_mkdir = org_sub.add_parser("mkdir", parents=[global_flags])
    o_mkdir.add_argument("path")
    o_mkdir.add_argument("--root", default="root")
    o_mkdir.add_argument("--drive")
    o_move = org_sub.add_parser("move", parents=[global_flags])
    o_move.add_argument("file_id")
    o_move.add_argument("add_parent")
    o_move.add_argument("--remove-parent")
    o_rename = org_sub.add_parser("rename", parents=[global_flags])
    o_rename.add_argument("file_id")
    o_rename.add_argument("new_name")
    o_copy = org_sub.add_parser("copy", parents=[global_flags])
    o_copy.add_argument("file_id")
    o_copy.add_argument("--name")
    o_copy.add_argument("--parent")
    o_trash = org_sub.add_parser("trash", parents=[global_flags])
    o_trash.add_argument("file_id")
    o_restore = org_sub.add_parser("restore", parents=[global_flags])
    o_restore.add_argument("file_id")

    return parser


def _make_client(args) -> dc.DriveClient:
    """Construye un ``DriveClient`` autenticado (service real de Drive).

    :param args: namespace con configuración global.
    :return: cliente listo para operar.
    """
    from googleapiclient.discovery import build

    settings = auth.load_settings()
    creds = auth.get_credentials(settings)
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return dc.DriveClient(service)


# --- Handlers de subcomandos -------------------------------------------------


def _cmd_auth(client, args) -> Any:
    """Handler de ``auth``: fuerza la obtención/renovación de credenciales."""
    return {"status": "authenticated"}


def _cmd_drives(client, args) -> Any:
    return {"drives": client.list_shared_drives()}


def _cmd_search(client, args) -> Any:
    max_results = None if args.all else args.limit
    files = client.search(
        scope=args.scope,
        drive_id=args.drive,
        name=args.name,
        name_contains=args.name_contains,
        parent=args.parent,
        mime_type=args.mime_type,
        modified_after=args.modified_after,
        modified_before=args.modified_before,
        owner=args.owner,
        max_results=max_results,
    )
    result: dict[str, Any] = {"files": files, "count": len(files)}
    if max_results is not None and len(files) == max_results:
        result["truncated"] = True
        result["hint"] = "Hay más resultados; afina filtros o usa --all para traer todo."
    return result


def _cmd_download(client, args) -> Any:
    if args.recursive:
        if args.dry_run:
            return {"dry_run": True, "action": "download_folder_recursive",
                    "folder_id": args.file_id, "dest": args.dest, "export": args.export}
        written = client.download_folder_recursive(args.file_id, args.dest, args.export)
        return {"downloaded": written, "count": len(written)}

    meta = client.get_file(args.file_id)
    if args.dry_run:
        return {"dry_run": True, "action": "download", "file": meta, "export": args.export}
    if mime_map.is_google_native(meta["mimeType"]):
        path = client.export_file(args.file_id, meta["mimeType"], args.dest, args.export)
    else:
        path = client.download_file(args.file_id, args.dest)
    return {"downloaded": path}


def _cmd_upload(client, args) -> Any:
    if args.dry_run:
        return {"dry_run": True, "action": "upload", "local_path": args.local_path,
                "parent": args.parent, "convert": args.convert}
    result = client.upload(
        args.local_path,
        args.parent,
        name=args.name,
        convert=args.convert,
        on_conflict=args.on_conflict,
        drive_id=args.drive,
    )
    return {"uploaded": result}


def _cmd_update(client, args) -> Any:
    if not args.content and not args.name and not args.description:
        raise ValueError("Indique --content y/o --name/--description")
    if args.dry_run:
        return {"dry_run": True, "action": "update", "file_id": args.file_id,
                "content": bool(args.content), "name": args.name, "description": args.description}
    # Reemplazo de contenido es destructivo: exige confirmación.
    if args.content and not args.yes:
        raise _ConfirmationRequired("update --content reemplaza el contenido; use --yes o --dry-run")
    results: dict[str, Any] = {}
    if args.content:
        results["content"] = client.update_content(args.file_id, args.content)
    if args.name or args.description:
        results["metadata"] = client.update_metadata(
            args.file_id, name=args.name, description=args.description
        )
    return {"updated": results}


def _cmd_organize(client, args) -> Any:
    action = args.action
    if action == "mkdir":
        if args.dry_run:
            return {"dry_run": True, "action": "mkdir", "path": args.path}
        return {"folder_id": client.mkdir_p(args.path, root=args.root, drive_id=args.drive)}
    if action == "move":
        if args.dry_run:
            return {"dry_run": True, "action": "move", "file_id": args.file_id,
                    "add_parent": args.add_parent}
        return {"moved": client.move(args.file_id, args.add_parent, args.remove_parent)}
    if action == "rename":
        if args.dry_run:
            return {"dry_run": True, "action": "rename", "file_id": args.file_id,
                    "new_name": args.new_name}
        return {"renamed": client.rename(args.file_id, args.new_name)}
    if action == "copy":
        if args.dry_run:
            return {"dry_run": True, "action": "copy", "file_id": args.file_id}
        return {"copied": client.copy(args.file_id, args.name, args.parent)}
    if action == "trash":
        if args.dry_run:
            return {"dry_run": True, "action": "trash", "file_id": args.file_id}
        if not args.yes:
            raise _ConfirmationRequired("trash es destructivo; use --yes o --dry-run")
        return {"trashed": client.trash(args.file_id)}
    if action == "restore":
        if args.dry_run:
            return {"dry_run": True, "action": "restore", "file_id": args.file_id}
        return {"restored": client.restore(args.file_id)}
    raise ValueError(f"acción de organize desconocida: {action}")


class _ConfirmationRequired(RuntimeError):
    """Operación destructiva sin ``--yes`` ni ``--dry-run``."""


_HANDLERS = {
    "auth": _cmd_auth,
    "drives": _cmd_drives,
    "search": _cmd_search,
    "download": _cmd_download,
    "upload": _cmd_upload,
    "update": _cmd_update,
    "organize": _cmd_organize,
}


def run(argv: list[str], client_factory=_make_client) -> int:
    """Punto de entrada testeable del CLI.

    :param argv: argumentos de línea de comandos (sin el nombre del programa).
    :param client_factory: fábrica de ``DriveClient`` (inyectable para tests).
    :return: código de salida.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    # Defaults de flags globales (con SUPPRESS pueden no existir en el namespace).
    args.pretty = getattr(args, "pretty", False)
    args.dry_run = getattr(args, "dry_run", False)
    args.yes = getattr(args, "yes", False)
    args.log_level = getattr(args, "log_level", "WARNING")
    _configure_logging(args.log_level)

    handler = _HANDLERS[args.command]
    try:
        # auth no requiere un cliente ya construido en modo normal, pero client_factory
        # dispara la autenticación; para ``auth`` basta con invocarla.
        client = None if args.command == "auth" else client_factory(args)
        if args.command == "auth":
            client_factory(args)
        result = handler(client, args)
    except _ConfirmationRequired as exc:
        return _fail("ConfirmationRequired", str(exc), EXIT_CONFLICT)
    except dc.ConflictError as exc:
        return _fail("ConflictError", str(exc), EXIT_CONFLICT)
    except dc.PermissionDeniedError as exc:
        return _fail("PermissionDeniedError", str(exc), EXIT_PERMISSION)
    except (dc.NotFoundError, dc.PathAmbiguousError) as exc:
        return _fail(type(exc).__name__, str(exc), EXIT_NOT_FOUND)
    except dc.QuotaExceededError as exc:
        return _fail("QuotaExceededError", str(exc), EXIT_QUOTA)
    except auth.AuthRequiredError as exc:
        return _fail("AuthRequiredError", str(exc), EXIT_AUTH)
    except (ValueError, mime_map.UnsupportedExportFormatError) as exc:
        return _fail(type(exc).__name__, str(exc), EXIT_USAGE)
    except dc.DriveClientError as exc:
        return _fail("DriveClientError", str(exc), EXIT_USAGE)

    _emit(result, args.pretty)
    return EXIT_OK


def main() -> int:
    """Entry point de consola."""
    return run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
