"""CLI de obsidian-manager.

Capa de presentación: parseo de argumentos, serialización JSON (o ``--pretty``),
confirmaciones de operaciones destructivas, ``--dry-run`` y códigos de salida. No contiene
lógica de dominio: delega en ``vault.VaultClient`` y ``sources``.

Contrato de salida:

- Éxito: JSON en stdout. Con ``--pretty``, JSON indentado.
- Error: JSON ``{"error": {"type", "message"}}`` en stderr y código de salida != 0.

Códigos de salida:
    0 éxito · 2 uso · 3 permisos · 4 no encontrado · 6 conflicto/confirmación
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

import sources
import vault

# Códigos de salida.
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_PERMISSION = 3
EXIT_NOT_FOUND = 4
EXIT_CONFLICT = 6


def _configure_logging(level: str) -> None:
    """Configura logging estructurado sin contenido de notas."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.WARNING),
        format="ts=%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s",
    )


def _emit(data: Any, pretty: bool) -> None:
    """Imprime un resultado como JSON en stdout."""
    if pretty:
        print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True, default=str))
    else:
        print(json.dumps(data, ensure_ascii=False, default=str))


def _fail(exc_type: str, message: str, code: int) -> int:
    """Imprime un error JSON en stderr y devuelve el código de salida."""
    print(json.dumps({"error": {"type": exc_type, "message": message}}, ensure_ascii=False),
          file=sys.stderr)
    return code


def _repo_root() -> Path:
    """Raíz del repo (…/skills-personalizados-dev), derivada de la ubicación de este script."""
    # scripts/obsidian_cli.py -> obsidian-manager -> workspace -> skills -> repo
    return Path(__file__).resolve().parents[4]


