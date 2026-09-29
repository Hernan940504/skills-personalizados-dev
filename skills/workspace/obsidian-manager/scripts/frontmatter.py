"""Parseo y serialización de frontmatter YAML mínimo para notas de Obsidian.

Una nota de Obsidian puede empezar con un bloque de frontmatter YAML delimitado por ``---``:

    ---
    title: Mi nota
    tags: [proyecto, ciencuadras]
    created: 2026-09-28
    ---
    Cuerpo de la nota...

Este módulo implementa un subconjunto de YAML **sin dependencias externas** (solo stdlib),
suficiente para el frontmatter que genera y consume este skill. Cumple RNF-1 del spec.

Subconjunto soportado:

- Pares ``clave: valor`` con escalares: str, int, float, bool y fecha ISO (``YYYY-MM-DD``).
- Listas inline: ``tags: [a, b, c]``.
- Listas en bloque:

    tags:
      - a
      - b

Explícitamente NO soportado (se falla claro en vez de corromper): mapas anidados, anclas/alias
YAML, multilínea con ``|``/``>``, y claves duplicadas. Ante estos casos se levanta
``FrontmatterError``.
"""

from __future__ import annotations

from datetime import date
from typing import Any

FRONTMATTER_DELIMITER = "---"


class FrontmatterError(ValueError):
    """El frontmatter contiene YAML fuera del subconjunto soportado."""


def parse(text: str) -> tuple[dict[str, Any], str]:
    """Separa el frontmatter YAML del cuerpo de una nota.

    :param text: contenido completo de la nota.
    :return: tupla ``(frontmatter, body)``. Si no hay frontmatter, ``({}, text)``.
    :raises FrontmatterError: si el bloque frontmatter usa YAML no soportado.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith(FRONTMATTER_DELIMITER + "\n") and normalized != FRONTMATTER_DELIMITER:
        return {}, text

    lines = normalized.split("\n")
    # La primera línea es el delimitador de apertura; buscar el de cierre.
    closing_index = _find_closing_delimiter(lines)
    if closing_index is None:
        # No hay cierre: no es un frontmatter válido, se trata todo como cuerpo.
        return {}, text

    fm_lines = lines[1:closing_index]
    body_lines = lines[closing_index + 1:]
    frontmatter = _parse_block(fm_lines)
    # El cuerpo conserva su contenido; se quita a lo sumo un salto de línea inicial.
    body = "\n".join(body_lines)
    if body.startswith("\n"):
        body = body[1:]
    return frontmatter, body


def dump(frontmatter: dict[str, Any], body: str) -> str:
    """Serializa frontmatter + cuerpo a una nota Markdown.

    :param frontmatter: mapping de campos del frontmatter (puede estar vacío).
    :param body: cuerpo Markdown de la nota.
    :return: texto de la nota. Si el frontmatter está vacío, devuelve solo el cuerpo.
    """
    if not frontmatter:
        return body
    rendered = [FRONTMATTER_DELIMITER]
    for key, value in frontmatter.items():
        rendered.append(_render_field(key, value))
    rendered.append(FRONTMATTER_DELIMITER)
    note = "\n".join(rendered)
    if body:
        note += "\n" + body
    else:
        note += "\n"
    return note


def merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Fusiona dos frontmatters, uniendo listas de tags sin duplicar.

    Los campos de ``updates`` pisan a los de ``base``, salvo las claves de tipo lista
    (``tags``, ``aliases``), que se unen preservando orden y sin duplicados.

    :param base: frontmatter existente.
    :param updates: campos nuevos a incorporar.
    :return: un nuevo dict fusionado (no muta los argumentos).
    """
    merged: dict[str, Any] = dict(base)
    for key, value in updates.items():
        if isinstance(value, list) and isinstance(merged.get(key), list):
            merged[key] = _union_preserving_order(merged[key], value)
        else:
            merged[key] = value
    return merged


# --- Helpers internos --------------------------------------------------------


def _find_closing_delimiter(lines: list[str]) -> int | None:
    """Devuelve el índice de la línea de cierre ``---`` del frontmatter, o ``None``."""
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONTMATTER_DELIMITER:
            return index
    return None


