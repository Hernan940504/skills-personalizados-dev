"""Cliente de vault de Obsidian: núcleo de seguridad, escritura y operaciones del second brain.

Capa de dominio del skill. No hace parseo de argumentos ni serialización JSON (eso vive en
``obsidian_cli.py``); expone métodos que devuelven estructuras Python.

Garantías de seguridad (RNF-3):

- Toda ruta destino se canonicaliza y se valida que quede DENTRO del vault (anti path-traversal).
- Escritura atómica (archivo temporal + ``os.replace``) para no dejar notas a medias (RNF-4).
- Sin borrado permanente: solo mover a ``.trash/`` (reversible).
- Sin red, sin secretos, sin contenido de notas en logs.

Solo stdlib. Cumple RNF-1.
"""

from __future__ import annotations

import logging
import os
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any

import frontmatter
import markdown_index as mi

logger = logging.getLogger("obsidian.vault")

# Variable de entorno y default del vault (fuera del repo).
ENV_VAULT_PATH = "OBSIDIAN_VAULT_PATH"
_DEFAULT_VAULT = Path.home() / "second-brain"

# Estructura base del vault que crea ``init`` (design §3).
BASE_DIRS = [
    "inbox",
    "proyectos",
    "daily",
    "referencias",
    "referencias/adjuntos",
    "plantillas",
    ".trash",
    ".brain",
    ".obsidian",
]

# Carpetas por defecto.
INBOX_DIR = "inbox"
DAILY_DIR = "daily"
PROJECTS_DIR = "proyectos"
ATTACHMENTS_DIR = "referencias/adjuntos"
TRASH_DIR = ".trash"
BRAIN_DIR = ".brain"
GLOBAL_TASKS_NOTE = "pendientes.md"
INDEX_NOTE = "index.md"
SOURCES_FILE = ".brain/fuentes.json"

# Estrategias de colisión de nombre.
CONFLICT_NEW = "new"
CONFLICT_SKIP = "skip"
CONFLICT_OVERWRITE = "overwrite"

# Extensiones que, aunque sean texto (XML/SVG), se tratan como ADJUNTO y no como cuerpo de nota:
# son formatos que se abren en su editor (diagramas, dibujos) y embeberlos como texto crudo
# contamina el vault (p. ej. un .drawio de varios MB). Se copian a adjuntos y se referencian.
ATTACHMENT_EXTENSIONS = {".drawio", ".svg", ".xml", ".excalidraw"}


class VaultError(RuntimeError):
    """Error base del cliente de vault."""


class NotFoundError(VaultError):
    """El vault o una nota solicitada no existe."""


class ConflictError(VaultError):
    """Colisión de nombre o confirmación destructiva requerida."""


class UnsafePathError(VaultError):
    """Una ruta destino escaparía del vault (path traversal)."""


def resolve_vault_path(explicit: str | None = None, env: dict[str, str] | None = None) -> Path:
    """Resuelve la ruta del vault desde argumento explícito, env var o default.

    :param explicit: ruta pasada explícitamente (mayor prioridad).
    :param env: mapping de entorno; por defecto ``os.environ``.
    :return: ruta expandida (no garantiza que exista).
    """
    env = env if env is not None else dict(os.environ)
    if explicit:
        return Path(explicit).expanduser()
    configured = env.get(ENV_VAULT_PATH)
    if configured:
        return Path(configured).expanduser()
    return _DEFAULT_VAULT


def slugify(title: str) -> str:
    """Deriva un nombre de archivo seguro (slug) a partir de un título.

    :param title: título legible de la nota.
    :return: slug en minúsculas, ascii, con guiones; ``nota`` si queda vacío.
    """
    normalized = unicodedata.normalize("NFKD", title)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug or "nota"