def _build_parser() -> argparse.ArgumentParser:
    """Construye el parser con todos los subcomandos y flags globales."""
    # Parser padre reutilizable: flags globales aceptados antes o después del subcomando.
    g = argparse.ArgumentParser(add_help=False)
    g.add_argument("--pretty", action="store_true", default=argparse.SUPPRESS,
                   help="salida JSON legible")
    g.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS,
                   help="muestra el plan sin ejecutar")
    g.add_argument("--yes", action="store_true", default=argparse.SUPPRESS,
                   help="confirma operaciones destructivas")
    g.add_argument("--vault", default=argparse.SUPPRESS, help="ruta del vault (o OBSIDIAN_VAULT_PATH)")
    g.add_argument("--log-level", default=argparse.SUPPRESS, help="nivel de logging")

    parser = argparse.ArgumentParser(prog="obsidian_cli", description="Second brain en Obsidian",
                                     parents=[g])
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="inicializa el vault", parents=[g])
    p_init.add_argument("path", nargs="?", help="ruta del vault (opcional)")

    # note create|append|update
    p_note = sub.add_parser("note", help="operaciones de notas", parents=[g])
    note_sub = p_note.add_subparsers(dest="action", required=True)
    n_create = note_sub.add_parser("create", parents=[g])
    n_create.add_argument("title")
    n_create.add_argument("--body", default="")
    n_create.add_argument("--folder", default=vault.INBOX_DIR)
    n_create.add_argument("--tag", action="append", dest="tags")
    n_create.add_argument("--alias", action="append", dest="aliases")
    n_create.add_argument("--project")
    n_create.add_argument("--link", action="append", dest="links")
    n_create.add_argument("--on-conflict",
                          choices=[vault.CONFLICT_NEW, vault.CONFLICT_SKIP, vault.CONFLICT_OVERWRITE],
                          default=vault.CONFLICT_NEW)
    n_append = note_sub.add_parser("append", parents=[g])
    n_append.add_argument("note")
    n_append.add_argument("text")
    n_update = note_sub.add_parser("update", parents=[g])
    n_update.add_argument("note")
    n_update.add_argument("--frontmatter", help="JSON con campos a fusionar")
    n_update.add_argument("--body", help="nuevo cuerpo (destructivo)")

    # search
    p_search = sub.add_parser("search", help="busca notas", parents=[g])
    p_search.add_argument("--text")
    p_search.add_argument("--tag")
    p_search.add_argument("--links-to")
    p_search.add_argument("--folder")
    p_search.add_argument("--limit", type=int, default=200)

    # graph backlinks|outlinks|orphans
    p_graph = sub.add_parser("graph", help="grafo de enlaces", parents=[g])
    graph_sub = p_graph.add_subparsers(dest="action", required=True)
    gb = graph_sub.add_parser("backlinks", parents=[g])
    gb.add_argument("note")
    go = graph_sub.add_parser("outlinks", parents=[g])
    go.add_argument("note")
    graph_sub.add_parser("orphans", parents=[g])

    # ingest
    p_ing = sub.add_parser("ingest", help="ingiere un archivo o stdin ('-')", parents=[g])
    p_ing.add_argument("source", help="ruta local o '-' para stdin")
    p_ing.add_argument("--title")
    p_ing.add_argument("--folder", default=vault.INBOX_DIR)
    p_ing.add_argument("--tag", action="append", dest="tags")
    p_ing.add_argument("--project")
    p_ing.add_argument("--link", action="append", dest="links")

    # daily
    p_daily = sub.add_parser("daily", help="daily note del día", parents=[g])
    p_daily.add_argument("--add", help="entrada a añadir a 'Trabajado'")
    p_daily.add_argument("--date", help="fecha YYYY-MM-DD (default hoy)")
    p_daily.add_argument("--project")

    # task add|list|done
    p_task = sub.add_parser("task", help="pendientes / tareas", parents=[g])
    task_sub = p_task.add_subparsers(dest="action", required=True)
    t_add = task_sub.add_parser("add", parents=[g])
    t_add.add_argument("text")
    t_add.add_argument("--project")
    t_list = task_sub.add_parser("list", parents=[g])
    t_list.add_argument("--project")
    t_list.add_argument("--include-done", action="store_true")
    t_done = task_sub.add_parser("done", parents=[g])
    t_done.add_argument("text")
    t_done.add_argument("--project")

    # project create|note|list
    p_proj = sub.add_parser("project", help="contexto de proyectos", parents=[g])
    proj_sub = p_proj.add_subparsers(dest="action", required=True)
    pc = proj_sub.add_parser("create", parents=[g])
    pc.add_argument("name")
    pc.add_argument("--status", default="activo")
    pc.add_argument("--tag", action="append", dest="tags")
    pn = proj_sub.add_parser("note", parents=[g])
    pn.add_argument("name")
    pn.add_argument("text")
    pn.add_argument("--section", default="Resumen")
    proj_sub.add_parser("list", parents=[g])

    # sources list|sync
    p_src = sub.add_parser("sources", help="orquestación de fuentes", parents=[g])
    src_sub = p_src.add_subparsers(dest="action", required=True)
    src_sub.add_parser("list", parents=[g])
    ss = src_sub.add_parser("sync", parents=[g])
    ss.add_argument("name")

    # trash|restore
    p_trash = sub.add_parser("trash", help="envía una nota a la papelera", parents=[g])
    p_trash.add_argument("note")
    p_restore = sub.add_parser("restore", help="restaura una nota de la papelera", parents=[g])
    p_restore.add_argument("trash_name")
    p_restore.add_argument("--folder", default=vault.INBOX_DIR)

    return parser


def _make_client(args) -> vault.VaultClient:
    """Construye un ``VaultClient`` a partir de la ruta resuelta del vault."""
    vault_path = vault.resolve_vault_path(getattr(args, "vault", None))
    return vault.VaultClient(vault_path)


# --- Handlers ----------------------------------------------------------------


def _cmd_init(client, args) -> Any:
    vault_path = vault.resolve_vault_path(getattr(args, "path", None) or getattr(args, "vault", None))
    return vault.init_vault(vault_path)


def _cmd_note(client, args) -> Any:
    if args.action == "create":
        return client.create_note(
            args.title, body=args.body, folder=args.folder,
            tags=args.tags, aliases=args.aliases,
            project=args.project, links=args.links,
            on_conflict=args.on_conflict, confirmed=args.yes,
        )
    if args.action == "append":
        return client.append_note(args.note, args.text)
    if args.action == "update":
        if not args.frontmatter and args.body is None:
            raise ValueError("Indique --frontmatter y/o --body")
        result: dict[str, Any] = {}
        if args.frontmatter:
            updates = json.loads(args.frontmatter)
            result["frontmatter"] = client.update_frontmatter(args.note, updates)
        if args.body is not None:
            if args.dry_run:
                result["body"] = {"dry_run": True, "action": "update_body", "note": args.note}
            else:
                result["body"] = client.update_body(args.note, args.body, confirmed=args.yes)
        return result
    raise ValueError(f"acción de note desconocida: {args.action}")


