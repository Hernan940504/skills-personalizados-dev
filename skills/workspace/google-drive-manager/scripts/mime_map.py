"""Mapeo de exportación y conversión de tipos MIME de Google Workspace.

Google Docs/Sheets/Slides/Drawings no se descargan directamente: se exportan a un
formato ofimático (docx, xlsx, pptx, pdf, csv, md). Este módulo centraliza:

- ``EXPORT_MAP``: por cada MIME Google, los formatos de export soportados y su
  ``(mime_destino, extension)``.
- ``DEFAULT_EXPORT``: formato por defecto por cada MIME Google.
- ``CONVERT_MAP``: MIME de un archivo local -> MIME Google al subir con ``--convert``.

No realiza llamadas de red ni maneja secretos.
"""

from __future__ import annotations

# MIME types nativos de Google Workspace.
GOOGLE_DOC = "application/vnd.google-apps.document"
GOOGLE_SHEET = "application/vnd.google-apps.spreadsheet"
GOOGLE_SLIDES = "application/vnd.google-apps.presentation"
GOOGLE_DRAWING = "application/vnd.google-apps.drawing"
GOOGLE_FOLDER = "application/vnd.google-apps.folder"

# MIME destino de export por formato ofimático.
_MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_MIME_PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
_MIME_PDF = "application/pdf"
_MIME_CSV = "text/csv"
_MIME_MD = "text/markdown"
_MIME_PNG = "image/png"
_MIME_SVG = "image/svg+xml"

# Por cada MIME Google: formato legible -> (mime_destino, extension).
EXPORT_MAP: dict[str, dict[str, tuple[str, str]]] = {
    GOOGLE_DOC: {
        "docx": (_MIME_DOCX, ".docx"),
        "pdf": (_MIME_PDF, ".pdf"),
        "md": (_MIME_MD, ".md"),
    },
    GOOGLE_SHEET: {
        "xlsx": (_MIME_XLSX, ".xlsx"),
        "csv": (_MIME_CSV, ".csv"),
        "pdf": (_MIME_PDF, ".pdf"),
    },
    GOOGLE_SLIDES: {
        "pptx": (_MIME_PPTX, ".pptx"),
        "pdf": (_MIME_PDF, ".pdf"),
    },
    GOOGLE_DRAWING: {
        "pdf": (_MIME_PDF, ".pdf"),
        "png": (_MIME_PNG, ".png"),
        "svg": (_MIME_SVG, ".svg"),
    },
}

# Formato por defecto por tipo Google cuando el usuario no especifica ``--export``.
DEFAULT_EXPORT: dict[str, str] = {
    GOOGLE_DOC: "docx",
    GOOGLE_SHEET: "xlsx",
    GOOGLE_SLIDES: "pptx",
    GOOGLE_DRAWING: "pdf",
}

# MIME local -> MIME Google al subir con conversión (``--convert``).
CONVERT_MAP: dict[str, str] = {
    _MIME_DOCX: GOOGLE_DOC,
    "application/msword": GOOGLE_DOC,
    _MIME_XLSX: GOOGLE_SHEET,
    "application/vnd.ms-excel": GOOGLE_SHEET,
    _MIME_CSV: GOOGLE_SHEET,
    _MIME_PPTX: GOOGLE_SLIDES,
    "application/vnd.ms-powerpoint": GOOGLE_SLIDES,
    "text/plain": GOOGLE_DOC,
}


class UnsupportedExportFormatError(ValueError):
    """El formato de export pedido no aplica al tipo Google indicado."""


def is_google_native(mime_type: str) -> bool:
    """Indica si un MIME corresponde a un tipo nativo de Google Workspace.

    :param mime_type: MIME del archivo en Drive.
    :return: ``True`` si requiere export en lugar de descarga directa.
    """
    return mime_type.startswith("application/vnd.google-apps")


def is_folder(mime_type: str) -> bool:
    """Indica si un MIME corresponde a una carpeta de Drive.

    :param mime_type: MIME del archivo en Drive.
    :return: ``True`` si es carpeta.
    """
    return mime_type == GOOGLE_FOLDER


def default_export(google_mime: str) -> str:
    """Devuelve el formato de export por defecto para un MIME Google.

    :param google_mime: MIME nativo de Google Workspace.
    :return: nombre del formato por defecto (p. ej. ``docx``).
    :raises UnsupportedExportFormatError: si el tipo no tiene default definido.
    """
    fmt = DEFAULT_EXPORT.get(google_mime)
    if fmt is None:
        raise UnsupportedExportFormatError(
            f"No hay formato de export por defecto para el tipo {google_mime}"
        )
    return fmt


def resolve_export(google_mime: str, fmt: str | None) -> tuple[str, str]:
    """Resuelve el ``(mime_destino, extension)`` para exportar un tipo Google.

    :param google_mime: MIME nativo de Google Workspace.
    :param fmt: formato deseado; si es ``None`` se usa el default del tipo.
    :return: tupla ``(mime_destino, extension)`` para la llamada de export.
    :raises UnsupportedExportFormatError: si el tipo o el formato no se soportan.
    """
    formats = EXPORT_MAP.get(google_mime)
    if formats is None:
        raise UnsupportedExportFormatError(
            f"El tipo {google_mime} no admite export"
        )
    chosen = fmt or default_export(google_mime)
    target = formats.get(chosen)
    if target is None:
        valid = ", ".join(sorted(formats))
        raise UnsupportedExportFormatError(
            f"Formato '{chosen}' no válido para {google_mime}. Válidos: {valid}"
        )
    return target


def convert_target(source_mime: str) -> str | None:
    """Devuelve el MIME Google al que convertir un archivo local, si aplica.

    :param source_mime: MIME del archivo local a subir.
    :return: MIME Google destino, o ``None`` si no hay conversión conocida.
    """
    return CONVERT_MAP.get(source_mime)