class VaultClient:
    """Operaciones sobre un vault de Obsidian confinadas a su directorio raíz.

    :param vault_path: ruta al vault.
    :param require_exists: si ``True`` (default), valida que el vault exista; ``init`` usa ``False``.
    """

    def __init__(self, vault_path: str | os.PathLike[str], *, require_exists: bool = True) -> None:
        self._vault = Path(vault_path).expanduser()
        if require_exists:
            if not self._vault.exists():
                raise NotFoundError(
                    f"El vault no existe en {self._vault}. Ejecute `init` para crearlo."
                )
            self._vault_real = self._vault.resolve()
        else:
            # Para init: la raíz puede no existir todavía; se canonicaliza el padre existente.
            self._vault_real = self._vault.resolve()

    @property
    def path(self) -> Path:
        """Ruta canónica del vault."""
        return self._vault_real

    def is_initialized(self) -> bool:
        """Indica si la ruta ya contiene un vault (``.obsidian/`` o ``index.md``)."""
        return (self._vault / ".obsidian").exists() or (self._vault / INDEX_NOTE).exists()

    # --- Notas: crear, anexar, actualizar ------------------------------------

    def create_note(
        self,
        title: str,
        *,
        body: str = "",
        folder: str = INBOX_DIR,
        tags: list[str] | None = None,
        aliases: list[str] | None = None,
        extra_frontmatter: dict[str, Any] | None = None,
        project: str | None = None,
        links: list[str] | None = None,
        on_conflict: str = CONFLICT_NEW,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        """Crea una nota Markdown con frontmatter en la carpeta indicada.

        :param title: título legible (base del nombre de archivo y del campo ``title``).
        :param body: cuerpo Markdown de la nota.
        :param folder: carpeta relativa destino (default ``inbox``).
        :param tags: tags para el frontmatter.
        :param aliases: aliases para el frontmatter.
        :param extra_frontmatter: campos adicionales de frontmatter.
        :param project: slug de proyecto al que asociar y enlazar la nota.
        :param links: nombres/slugs de notas a enlazar (wikilinks) desde la nota.
        :param on_conflict: estrategia si el nombre existe: ``new``/``skip``/``overwrite``.
        :param confirmed: confirmación explícita, requerida para ``overwrite`` (destructivo).
        :return: dict con ``path`` (relativo), ``name`` y ``created`` (bool).
        :raises ConflictError: si ``overwrite`` sin ``confirmed``.
        """
        base_slug = slugify(title)
        existing = self._safe_path(f"{folder}/{base_slug}.md")

        if existing.exists():
            if on_conflict == CONFLICT_SKIP:
                return {
                    "path": self._relpath(existing),
                    "name": base_slug,
                    "created": False,
                    "skipped": True,
                }
            if on_conflict == CONFLICT_OVERWRITE:
                if not confirmed:
                    raise ConflictError(
                        "Sobrescribir una nota es destructivo; use --yes o --dry-run."
                    )
                slug = base_slug
            else:  # CONFLICT_NEW
                slug = self._unique_slug(folder, base_slug)
        else:
            slug = base_slug

        fm: dict[str, Any] = {"title": title, "created": self._today()}
        if tags:
            fm["tags"] = list(tags)
        if aliases:
            fm["aliases"] = list(aliases)
        if project:
            fm["project"] = slugify(project)
        if extra_frontmatter:
            fm = frontmatter.merge(fm, extra_frontmatter)

        if project or links:
            body = self._with_links(body, project=project, links=links)

        target = self._safe_path(f"{folder}/{slug}.md")
        self._atomic_write(target, frontmatter.dump(fm, body))
        logger.info("nota creada name=%s folder=%s", slug, folder)
        self._link_project(project, slug)
        return {"path": self._relpath(target), "name": slug, "created": True}

    def append_note(self, name_or_path: str, text: str) -> dict[str, Any]:
        """Añade contenido al final del cuerpo de una nota, sin tocar su frontmatter.

        :param name_or_path: nombre de nota o ruta relativa dentro del vault.
        :param text: texto a anexar (se separa con una línea en blanco).
        :return: dict con ``path`` y ``appended`` (True).
        :raises NotFoundError: si la nota no existe.
        """
        target = self._resolve_note(name_or_path)
        fm, body = frontmatter.parse(self._read(target))
        separator = "\n\n" if body and not body.endswith("\n\n") else ""
        new_body = f"{body}{separator}{text}\n"
        self._atomic_write(target, frontmatter.dump(fm, new_body))
        return {"path": self._relpath(target), "appended": True}

    def update_frontmatter(self, name_or_path: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Fusiona campos en el frontmatter de una nota conservando el cuerpo.

        :param name_or_path: nombre de nota o ruta relativa.
        :param updates: campos a fusionar (tags/aliases se unen sin duplicar).
        :return: dict con ``path`` y ``updated`` (True).
        :raises NotFoundError: si la nota no existe.
        """
        target = self._resolve_note(name_or_path)
        fm, body = frontmatter.parse(self._read(target))
        merged = frontmatter.merge(fm, updates)
        self._atomic_write(target, frontmatter.dump(merged, body))
        return {"path": self._relpath(target), "updated": True}

    def update_body(self, name_or_path: str, new_body: str, *, confirmed: bool = False) -> dict[str, Any]:
        """Reemplaza el cuerpo de una nota (destructivo), conservando el frontmatter.

        :param name_or_path: nombre de nota o ruta relativa.
        :param new_body: nuevo cuerpo completo.
        :param confirmed: confirmación explícita (requerida por ser destructivo).
        :return: dict con ``path`` y ``updated`` (True).
        :raises ConflictError: si ``confirmed`` es False.
        :raises NotFoundError: si la nota no existe.
        """
        target = self._resolve_note(name_or_path)
        if not confirmed:
            raise ConflictError(
                "Reemplazar el cuerpo de una nota es destructivo; use --yes o --dry-run."
            )
        fm, _old = frontmatter.parse(self._read(target))
        self._atomic_write(target, frontmatter.dump(fm, new_body))
        return {"path": self._relpath(target), "updated": True}

    # --- Búsqueda ------------------------------------------------------------

    def search(
        self,
        *,
        text: str | None = None,
        tag: str | None = None,
        links_to: str | None = None,
        folder: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        """Busca notas por texto, tag o backlinks, con filtro de carpeta y tope de resultados.

        Los criterios son AND: una nota debe cumplir todos los que se pasen.

        :param text: subcadena a buscar en título/frontmatter/cuerpo (case-insensitive).
        :param tag: tag exacto (sin ``#``) que la nota debe tener.
        :param links_to: nombre de nota a la que deben enlazar (backlinks).
        :param folder: acota a notas bajo esta carpeta relativa.
        :param limit: máximo de resultados; si hay más, marca ``truncated``.
        :return: dict con ``results`` (lista), ``count`` y opcional ``truncated``.
        """
        index = self._load_index()
        backlink_set = set(index.backlinks.get(links_to, [])) if links_to else None
        needle = text.lower() if text else None

        matches: list[dict[str, Any]] = []
        for path in self._iter_notes():
            name = self._note_name(path)
            if folder and not self._relpath(path).startswith(folder.rstrip("/") + "/"):
                continue
            if backlink_set is not None and name not in backlink_set:
                continue
            if tag and tag not in index.tags.get(name, set()):
                continue
            content = self._read(path)
            if needle is not None and needle not in content.lower():
                continue
            matches.append(self._search_hit(path, name, content, needle))

        matches.sort(key=lambda hit: hit["path"])
        result: dict[str, Any] = {"results": matches[:limit], "count": min(len(matches), limit)}
        if len(matches) > limit:
            result["truncated"] = True
            result["total_matches"] = len(matches)
        return result

    def _search_hit(self, path: Path, name: str, content: str, needle: str | None) -> dict[str, Any]:
        """Construye un resultado de búsqueda con fragmento de contexto si aplica."""
        fm, body = frontmatter.parse(content) if content.startswith("---") else ({}, content)
        hit: dict[str, Any] = {
            "name": name,
            "path": self._relpath(path),
            "title": fm.get("title", name),
        }
        if needle is not None:
            hit["snippet"] = self._snippet(body or content, needle)
        return hit

    @staticmethod
    def _snippet(text: str, needle: str, radius: int = 60) -> str:
        """Devuelve un fragmento alrededor de la primera coincidencia de ``needle``."""
        lowered = text.lower()
        idx = lowered.find(needle)
        if idx == -1:
            return text[: radius * 2].strip()
        start = max(0, idx - radius)
        end = min(len(text), idx + len(needle) + radius)
        fragment = text[start:end].replace("\n", " ").strip()
        prefix = "…" if start > 0 else ""
        suffix = "…" if end < len(text) else ""
        return f"{prefix}{fragment}{suffix}"

    # --- Grafo: backlinks, outlinks, huérfanas -------------------------------

    def backlinks(self, name_or_path: str) -> dict[str, Any]:
        """Devuelve las notas que enlazan a la nota indicada.

        :param name_or_path: nombre de nota o ruta relativa.
        :return: dict con ``note`` y ``backlinks`` (lista de nombres).
        :raises NotFoundError: si la nota no existe.
        """
        target = self._resolve_note(name_or_path)
        name = self._note_name(target)
        index = self._load_index()
        return {"note": name, "backlinks": sorted(index.backlinks.get(name, []))}

    def outlinks(self, name_or_path: str) -> dict[str, Any]:
        """Devuelve los wikilinks salientes de una nota, separando los rotos.

        :param name_or_path: nombre de nota o ruta relativa.
        :return: dict con ``note``, ``outlinks`` (existentes) y ``broken`` (no resueltos).
        :raises NotFoundError: si la nota no existe.
        """
        target = self._resolve_note(name_or_path)
        name = self._note_name(target)
        index = self._load_index()
        return {
            "note": name,
            "outlinks": sorted(index.outlinks.get(name, [])),
            "broken": sorted(index.broken.get(name, [])),
        }

    def orphans(self) -> dict[str, Any]:
        """Devuelve las notas sin backlinks entrantes ni wikilinks salientes.

        :return: dict con ``orphans`` (lista de nombres) y ``count``.
        """
        index = self._load_index()
        result = mi.orphans(index)
        return {"orphans": result, "count": len(result)}

    # --- Proyectos -----------------------------------------------------------

    def project_create(
        self, name: str, *, tags: list[str] | None = None, status: str = "activo"
    ) -> dict[str, Any]:
        """Crea la nota de contexto de un proyecto (idempotente).

        :param name: nombre legible del proyecto.
        :param tags: tags adicionales para el frontmatter.
        :param status: estado inicial del proyecto (frontmatter ``estado``).
        :return: dict con ``project``, ``path`` y ``created`` (bool).
        """
        slug = slugify(name)
        rel = self._project_context_relpath(name)
        target = self._safe_path(rel)
        if target.exists():
            return {"project": slug, "path": self._relpath(target), "created": False}
        fm: dict[str, Any] = {
            "title": f"Contexto — {name}",
            "tags": ["proyecto"] + (tags or []),
            "estado": status,
            "created": self._today(),
        }
        body = (
            f"# Contexto — {name}\n\n"
            "## Resumen\n\n"
            "## Decisiones\n\n"
            "## Enlaces\n\n"
            "## Pendientes\n"
        )
        self._atomic_write(target, frontmatter.dump(fm, body))
        logger.info("proyecto creado slug=%s", slug)
        return {"project": slug, "path": self._relpath(target), "created": True}

    def project_note(self, name: str, text: str, *, section: str = "Resumen") -> dict[str, Any]:
        """Añade una entrada fechada a una sección del contexto de un proyecto.

        :param name: nombre o slug del proyecto.
        :param text: contenido de la entrada.
        :param section: sección destino (``Resumen``/``Decisiones``/``Enlaces``/``Pendientes``).
        :return: dict con ``project``, ``path`` y ``section``.
        :raises NotFoundError: si el proyecto no existe.
        """
        target = self._safe_path(self._project_context_relpath(name))
        if not target.exists():
            raise NotFoundError(
                f"El proyecto {name!r} no existe; créelo con `project create`."
            )
        fm, body = frontmatter.parse(self._read(target))
        entry = f"- {self._now_iso()} {text}"
        body = self._append_to_section(body, section, entry)
        self._atomic_write(target, frontmatter.dump(fm, body))
        return {"project": slugify(name), "path": self._relpath(target), "section": section}

    def project_list(self) -> dict[str, Any]:
        """Lista los proyectos con su estado (leído del frontmatter del contexto).

        :return: dict con ``projects`` (lista de ``{project, path, estado, title}``) y ``count``.
        """
        projects: list[dict[str, Any]] = []
        projects_root = self._safe_path(PROJECTS_DIR)
        if projects_root.exists():
            for context in sorted(projects_root.glob("*/_contexto-*.md")):
                fm, _body = frontmatter.parse(self._read(context))
                projects.append({
                    "project": context.parent.name,
                    "path": self._relpath(context),
                    "estado": fm.get("estado", "desconocido"),
                    "title": fm.get("title", context.stem),
                })
        return {"projects": projects, "count": len(projects)}

    # --- Papelera (reversible, sin borrado permanente) -----------------------

    def trash(self, name_or_path: str, *, confirmed: bool = False) -> dict[str, Any]:
        """Mueve una nota a ``.trash/`` (reversible). No hay borrado permanente.

        :param name_or_path: nombre de nota o ruta relativa.
        :param confirmed: confirmación explícita (operación destructiva).
        :return: dict con ``trashed`` (ruta en papelera) y ``original``.
        :raises ConflictError: si ``confirmed`` es False.
        :raises NotFoundError: si la nota no existe.
        """
        target = self._resolve_note(name_or_path)
        if not confirmed:
            raise ConflictError("Enviar a la papelera es destructivo; use --yes o --dry-run.")
        original_rel = self._relpath(target)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        trash_rel = f"{TRASH_DIR}/{stamp}__{target.name}"
        dest = self._safe_path(trash_rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.replace(target, dest)
        logger.info("nota enviada a papelera name=%s", target.stem)
        return {"trashed": trash_rel, "original": original_rel}

    def restore(self, trash_name: str, *, dest_folder: str = INBOX_DIR) -> dict[str, Any]:
        """Restaura una nota desde ``.trash/`` a una carpeta del vault.

        :param trash_name: nombre del archivo en ``.trash/`` (con o sin el prefijo de timestamp).
        :param dest_folder: carpeta destino de la restauración (default ``inbox``).
        :return: dict con ``restored`` (ruta destino) y ``from`` (ruta en papelera).
        :raises NotFoundError: si el archivo no está en la papelera.
        """
        trash_file = self._safe_path(f"{TRASH_DIR}/{trash_name}")
        if not trash_file.exists():
            raise NotFoundError(f"No hay en la papelera: {trash_name!r}")
        # Quita el prefijo de timestamp ``YYYYMMDD-HHMMSS__`` si está presente.
        original_name = trash_file.name.split("__", 1)[-1]
        dest = self._safe_path(f"{dest_folder}/{original_name}")
        base_slug = dest.stem
        if dest.exists():
            unique = self._unique_slug(dest_folder, base_slug)
            dest = self._safe_path(f"{dest_folder}/{unique}.md")
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.replace(trash_file, dest)
        return {"restored": self._relpath(dest), "from": f"{TRASH_DIR}/{trash_name}"}

    # --- Daily note (día a día) ----------------------------------------------

    def daily(self, *, day: date | None = None) -> dict[str, Any]:
        """Crea o abre la daily note del día indicado con secciones base (no sobrescribe).

        :param day: fecha de la daily; por defecto hoy.
        :return: dict con ``path``, ``name`` y ``created`` (bool).
        """
        day = day or self._today()
        rel = f"{DAILY_DIR}/{day.isoformat()}.md"
        target = self._safe_path(rel)
        if target.exists():
            return {"path": self._relpath(target), "name": day.isoformat(), "created": False}
        fm = {"title": day.isoformat(), "tags": ["daily"], "created": day}
        body = "# " + day.isoformat() + "\n\n## Trabajado\n\n## Pendientes\n\n## Notas\n"
        self._atomic_write(target, frontmatter.dump(fm, body))
        return {"path": self._relpath(target), "name": day.isoformat(), "created": True}

    def daily_add(
        self, text: str, *, day: date | None = None, project: str | None = None
    ) -> dict[str, Any]:
        """Añade una entrada con timestamp a la sección "Trabajado" de la daily note.

        :param text: descripción de lo trabajado.
        :param day: fecha; por defecto hoy.
        :param project: slug de proyecto a enlazar en la entrada.
        :return: dict con ``path`` y ``added`` (True).
        """
        day = day or self._today()
        self.daily(day=day)  # asegura que exista
        rel = f"{DAILY_DIR}/{day.isoformat()}.md"
        target = self._safe_path(rel)
        fm, body = frontmatter.parse(self._read(target))
        stamp = datetime.now().strftime("%H:%M")
        suffix = f" [[{self._project_context_name(project)}]]" if project else ""
        entry = f"- {stamp} {text}{suffix}"
        body = self._append_to_section(body, "Trabajado", entry)
        self._atomic_write(target, frontmatter.dump(fm, body))
        return {"path": self._relpath(target), "added": True}

    # --- Tareas / pendientes -------------------------------------------------

    def task_add(self, text: str, *, project: str | None = None) -> dict[str, Any]:
        """Registra una tarea como checkbox en el proyecto indicado o en pendientes globales.

        :param text: descripción de la tarea.
        :param project: slug de proyecto; si falta, va a ``pendientes.md``.
        :return: dict con ``path`` y ``added`` (True).
        """
        line = f"- [ ] {text}"
        if project:
            rel = self._project_context_relpath(project)
            target = self._safe_path(rel)
            if not target.exists():
                raise NotFoundError(
                    f"El proyecto {project!r} no existe; créelo con `project create`."
                )
            fm, body = frontmatter.parse(self._read(target))
            body = self._append_to_section(body, "Pendientes", line)
            self._atomic_write(target, frontmatter.dump(fm, body))
            return {"path": self._relpath(target), "added": True}
        target = self._safe_path(GLOBAL_TASKS_NOTE)
        fm, body = frontmatter.parse(self._read(target))
        body = body.rstrip("\n") + "\n" + line + "\n"
        self._atomic_write(target, frontmatter.dump(fm, body))
        return {"path": self._relpath(target), "added": True}

    def task_list(self, *, project: str | None = None, include_done: bool = False) -> dict[str, Any]:
        """Recolecta las tareas del vault (checkboxes) con su nota y proyecto de origen.

        :param project: filtra a las tareas de un proyecto (por su carpeta).
        :param include_done: si ``True``, incluye tareas cerradas ``- [x]``.
        :return: dict con ``tasks`` (lista) y ``count``.
        """
        tasks: list[dict[str, Any]] = []
        for path in self._iter_notes():
            rel = self._relpath(path)
            note_project = self._project_of_path(rel)
            if project and note_project != slugify(project):
                continue
            for lineno, line in enumerate(self._read(path).split("\n"), start=1):
                parsed = _parse_task_line(line)
                if parsed is None:
                    continue
                done, task_text = parsed
                if done and not include_done:
                    continue
                tasks.append({
                    "text": task_text,
                    "done": done,
                    "note": self._note_name(path),
                    "path": rel,
                    "line": lineno,
                    "project": note_project,
                })
        return {"tasks": tasks, "count": len(tasks)}

    def task_done(self, text: str, *, project: str | None = None) -> dict[str, Any]:
        """Marca como completada la primera tarea abierta cuyo texto coincida.

        :param text: texto (o subcadena) de la tarea a cerrar.
        :param project: acota la búsqueda a un proyecto.
        :return: dict con ``path``, ``line`` y ``done`` (True).
        :raises NotFoundError: si no se encuentra una tarea abierta que coincida.
        """
        for path in self._iter_notes():
            rel = self._relpath(path)
            if project and self._project_of_path(rel) != slugify(project):
                continue
            lines = self._read(path).split("\n")
            changed = False
            for i, line in enumerate(lines):
                parsed = _parse_task_line(line)
                if parsed is None:
                    continue
                done, task_text = parsed
                if not done and text in task_text:
                    lines[i] = line.replace("- [ ]", "- [x]", 1)
                    changed = True
                    break
            if changed:
                fm, body = frontmatter.parse("\n".join(lines))
                self._atomic_write(path, frontmatter.dump(fm, body))
                return {"path": rel, "line": i + 1, "done": True}
        raise NotFoundError(f"No se encontró una tarea abierta que coincida con: {text!r}")

    def _project_of_path(self, rel: str) -> str | None:
        """Devuelve el slug de proyecto si la ruta relativa vive bajo ``proyectos/<slug>/``."""
        parts = rel.split("/")
        if len(parts) >= 2 and parts[0] == PROJECTS_DIR:
            return parts[1]
        return None

    # --- Ingesta de material externo -----------------------------------------

    def ingest(
        self,
        *,
        source_path: str | None = None,
        stdin_text: str | None = None,
        title: str | None = None,
        folder: str = INBOX_DIR,
        tags: list[str] | None = None,
        project: str | None = None,
        links: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Ingiere material externo (archivo o texto) como nota del vault.

        Agnóstico del origen: recibe un archivo ya presente en disco o texto por stdin. El
        material Markdown/texto se convierte en nota; el binario se copia a adjuntos y se crea
        una nota-índice que lo enlaza.

        :param source_path: ruta local del archivo a ingerir (excluyente con ``stdin_text``).
        :param stdin_text: texto a ingerir cuando no proviene de un archivo.
        :param title: título de la nota; si falta, se deriva del nombre de archivo.
        :param folder: carpeta destino de la nota (default ``inbox``).
        :param tags: tags para el frontmatter.
        :param project: slug de proyecto al que asociar y enlazar la nota.
        :param links: nombres/slugs de notas a enlazar (wikilinks) desde la nota creada.
        :param dry_run: si ``True``, reporta el plan sin escribir.
        :return: dict describiendo la nota creada (o el plan en dry-run).
        :raises ValueError: si no se indica ni ``source_path`` ni ``stdin_text``.
        """
        if not source_path and stdin_text is None:
            raise ValueError("Indique un archivo (source_path) o texto por stdin.")

        if source_path is not None:
            return self._ingest_file(
                source_path, title, folder, tags, project, links, dry_run
            )
        return self._ingest_text(
            stdin_text or "", title or "captura", folder, tags, project, links, "stdin", dry_run
        )

    def _ingest_file(self, source_path, title, folder, tags, project, links, dry_run):
        """Ingiere un archivo local: texto/markdown como nota; binario como adjunto + nota-índice."""
        src = Path(source_path).expanduser()
        if not src.exists() or not src.is_file():
            raise NotFoundError(f"Archivo a ingerir no encontrado: {source_path}")
        effective_title = title or src.stem
        # Ciertos formatos son texto (XML/SVG) pero deben ir como adjunto, no como cuerpo de nota.
        force_attachment = src.suffix.lower() in ATTACHMENT_EXTENSIONS
        if self._is_text_file(src) and not force_attachment:
            content = src.read_text(encoding="utf-8", errors="replace")
            return self._ingest_text(
                content, effective_title, folder, tags, project, links, str(src), dry_run,
                is_markdown=src.suffix.lower() in (".md", ".markdown"),
            )
        return self._ingest_binary(src, effective_title, folder, tags, project, links, dry_run)

    def _ingest_text(
        self, content, title, folder, tags, project, links, source, dry_run, *, is_markdown=False
    ):
        """Crea una nota a partir de texto, fusionando frontmatter existente si es Markdown."""
        existing_fm: dict[str, Any] = {}
        body = content
        if is_markdown and content.startswith("---"):
            existing_fm, body = frontmatter.parse(content)

        generated_fm: dict[str, Any] = {
            "title": title,
            "created": self._today(),
            "source": source,
            "ingested": self._now_iso(),
        }
        if tags:
            generated_fm["tags"] = list(tags)
        fm = frontmatter.merge(existing_fm, generated_fm)

        if dry_run:
            return {
                "dry_run": True,
                "action": "ingest_text",
                "title": title,
                "folder": folder,
                "source": source,
            }
        # create_note se encarga de los wikilinks (project/links) y de enlazar el contexto.
        result = self.create_note(
            title, body=body, folder=folder,
            tags=fm.get("tags"), aliases=None, project=project, links=links,
            extra_frontmatter={
                k: v for k, v in fm.items() if k not in ("title", "created", "tags")
            },
        )
        result["source"] = source
        return result

    def _ingest_binary(self, src: Path, title, folder, tags, project, links, dry_run):
        """Copia un binario a adjuntos y crea una nota-índice que lo referencia (embed)."""
        attachment_rel = f"{ATTACHMENTS_DIR}/{src.name}"
        if dry_run:
            return {
                "dry_run": True,
                "action": "ingest_binary",
                "attachment": attachment_rel,
                "title": title,
            }
        dest = self._safe_path(attachment_rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())

        embed = f"![[{src.name}]]"
        body = f"Adjunto ingerido desde `{src.name}`.\n\n{embed}\n"
        result = self.create_note(
            title, body=body, folder=folder, tags=tags, project=project, links=links,
            extra_frontmatter={"source": str(src), "attachment": attachment_rel,
                               "ingested": self._now_iso()},
        )
        result["attachment"] = attachment_rel
        return result

    def _with_links(self, body: str, *, project: str | None, links: list[str] | None) -> str:
        """Añade una sección de enlaces (wikilinks) al final del cuerpo, si hay enlaces."""
        wikilinks: list[str] = []
        if project:
            wikilinks.append(f"[[{self._project_context_name(project)}]]")
        for link in links or []:
            wikilinks.append(f"[[{link}]]")
        if not wikilinks:
            return body
        section = "\n\n## Enlaces\n" + "\n".join(f"- {link}" for link in wikilinks) + "\n"
        return body.rstrip("\n") + "\n" + section

    @staticmethod
    def _is_text_file(path: Path, sample_size: int = 8192) -> bool:
        """Heurística: un archivo es texto si su muestra decodifica UTF-8 y no tiene bytes nulos."""
        try:
            chunk = path.read_bytes()[:sample_size]
        except OSError:
            return False
        if b"\x00" in chunk:
            return False
        try:
            chunk.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False

    # --- Primitivas de seguridad y E/S ---------------------------------------

    def _relpath(self, target: Path) -> str:
        """Ruta relativa de un archivo respecto de la raíz del vault (posix)."""
        return target.resolve().relative_to(self._vault_real).as_posix()

    @staticmethod
    def _project_context_name(project: str) -> str:
        """Nombre de nota (stem) del contexto de un proyecto. Estable para wikilinks."""
        return f"_contexto-{slugify(project)}"

    def _project_context_relpath(self, project: str) -> str:
        """Ruta relativa de la nota de contexto de un proyecto dentro del vault."""
        slug = slugify(project)
        return f"{PROJECTS_DIR}/{slug}/{self._project_context_name(project)}.md"

    def _link_project(self, project: str | None, note_name: str) -> None:
        """Registra en el contexto del proyecto un wikilink a la nota indicada, si el contexto existe.

        No crea el proyecto: si el contexto no existe todavía, no hace nada (la nota ya quedó
        enlazada desde su propio cuerpo hacia el contexto vía ``_with_links``).
        """
        if not project:
            return
        try:
            context = self._safe_path(self._project_context_relpath(project))
        except UnsafePathError:
            return
        if not context.exists():
            return
        fm, body = frontmatter.parse(self._read(context))
        wikilink = f"- [[{note_name}]]"
        if wikilink in body:
            return
        body = self._append_to_section(body, "Enlaces", wikilink)
        self._atomic_write(context, frontmatter.dump(fm, body))

    @staticmethod
    def _append_to_section(body: str, section: str, line: str) -> str:
        """Añade ``line`` bajo el encabezado ``## <section>``; si no existe, lo crea al final."""
        heading = f"## {section}"
        lines = body.split("\n")
        if heading in lines:
            insert_at = lines.index(heading) + 1
            # Insertar tras el heading (y tras líneas en blanco iniciales de la sección).
            while insert_at < len(lines) and lines[insert_at].strip() == "":
                insert_at += 1
            lines.insert(insert_at, line)
            result = "\n".join(lines)
            return result if result.endswith("\n") else result + "\n"
        suffix = "" if body.endswith("\n") else "\n"
        return f"{body}{suffix}\n{heading}\n{line}\n"

    def _resolve_note(self, name_or_path: str) -> Path:
        """Resuelve un nombre de nota o ruta relativa a un archivo ``.md`` existente.

        :param name_or_path: nombre de nota (``Mi nota``), slug, o ruta relativa ``inbox/x.md``.
        :return: ruta absoluta del archivo dentro del vault.
        :raises NotFoundError: si no se encuentra la nota.
        """
        # 1) Ruta relativa directa (con o sin extensión).
        candidate_rel = name_or_path if name_or_path.endswith(".md") else f"{name_or_path}.md"
        try:
            direct = self._safe_path(candidate_rel)
            if direct.exists():
                return direct
        except UnsafePathError:
            pass
        # 2) Búsqueda por nombre de nota (stem) en todo el vault.
        for path in self._iter_notes():
            if self._note_name(path) == name_or_path:
                return path
        raise NotFoundError(f"Nota no encontrada: {name_or_path!r}")

    def _safe_path(self, relative: str) -> Path:
        """Resuelve una ruta relativa dentro del vault y valida que no lo escape.

        :param relative: ruta relativa (p. ej. ``inbox/nota.md``).
        :return: ruta absoluta canónica dentro del vault.
        :raises UnsafePathError: si la ruta resuelta cae fuera del vault.
        """
        if os.path.isabs(relative):
            raise UnsafePathError(f"No se permiten rutas absolutas: {relative!r}")
        candidate = (self._vault_real / relative).resolve()
        vault_str = str(self._vault_real)
        candidate_str = str(candidate)
        if candidate_str != vault_str and not candidate_str.startswith(vault_str + os.sep):
            raise UnsafePathError(f"Ruta fuera del vault: {relative!r}")
        return candidate

    def _atomic_write(self, target: Path, text: str) -> None:
        """Escribe texto de forma atómica (temporal + ``os.replace``), UTF-8, LF.

        :param target: ruta absoluta dentro del vault.
        :param text: contenido a escribir.
        """
        target.parent.mkdir(parents=True, exist_ok=True)
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(normalized, encoding="utf-8")
        os.replace(tmp, target)

    def _read(self, target: Path) -> str:
        """Lee un archivo de texto del vault en UTF-8."""
        return target.read_text(encoding="utf-8")

    def _write_if_absent(self, relative: str, text: str) -> bool:
        """Escribe ``text`` en ``relative`` solo si el archivo no existe todavía.

        :param relative: ruta relativa dentro del vault.
        :param text: contenido a escribir.
        :return: ``True`` si escribió, ``False`` si ya existía.
        """
        target = self._safe_path(relative)
        if target.exists():
            return False
        self._atomic_write(target, text)
        return True

    def _unique_slug(self, folder: str, base_slug: str) -> str:
        """Devuelve un slug único en ``folder`` añadiendo sufijo ``-2``, ``-3``… si colisiona.

        :param folder: carpeta relativa donde vivirá la nota.
        :param base_slug: slug base derivado del título.
        :return: slug garantizado sin colisión de archivo ``.md``.
        """
        candidate = base_slug
        counter = 2
        while self._safe_path(f"{folder}/{candidate}.md").exists():
            candidate = f"{base_slug}-{counter}"
            counter += 1
        return candidate

    def _iter_notes(self) -> list[Path]:
        """Lista todas las notas ``.md`` del vault, excluyendo ``.trash/`` y ``.brain/``."""
        notes: list[Path] = []
        for path in self._vault_real.rglob("*.md"):
            rel = path.relative_to(self._vault_real)
            top = rel.parts[0] if rel.parts else ""
            if top in (TRASH_DIR, BRAIN_DIR):
                continue
            notes.append(path)
        return notes

    def _note_name(self, path: Path) -> str:
        """Nombre de nota (stem del archivo) usado como identidad para wikilinks."""
        return path.stem

    def _load_index(self) -> mi.Index:
        """Construye el índice de enlaces/tags de todo el vault."""
        notes: dict[str, str] = {}
        for path in self._iter_notes():
            notes[self._note_name(path)] = self._read(path)
        return mi.build_index(notes)

    @staticmethod
    def _now_iso() -> str:
        """Timestamp local ISO (segundos) para entradas fechadas."""
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _today() -> date:
        """Fecha local de hoy."""
        return date.today()


# --- Contenido base de plantillas del vault ----------------------------------

_INDEX_TEMPLATE = """---
title: Índice del Second Brain
tags: [moc]
---
# Índice — Second Brain

Mapa de contenido (MOC) del vault. Punto de entrada al conocimiento.

## Áreas
- [[pendientes]] — tareas abiertas del vault.

## Proyectos
_Los proyectos viven en `proyectos/<slug>/_contexto.md`._

## Captura
- `inbox/` — notas sin clasificar.
- `daily/` — bitácora diaria.
- `referencias/` — material ingerido y adjuntos.
"""

_GLOBAL_TASKS_TEMPLATE = """---
title: Pendientes
tags: [pendientes]
---
# Pendientes globales

Tareas que no pertenecen a un proyecto concreto.
"""

_SOURCES_TEMPLATE = """{
  "sources": []
}
"""

_OBSIDIAN_APP_JSON = "{}\n"


def init_vault(vault_path: str | os.PathLike[str]) -> dict[str, Any]:
    """Inicializa (o reconoce) un vault de second brain en ``vault_path``.

    Idempotente: si ya está inicializado, no sobrescribe y reporta el estado.

    :param vault_path: ruta destino del vault.
    :return: dict con ``path``, ``created`` (bool) y ``already_initialized`` (bool).
    """
    root = Path(vault_path).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    client = VaultClient(root, require_exists=False)

    if client.is_initialized():
        return {
            "path": str(client.path),
            "created": False,
            "already_initialized": True,
        }

    for rel in BASE_DIRS:
        client._safe_path(rel).mkdir(parents=True, exist_ok=True)

    # Archivos base: no sobrescribir si el usuario ya los tenía.
    client._write_if_absent(INDEX_NOTE, _INDEX_TEMPLATE)
    client._write_if_absent(GLOBAL_TASKS_NOTE, _GLOBAL_TASKS_TEMPLATE)
    client._write_if_absent(SOURCES_FILE, _SOURCES_TEMPLATE)
    # ``app.json`` mínimo para que Obsidian reconozca el vault, sin pisar config existente.
    client._write_if_absent(".obsidian/app.json", _OBSIDIAN_APP_JSON)

    return {
        "path": str(client.path),
        "created": True,
        "already_initialized": False,
    }


# Checkbox Markdown de tarea: "- [ ] texto" (abierta) o "- [x] texto" (cerrada).
_TASK_RE = re.compile(r"^\s*-\s*\[( |x|X)\]\s*(.*)$")


def _parse_task_line(line: str) -> tuple[bool, str] | None:
    """Parsea una línea de checkbox Markdown.

    :param line: línea del cuerpo de una nota.
    :return: ``(done, texto)`` si es una tarea; ``None`` si no lo es.
    """
    match = _TASK_RE.match(line)
    if not match:
        return None
    done = match.group(1).lower() == "x"
    return done, match.group(2).strip()
