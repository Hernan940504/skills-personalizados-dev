"""Índice del vault: extracción de wikilinks y tags, y construcción del grafo de enlaces.

Este módulo es agnóstico del sistema de archivos: recibe el contenido de las notas ya leído
(mapa ``nombre_de_nota -> texto``) y produce un índice con:

- ``names``: conjunto de nombres de nota existentes.
- ``aliases``: ``alias -> nombre_de_nota`` (declarados en frontmatter ``aliases:``).
- ``outlinks``: ``nota -> [notas destino]`` (wikilinks salientes, resueltos por nombre/alias).
- ``backlinks``: ``nota -> [notas origen]`` (invertido de outlinks).
- ``broken``: ``nota -> [targets no resueltos]`` (wikilinks a notas inexistentes).
- ``tags``: ``nota -> set(tags)``.

Solo stdlib (``re``). Cumple RNF-1.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import frontmatter

# [[Nota]] o [[Nota|alias]] o [[Nota#seccion]]; captura el target antes de | o #.
_WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:[#\|][^\]]*)?\]\]")
# #tag inline: empieza en límite de palabra, admite letras, dígitos, _, -, / (jerárquicos).
_INLINE_TAG_RE = re.compile(r"(?<!\w)#([A-Za-z][\w/\-]*)")
# Bloques de código a ignorar para tags inline (fences ``` y code inline `...`).
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")


@dataclass
class Index:
    """Índice de enlaces y tags del vault.

    :param names: nombres de nota existentes (sin extensión).
    :param aliases: mapping alias -> nombre de nota canónico.
    :param outlinks: nota -> lista de notas destino existentes.
    :param backlinks: nota -> lista de notas que la enlazan.
    :param broken: nota -> lista de targets de wikilink no resueltos.
    :param tags: nota -> conjunto de tags.
    """

    names: set[str] = field(default_factory=set)
    aliases: dict[str, str] = field(default_factory=dict)
    outlinks: dict[str, list[str]] = field(default_factory=dict)
    backlinks: dict[str, list[str]] = field(default_factory=dict)
    broken: dict[str, list[str]] = field(default_factory=dict)
    tags: dict[str, set[str]] = field(default_factory=dict)


def extract_wikilinks(body: str) -> list[str]:
    """Extrae los targets de wikilinks de un cuerpo Markdown, preservando orden y sin duplicar.

    :param body: cuerpo de la nota.
    :return: lista de nombres/alias destino (sin sección ni alias de display).
    """
    seen: list[str] = []
    for match in _WIKILINK_RE.finditer(body):
        target = match.group(1).strip()
        if target and target not in seen:
            seen.append(target)
    return seen


def extract_tags(fm: dict[str, Any], body: str) -> set[str]:
    """Extrae los tags de una nota: los de frontmatter ``tags:`` y los inline ``#tag``.

    Los tags inline dentro de bloques de código o code inline se ignoran.

    :param fm: frontmatter ya parseado de la nota.
    :param body: cuerpo de la nota.
    :return: conjunto de tags (sin el ``#``).
    """
    tags: set[str] = set()
    fm_tags = fm.get("tags")
    if isinstance(fm_tags, list):
        tags.update(str(t).lstrip("#") for t in fm_tags if str(t).strip())
    elif isinstance(fm_tags, str) and fm_tags.strip():
        tags.add(fm_tags.strip().lstrip("#"))
    cleaned = _strip_code(body)
    for match in _INLINE_TAG_RE.finditer(cleaned):
        tags.add(match.group(1))
    return tags


def build_index(notes: dict[str, str]) -> Index:
    """Construye el índice del vault a partir de los contenidos de las notas.

    :param notes: mapping ``nombre_de_nota -> contenido completo`` (con frontmatter).
    :return: ``Index`` con enlaces, backlinks, rotos y tags.
    """
    index = Index()
    parsed: dict[str, tuple[dict[str, Any], str]] = {}

    for name, text in notes.items():
        index.names.add(name)
        try:
            fm, body = frontmatter.parse(text)
        except frontmatter.FrontmatterError:
            # Una nota con frontmatter inválido no debe romper el índice completo.
            fm, body = {}, text
        parsed[name] = (fm, body)
        for alias in _aliases_of(fm):
            index.aliases[alias] = name
        index.tags[name] = extract_tags(fm, body)

    for name, (_fm, body) in parsed.items():
        resolved: list[str] = []
        broken: list[str] = []
        for target in extract_wikilinks(body):
            canonical = resolve_link(target, index)
            if canonical is None:
                broken.append(target)
            elif canonical not in resolved:
                resolved.append(canonical)
        index.outlinks[name] = resolved
        if broken:
            index.broken[name] = broken

    _build_backlinks(index)
    return index


def resolve_link(target: str, index: Index) -> str | None:
    """Resuelve el target de un wikilink a un nombre de nota canónico.

    Intenta por nombre exacto y luego por alias declarado en frontmatter.

    :param target: texto del wikilink (nombre o alias).
    :param index: índice con nombres y aliases.
    :return: nombre canónico si existe, o ``None`` si el enlace está roto.
    """
    if target in index.names:
        return target
    if target in index.aliases:
        return index.aliases[target]
    return None


def orphans(index: Index) -> list[str]:
    """Devuelve las notas sin backlinks entrantes ni outlinks salientes.

    :param index: índice del vault.
    :return: lista ordenada de nombres de nota huérfanas.
    """
    result = []
    for name in index.names:
        has_out = bool(index.outlinks.get(name))
        has_in = bool(index.backlinks.get(name))
        if not has_out and not has_in:
            result.append(name)
    return sorted(result)


# --- Helpers internos --------------------------------------------------------


def _aliases_of(fm: dict[str, Any]) -> list[str]:
    """Devuelve la lista de aliases declarados en el frontmatter."""
    raw = fm.get("aliases")
    if isinstance(raw, list):
        return [str(a).strip() for a in raw if str(a).strip()]
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []


def _build_backlinks(index: Index) -> None:
    """Rellena ``index.backlinks`` invirtiendo ``index.outlinks``."""
    for source, targets in index.outlinks.items():
        for target in targets:
            index.backlinks.setdefault(target, [])
            if source not in index.backlinks[target]:
                index.backlinks[target].append(source)


def _strip_code(body: str) -> str:
    """Elimina bloques de código y code inline para no confundir ``#tag`` con ``#heading``.

    Nota: los encabezados Markdown (``# Título``) no coinciden con el patrón de tag inline
    porque este exige que ``#`` no esté precedido de espacio-inicio-de-línea seguido de espacio;
    aun así se limpia el código para evitar falsos positivos dentro de fences.
    """
    without_fences = _CODE_FENCE_RE.sub(" ", body)
    return _INLINE_CODE_RE.sub(" ", without_fences)