def _parse_block(fm_lines: list[str]) -> dict[str, Any]:
    """Parsea las líneas internas del frontmatter al subconjunto soportado."""
    result: dict[str, Any] = {}
    index = 0
    while index < len(fm_lines):
        raw = fm_lines[index]
        line = raw.rstrip()
        if not line.strip():
            index += 1
            continue
        _reject_unsupported(line)
        key, sep, inline_value = line.partition(":")
        if not sep:
            raise FrontmatterError(f"Línea de frontmatter sin 'clave: valor': {line!r}")
        key = key.strip()
        if key in result:
            raise FrontmatterError(f"Clave duplicada en frontmatter: {key!r}")
        inline_value = inline_value.strip()
        if inline_value == "":
            # Puede ser una lista en bloque en las líneas siguientes.
            block_items, consumed = _consume_block_list(fm_lines, index + 1)
            if block_items is not None:
                result[key] = block_items
                index += 1 + consumed
                continue
            # Clave sin valor y sin lista: valor nulo/cadena vacía.
            result[key] = ""
            index += 1
            continue
        result[key] = _parse_scalar_or_inline_list(inline_value)
        index += 1
    return result


def _consume_block_list(fm_lines: list[str], start: int) -> tuple[list[Any] | None, int]:
    """Intenta consumir una lista en bloque (``- item``) a partir de ``start``.

    :return: ``(items, consumidas)`` si hay lista; ``(None, 0)`` si no.
    """
    items: list[Any] = []
    consumed = 0
    for index in range(start, len(fm_lines)):
        stripped = fm_lines[index].strip()
        if stripped.startswith("- "):
            items.append(_parse_scalar(stripped[2:].strip()))
            consumed += 1
        elif stripped == "-":
            items.append("")
            consumed += 1
        else:
            break
    if consumed == 0:
        return None, 0
    return items, consumed


def _reject_unsupported(line: str) -> None:
    """Levanta ``FrontmatterError`` ante construcciones YAML fuera de alcance."""
    stripped = line.strip()
    if stripped.endswith("|") or stripped.endswith(">"):
        raise FrontmatterError(
            "Frontmatter con bloque multilínea (| o >) no soportado por el parser mínimo"
        )
    if stripped.startswith("&") or stripped.startswith("*"):
        raise FrontmatterError("Anclas/alias YAML no soportados por el parser mínimo")


def _parse_scalar_or_inline_list(value: str) -> Any:
    """Parsea un valor que puede ser lista inline ``[a, b]`` o un escalar."""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item.strip()) for item in inner.split(",")]
    return _parse_scalar(value)


def _parse_scalar(token: str) -> Any:
    """Convierte un token escalar a su tipo Python (bool, int, float, fecha, str)."""
    token = _strip_quotes(token.strip())
    if token == "":
        return ""
    lowered = token.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "~"):
        return None
    parsed_date = _try_parse_iso_date(token)
    if parsed_date is not None:
        return parsed_date
    parsed_int = _try_parse_int(token)
    if parsed_int is not None:
        return parsed_int
    parsed_float = _try_parse_float(token)
    if parsed_float is not None:
        return parsed_float
    return token


def _strip_quotes(token: str) -> str:
    """Quita comillas simples o dobles envolventes, si las hay."""
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        return token[1:-1]
    return token


def _try_parse_iso_date(token: str) -> date | None:
    """Devuelve un ``date`` si el token es ``YYYY-MM-DD``, o ``None``."""
    if len(token) != 10 or token[4] != "-" or token[7] != "-":
        return None
    try:
        return date.fromisoformat(token)
    except ValueError:
        return None


def _try_parse_int(token: str) -> int | None:
    """Devuelve un ``int`` si el token es entero, o ``None``."""
    try:
        if token.lstrip("-").isdigit():
            return int(token)
    except ValueError:
        return None
    return None


def _try_parse_float(token: str) -> float | None:
    """Devuelve un ``float`` si el token es decimal, o ``None``."""
    try:
        return float(token)
    except ValueError:
        return None


def _union_preserving_order(base: list[Any], extra: list[Any]) -> list[Any]:
    """Une dos listas preservando el orden y sin duplicados."""
    result = list(base)
    for item in extra:
        if item not in result:
            result.append(item)
    return result


def _render_field(key: str, value: Any) -> str:
    """Serializa un par clave/valor del frontmatter a una línea YAML."""
    if isinstance(value, list):
        rendered_items = ", ".join(_render_scalar(item) for item in value)
        return f"{key}: [{rendered_items}]"
    return f"{key}: {_render_scalar(value)}"


def _render_scalar(value: Any) -> str:
    """Serializa un escalar a su representación YAML."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, date):
        return value.isoformat()
    return str(value)