def _cmd_search(client, args) -> Any:
    return client.search(
        text=args.text, tag=args.tag, links_to=args.links_to,
        folder=args.folder, limit=args.limit,
    )


def _cmd_graph(client, args) -> Any:
    if args.action == "backlinks":
        return client.backlinks(args.note)
    if args.action == "outlinks":
        return client.outlinks(args.note)
    if args.action == "orphans":
        return client.orphans()
    raise ValueError(f"acción de graph desconocida: {args.action}")


def _cmd_ingest(client, args) -> Any:
    if args.source == "-":
        stdin_text = sys.stdin.read()
        return client.ingest(
            stdin_text=stdin_text, title=args.title, folder=args.folder,
            tags=args.tags, project=args.project, links=args.links, dry_run=args.dry_run,
        )
    return client.ingest(
        source_path=args.source, title=args.title, folder=args.folder,
        tags=args.tags, project=args.project, links=args.links, dry_run=args.dry_run,
    )


def _cmd_daily(client, args) -> Any:
    day = date.fromisoformat(args.date) if args.date else None
    if args.add:
        return client.daily_add(args.add, day=day, project=args.project)
    return client.daily(day=day)


def _cmd_task(client, args) -> Any:
    if args.action == "add":
        return client.task_add(args.text, project=args.project)
    if args.action == "list":
        return client.task_list(project=args.project, include_done=args.include_done)
    if args.action == "done":
        return client.task_done(args.text, project=args.project)
    raise ValueError(f"acción de task desconocida: {args.action}")


def _cmd_project(client, args) -> Any:
    if args.action == "create":
        return client.project_create(args.name, tags=args.tags, status=args.status)
    if args.action == "note":
        return client.project_note(args.name, args.text, section=args.section)
    if args.action == "list":
        return client.project_list()
    raise ValueError(f"acción de project desconocida: {args.action}")


def _cmd_sources(client, args) -> Any:
    if args.action == "list":
        return sources.list_sources(client)
    if args.action == "sync":
        return sources.sync(client, args.name, repo_root=_repo_root(), dry_run=args.dry_run)
    raise ValueError(f"acción de sources desconocida: {args.action}")


def _cmd_trash(client, args) -> Any:
    if args.dry_run:
        return {"dry_run": True, "action": "trash", "note": args.note}
    return client.trash(args.note, confirmed=args.yes)


def _cmd_restore(client, args) -> Any:
    return client.restore(args.trash_name, dest_folder=args.folder)


_HANDLERS = {
    "init": _cmd_init,
    "note": _cmd_note,
    "search": _cmd_search,
    "graph": _cmd_graph,
    "ingest": _cmd_ingest,
    "daily": _cmd_daily,
    "task": _cmd_task,
    "project": _cmd_project,
    "sources": _cmd_sources,
    "trash": _cmd_trash,
    "restore": _cmd_restore,
}


def run(argv: list[str], client_factory=_make_client) -> int:
    """Punto de entrada testeable del CLI.

    :param argv: argumentos (sin el nombre del programa).
    :param client_factory: fábrica de ``VaultClient`` (inyectable para tests).
    :return: código de salida.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.pretty = getattr(args, "pretty", False)
    args.dry_run = getattr(args, "dry_run", False)
    args.yes = getattr(args, "yes", False)
    args.log_level = getattr(args, "log_level", "WARNING")
    _configure_logging(args.log_level)

    handler = _HANDLERS[args.command]
    try:
        # ``init`` no requiere un vault existente; el resto sí.
        client = None if args.command == "init" else client_factory(args)
        result = handler(client, args)
    except vault.ConflictError as exc:
        return _fail("ConflictError", str(exc), EXIT_CONFLICT)
    except vault.UnsafePathError as exc:
        return _fail("UnsafePathError", str(exc), EXIT_USAGE)
    except vault.NotFoundError as exc:
        return _fail("NotFoundError", str(exc), EXIT_NOT_FOUND)
    except PermissionError as exc:
        return _fail("PermissionError", str(exc), EXIT_PERMISSION)
    except sources.SourceError as exc:
        return _fail("SourceError", str(exc), EXIT_USAGE)
    except (ValueError, json.JSONDecodeError) as exc:
        return _fail(type(exc).__name__, str(exc), EXIT_USAGE)
    except vault.VaultError as exc:
        return _fail("VaultError", str(exc), EXIT_USAGE)

    _emit(result, args.pretty)
    return EXIT_OK


def main() -> int:
    """Entry point de consola."""
    return run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
