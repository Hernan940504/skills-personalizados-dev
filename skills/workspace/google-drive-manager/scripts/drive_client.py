"""Wrapper de la Google Drive API v3.

Encapsula la lógica de negocio del skill sobre un ``service`` de la Drive API ya
autenticado (inyectado en el constructor, lo que permite testear con dobles sin red):

- ``_execute``: ejecuta una request con reintentos (backoff exponencial + jitter) ante
  429/500/503 y traduce ``HttpError`` a excepciones tipadas.
- Paginación completa, listados, descarga/export, subida, actualización y organización
  (se agregan en módulos/tareas posteriores).

Reglas transversales:

- Todas las llamadas incluyen ``supportsAllDrives=True``; los listados añaden
  ``includeItemsFromAllDrives=True`` y el ``corpora`` correspondiente.
- Nunca se registra contenido de archivos ni tokens.
- No existe borrado permanente (``files.delete``) ni vaciado de papelera.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any, Callable

logger = logging.getLogger("gdrive.client")

# Parámetros de reintat por defecto (configurables por instancia).
_DEFAULT_MAX_RETRIES = 5
_DEFAULT_BASE_DELAY = 1.0
_DEFAULT_CAP_DELAY = 32.0
_RETRYABLE_STATUS = frozenset({429, 500, 503})


class DriveClientError(RuntimeError):
    """Error base del cliente de Drive."""


class PermissionDeniedError(DriveClientError):
    """El usuario no tiene permisos suficientes sobre el recurso (403 no-quota)."""


class NotFoundError(DriveClientError):
    """El recurso solicitado no existe (404)."""


class QuotaExceededError(DriveClientError):
    """Cuota o rate limit excedido (403-quota o 429 tras agotar reintentos)."""


class ConflictError(DriveClientError):
    """Conflicto no resuelto (p. ej. nombre duplicado sin estrategia)."""


def _status_of(error: Exception) -> int | None:
    """Extrae el código HTTP de un ``HttpError`` de googleapiclient, si aplica.

    :param error: excepción capturada al ejecutar la request.
    :return: código de estado HTTP o ``None`` si no se puede determinar.
    """
    resp = getattr(error, "resp", None)
    status = getattr(resp, "status", None)
    if status is None:
        status = getattr(error, "status_code", None)
    try:
        return int(status) if status is not None else None
    except (TypeError, ValueError):
        return None


def _reason_of(error: Exception) -> str:
    """Devuelve una razón textual del error en minúsculas para clasificarlo.

    :param error: excepción capturada.
    :return: razón concatenada en minúsculas (vacía si no hay).
    """
    parts: list[str] = []
    for attr in ("reason", "_get_reason"):
        val = getattr(error, attr, None)
        if callable(val):
            try:
                val = val()
            except Exception:
                val = None
        if isinstance(val, str):
            parts.append(val)
    parts.append(str(error))
    return " ".join(parts).lower()


def _is_quota_reason(reason: str) -> bool:
    """Heurística para distinguir un 403 de cuota/rate de uno de permisos.

    :param reason: razón textual en minúsculas.
    :return: ``True`` si el 403 corresponde a límite de cuota/rate.
    """
    quota_markers = (
        "ratelimitexceeded",
        "userratelimitexceeded",
        "quotaexceeded",
        "rate limit",
        "quota",
    )
    return any(marker in reason for marker in quota_markers)


class DriveClient:
    """Cliente de alto nivel sobre un ``service`` de la Drive API v3."""

    def __init__(
        self,
        service: Any,
        *,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        base_delay: float = _DEFAULT_BASE_DELAY,
        cap_delay: float = _DEFAULT_CAP_DELAY,
        sleep: Callable[[float], None] = time.sleep,
        downloader_factory: Callable[[Any, Any], Any] | None = None,
        uploader_factory: Callable[..., Any] | None = None,
    ) -> None:
        """Inicializa el cliente.

        :param service: servicio de Drive (``googleapiclient.discovery.build`` o doble).
        :param max_retries: número máximo de reintentos ante errores transitorios.
        :param base_delay: retardo base en segundos para el backoff exponencial.
        :param cap_delay: tope del retardo en segundos.
        :param sleep: función de espera (inyectable para tests).
        :param downloader_factory: crea el descargador de media (inyectable para tests).
        :param uploader_factory: crea el ``MediaFileUpload`` de subida (inyectable para tests).
        """
        self._service = service
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._cap_delay = cap_delay
        self._sleep = sleep
        self._downloader_factory = downloader_factory or _default_downloader_factory
        self._uploader_factory = uploader_factory or _default_uploader_factory

    def _backoff_delay(self, attempt: int) -> float:
        """Calcula el retardo del intento con backoff exponencial + jitter.

        :param attempt: número de intento (0-based).
        :return: segundos a esperar antes del siguiente intento.
        """
        exp = min(self._base_delay * (2 ** attempt), self._cap_delay)
        return exp + random.uniform(0, self._base_delay)

    def _execute(self, request: Any) -> Any:
        """Ejecuta una request de la API con reintentos y errores tipados.

        :param request: objeto con método ``execute()`` (request de googleapiclient o doble).
        :return: el resultado de ``request.execute()``.
        :raises PermissionDeniedError: 403 de permisos.
        :raises NotFoundError: 404.
        :raises QuotaExceededError: 403-quota o 429 tras agotar reintentos.
        :raises DriveClientError: otros errores no recuperables.
        """
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                return request.execute()
            except Exception as exc:  # googleapiclient.errors.HttpError y afines
                status = _status_of(exc)
                reason = _reason_of(exc)
                last_error = exc

                if status in _RETRYABLE_STATUS and attempt < self._max_retries:
                    delay = self._backoff_delay(attempt)
                    logger.warning(
                        "reintento %d/%d tras status=%s en %.2fs",
                        attempt + 1,
                        self._max_retries,
                        status,
                        delay,
                    )
                    self._sleep(delay)
                    continue

                raise self._classify(status, reason, exc) from exc

        # Reintentos agotados sobre un status transitorio.
        status = _status_of(last_error) if last_error else None
        reason = _reason_of(last_error) if last_error else ""
        raise self._classify(status, reason, last_error) from last_error

    @staticmethod
    def _classify(status: int | None, reason: str, error: Exception | None) -> DriveClientError:
        """Traduce un error HTTP a la excepción tipada correspondiente.

        :param status: código HTTP.
        :param reason: razón textual en minúsculas.
        :param error: excepción original.
        :return: instancia de ``DriveClientError`` (o subclase).
        """
        if status == 404:
            return NotFoundError("Recurso no encontrado")
        if status == 429:
            return QuotaExceededError("Cuota o rate limit excedido")
        if status == 403:
            if _is_quota_reason(reason):
                return QuotaExceededError("Cuota o rate limit excedido")
            return PermissionDeniedError("Permisos insuficientes sobre el recurso")
        return DriveClientError(f"Error de la Drive API (status={status})")

# --- Campos y ámbitos --------------------------------------------------------

# Campos mínimos pedidos por archivo (evita traer payloads innecesarios).
FILE_FIELDS = "id, name, mimeType, parents, modifiedTime, owners(emailAddress), size, trashed"

# Ámbitos de búsqueda.
SCOPE_MYDRIVE = "mydrive"
SCOPE_ALL = "all"


def _escape_query_value(value: str) -> str:
    """Escapa un valor para insertarlo en el parámetro ``q`` de la Drive API.

    La Drive API usa cadenas entre comillas simples; se escapan ``\\`` y ``'`` para
    evitar romper la query o inyectar cláusulas.

    :param value: valor crudo provisto por el usuario.
    :return: valor escapado, seguro para interpolar entre comillas simples.
    """
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _build_query(
    *,
    name: str | None = None,
    name_contains: str | None = None,
    parent: str | None = None,
    mime_type: str | None = None,
    modified_after: str | None = None,
    modified_before: str | None = None,
    owner: str | None = None,
    include_trashed: bool = False,
) -> str:
    """Construye el parámetro ``q`` de búsqueda a partir de filtros discretos.

    :param name: nombre exacto.
    :param name_contains: subcadena del nombre.
    :param parent: id de carpeta padre.
    :param mime_type: tipo MIME exacto.
    :param modified_after: fecha ISO-8601 límite inferior de modificación.
    :param modified_before: fecha ISO-8601 límite superior de modificación.
    :param owner: email del propietario.
    :param include_trashed: si ``True``, incluye elementos en papelera.
    :return: cadena ``q`` lista para la API.
    """
    clauses: list[str] = []
    if name:
        clauses.append(f"name = '{_escape_query_value(name)}'")
    if name_contains:
        clauses.append(f"name contains '{_escape_query_value(name_contains)}'")
    if parent:
        clauses.append(f"'{_escape_query_value(parent)}' in parents")
    if mime_type:
        clauses.append(f"mimeType = '{_escape_query_value(mime_type)}'")
    if modified_after:
        clauses.append(f"modifiedTime >= '{_escape_query_value(modified_after)}'")
    if modified_before:
        clauses.append(f"modifiedTime <= '{_escape_query_value(modified_before)}'")
    if owner:
        clauses.append(f"'{_escape_query_value(owner)}' in owners")
    if not include_trashed:
        clauses.append("trashed = false")
    return " and ".join(clauses)


def _list_params_for_scope(scope: str, drive_id: str | None) -> dict[str, Any]:
    """Devuelve los parámetros de ámbito para un ``files.list``.

    Garantiza ``supportsAllDrives`` e ``includeItemsFromAllDrives`` y fija ``corpora``
    según el ámbito, para que la búsqueda funcione igual en Mi unidad y Shared Drives.

    :param scope: ``mydrive``, ``all`` o ignorado si se pasa ``drive_id``.
    :param drive_id: id de una Shared Drive concreta, o ``None``.
    :return: dict de parámetros para inyectar en la request.
    """
    params: dict[str, Any] = {
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
    }
    if drive_id:
        params["corpora"] = "drive"
        params["driveId"] = drive_id
    elif scope == SCOPE_MYDRIVE:
        params["corpora"] = "user"
    else:  # SCOPE_ALL
        params["corpora"] = "allDrives"
    return params


# --- Métodos de listado (se enlazan a la clase DriveClient) ------------------


def _paginate(
    self,
    list_method: Callable[..., Any],
    item_key: str,
    max_results: int | None = None,
    **params: Any,
) -> list[dict]:
    """Itera ``nextPageToken`` y concatena los items, con tope opcional de resultados.

    :param list_method: método ``.list`` del recurso (p. ej. ``service.files().list``).
    :param item_key: clave de la respuesta que contiene la lista (``files`` o ``drives``).
    :param max_results: tope de items a devolver; ``None`` = sin tope (todas las páginas).
    :param params: parámetros de la primera página; se reusa en las siguientes.
    :return: lista de items (hasta ``max_results`` si se indicó).
    """
    items: list[dict] = []
    page_token: str | None = None
    while True:
        page_params = dict(params)
        if page_token:
            page_params["pageToken"] = page_token
        response = self._execute(list_method(**page_params))
        items.extend(response.get(item_key, []))
        if max_results is not None and len(items) >= max_results:
            return items[:max_results]
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return items


def list_shared_drives(self) -> list[dict]:
    """Lista las unidades compartidas accesibles (id y nombre).

    :return: lista de ``{"id", "name"}`` de todas las Shared Drives.
    """
    return self._paginate(
        self._service.drives().list,
        "drives",
        fields="nextPageToken, drives(id, name)",
        pageSize=100,
    )


def search(
    self,
    *,
    scope: str = SCOPE_ALL,
    drive_id: str | None = None,
    name: str | None = None,
    name_contains: str | None = None,
    parent: str | None = None,
    mime_type: str | None = None,
    modified_after: str | None = None,
    modified_before: str | None = None,
    owner: str | None = None,
    include_trashed: bool = False,
    page_size: int = 100,
    max_results: int | None = 200,
) -> list[dict]:
    """Busca/lista archivos según filtros y ámbito, con tope de resultados.

    Por defecto devuelve hasta ``max_results`` (200) para evitar recorrer un Drive
    completo sin querer; pasa ``max_results=None`` para traer todas las páginas.

    :param scope: ``all`` (default) o ``mydrive``. Ignorado si se pasa ``drive_id``.
    :param drive_id: id de una Shared Drive concreta para acotar el ámbito.
    :param name: nombre exacto.
    :param name_contains: subcadena del nombre.
    :param parent: id de carpeta padre.
    :param mime_type: tipo MIME exacto.
    :param modified_after: fecha ISO-8601 límite inferior.
    :param modified_before: fecha ISO-8601 límite superior.
    :param owner: email del propietario.
    :param include_trashed: incluir elementos en papelera.
    :param page_size: tamaño de página solicitado a la API.
    :param max_results: tope de resultados; ``None`` = sin tope (todas las páginas).
    :return: lista de archivos con ``FILE_FIELDS``; vacía si no hay coincidencias.
    """
    query = _build_query(
        name=name,
        name_contains=name_contains,
        parent=parent,
        mime_type=mime_type,
        modified_after=modified_after,
        modified_before=modified_before,
        owner=owner,
        include_trashed=include_trashed,
    )
    params: dict[str, Any] = {
        "fields": f"nextPageToken, files({FILE_FIELDS})",
        "pageSize": page_size,
        **_list_params_for_scope(scope, drive_id),
    }
    if query:
        params["q"] = query
    return self._paginate(
        self._service.files().list, "files", max_results=max_results, **params
    )


# Enlace de funciones-método a la clase (definidas fuera para legibilidad).
DriveClient._paginate = _paginate
DriveClient.list_shared_drives = list_shared_drives
DriveClient.search = search


# --- Descarga y export -------------------------------------------------------

import io  # noqa: E402  (import local al bloque de descarga)
import os  # noqa: E402

import mime_map  # noqa: E402


def _default_uploader_factory(path, mimetype=None, resumable=False, chunksize=None):
    """Crea un ``MediaFileUpload`` real de googleapiclient.

    :param path: ruta del archivo local a subir.
    :param mimetype: MIME del contenido; ``None`` deja que la librería lo infiera.
    :param resumable: si ``True`` usa subida resumable por chunks.
    :param chunksize: tamaño de chunk para subidas resumables.
    :return: instancia de ``MediaFileUpload``.
    """
    from googleapiclient.http import MediaFileUpload

    kwargs = {"resumable": resumable}
    if mimetype is not None:
        kwargs["mimetype"] = mimetype
    if chunksize is not None:
        kwargs["chunksize"] = chunksize
    return MediaFileUpload(path, **kwargs)


def _default_downloader_factory(fh, request):
    """Crea un ``MediaIoBaseDownload`` real de googleapiclient.

    :param fh: file handle binario destino.
    :param request: request de media/export a descargar.
    :return: instancia de descargador con método ``next_chunk()``.
    """
    from googleapiclient.http import MediaIoBaseDownload

    return MediaIoBaseDownload(fh, request)


def _download_stream(self, request, dest_path: str) -> str:
    """Descarga una request de media/export por chunks a un archivo destino.

    :param request: request de ``files().get_media`` o ``files().export_media``.
    :param dest_path: ruta de archivo destino.
    :return: la ruta destino escrita.
    """
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    fh = io.FileIO(dest_path, mode="wb")
    try:
        downloader = self._downloader_factory(fh, request)
        done = False
        while not done:
            _status, done = downloader.next_chunk()
    finally:
        fh.close()
    logger.info("descarga completa: %s", os.path.basename(dest_path))
    return dest_path


def download_file(self, file_id: str, dest_path: str) -> str:
    """Descarga un archivo binario directamente (``files.get`` con ``alt=media``).

    :param file_id: id del archivo en Drive.
    :param dest_path: ruta destino local.
    :return: la ruta destino escrita.
    """
    request = self._service.files().get_media(
        fileId=file_id, supportsAllDrives=True
    )
    return self._download_stream(request, dest_path)


def export_file(self, file_id: str, google_mime: str, dest_path: str, fmt: str | None = None) -> str:
    """Exporta un archivo Google (Doc/Sheet/Slides/Drawing) al formato indicado.

    :param file_id: id del archivo Google en Drive.
    :param google_mime: MIME nativo Google del archivo.
    :param dest_path: ruta destino local (sin extensión obligatoria).
    :param fmt: formato de export (docx/xlsx/pptx/pdf/csv/md/...); ``None`` usa el default.
    :return: la ruta destino escrita (con la extensión del formato).
    :raises mime_map.UnsupportedExportFormatError: si el formato no aplica al tipo.
    """
    export_mime, extension = mime_map.resolve_export(google_mime, fmt)
    if not dest_path.endswith(extension):
        dest_path = f"{dest_path}{extension}"
    request = self._service.files().export_media(
        fileId=file_id, mimeType=export_mime
    )
    return self._download_stream(request, dest_path)


def download_any(self, file_meta: dict, dest_dir: str, fmt: str | None = None) -> str:
    """Descarga un archivo resolviendo binario vs export según su MIME.

    :param file_meta: metadatos con al menos ``id``, ``name`` y ``mimeType``.
    :param dest_dir: directorio destino.
    :param fmt: formato de export para tipos Google; ignorado en binarios.
    :return: ruta del archivo escrito.
    """
    file_id = file_meta["id"]
    name = file_meta["name"]
    mime = file_meta["mimeType"]
    if mime_map.is_google_native(mime):
        return self.export_file(file_id, mime, os.path.join(dest_dir, name), fmt)
    return self.download_file(file_id, os.path.join(dest_dir, name))


def download_folder_recursive(self, folder_id: str, dest_dir: str, fmt: str | None = None) -> list[str]:
    """Descarga recursivamente una carpeta conservando la estructura.

    :param folder_id: id de la carpeta raíz a descargar.
    :param dest_dir: directorio local base donde recrear el árbol.
    :param fmt: formato de export para archivos Google encontrados.
    :return: lista de rutas de archivos escritos.
    """
    os.makedirs(dest_dir, exist_ok=True)
    written: list[str] = []
    children = self.search(parent=folder_id, max_results=None)
    for child in children:
        if mime_map.is_folder(child["mimeType"]):
            sub_dir = os.path.join(dest_dir, child["name"])
            written.extend(self.download_folder_recursive(child["id"], sub_dir, fmt))
        else:
            written.append(self.download_any(child, dest_dir, fmt))
    return written


DriveClient._download_stream = _download_stream
DriveClient.download_file = download_file
DriveClient.export_file = export_file
DriveClient.download_any = download_any
DriveClient.download_folder_recursive = download_folder_recursive


# --- Subida y actualización --------------------------------------------------

# Umbral para decidir subida simple vs resumable (5 MB).
RESUMABLE_THRESHOLD_BYTES = 5 * 1024 * 1024
_RESUMABLE_CHUNK_BYTES = 5 * 1024 * 1024

# Estrategias de conflicto de nombre.
CONFLICT_NEW = "new"
CONFLICT_REPLACE = "replace"
CONFLICT_VERSION = "version"


def _guess_mime(path: str) -> str | None:
    """Adivina el MIME de un archivo local por su extensión.

    :param path: ruta del archivo local.
    :return: MIME inferido o ``None`` si no se pudo determinar.
    """
    import mimetypes

    mime, _ = mimetypes.guess_type(path)
    return mime


def find_by_name_in_parent(self, name: str, parent: str, drive_id: str | None = None) -> list[dict]:
    """Busca archivos por nombre exacto dentro de una carpeta.

    :param name: nombre exacto a buscar.
    :param parent: id de la carpeta destino.
    :param drive_id: id de Shared Drive si aplica.
    :return: lista de coincidencias (puede ser vacía).
    """
    scope = SCOPE_ALL if drive_id else SCOPE_MYDRIVE
    return self.search(name=name, parent=parent, scope=scope, drive_id=drive_id, max_results=None)


def upload(
    self,
    local_path: str,
    parent: str,
    *,
    name: str | None = None,
    convert: bool = False,
    on_conflict: str | None = None,
    drive_id: str | None = None,
):
    """Sube un archivo con estrategia simple o resumable según su tamaño.

    :param local_path: ruta del archivo local a subir.
    :param parent: id de la carpeta destino.
    :param name: nombre destino; por defecto el del archivo local.
    :param convert: si ``True``, convierte a formato Google equivalente.
    :param on_conflict: ``new``/``replace``/``version`` para resolver nombre duplicado.
        Si ``None`` y existe conflicto, se levanta ``ConflictError``.
    :param drive_id: id de Shared Drive destino si aplica.
    :return: metadatos del archivo creado/actualizado.
    :raises ConflictError: si hay nombre duplicado y no se indicó estrategia.
    """
    name = name or os.path.basename(local_path)
    existing = self.find_by_name_in_parent(name, parent, drive_id)
    if existing and on_conflict is None:
        raise ConflictError(
            f"Ya existe '{name}' en el destino. Indique estrategia: "
            f"{CONFLICT_NEW}, {CONFLICT_REPLACE} o {CONFLICT_VERSION}."
        )
    if existing and on_conflict in (CONFLICT_REPLACE, CONFLICT_VERSION):
        # Ambas estrategias reusan el mismo fileId (nueva revisión); no crea duplicado.
        return self.update_content(existing[0]["id"], local_path)

    source_mime = _guess_mime(local_path)
    size = os.path.getsize(local_path)
    resumable = size > RESUMABLE_THRESHOLD_BYTES
    media = self._uploader_factory(
        local_path,
        mimetype=source_mime,
        resumable=resumable,
        chunksize=_RESUMABLE_CHUNK_BYTES if resumable else None,
    )

    body: dict[str, Any] = {"name": name, "parents": [parent]}
    if convert:
        target = mime_map.convert_target(source_mime) if source_mime else None
        if target:
            body["mimeType"] = target

    request = self._service.files().create(
        body=body,
        media_body=media,
        fields=FILE_FIELDS,
        supportsAllDrives=True,
    )
    return self._execute(request)


def update_content(self, file_id: str, local_path: str):
    """Reemplaza el contenido de un archivo existente (nueva revisión, mismo fileId).

    :param file_id: id del archivo a actualizar.
    :param local_path: ruta del nuevo contenido local.
    :return: metadatos del archivo actualizado.
    """
    source_mime = _guess_mime(local_path)
    size = os.path.getsize(local_path)
    resumable = size > RESUMABLE_THRESHOLD_BYTES
    media = self._uploader_factory(
        local_path,
        mimetype=source_mime,
        resumable=resumable,
        chunksize=_RESUMABLE_CHUNK_BYTES if resumable else None,
    )
    request = self._service.files().update(
        fileId=file_id,
        media_body=media,
        fields=FILE_FIELDS,
        supportsAllDrives=True,
    )
    return self._execute(request)


def update_metadata(
    self,
    file_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
    properties: dict[str, str] | None = None,
):
    """Actualiza metadatos (nombre, descripción, propiedades) sin tocar el contenido.

    :param file_id: id del archivo a actualizar.
    :param name: nuevo nombre, si se cambia.
    :param description: nueva descripción, si se cambia.
    :param properties: propiedades personalizadas a fijar.
    :return: metadatos del archivo actualizado.
    :raises ValueError: si no se indicó ningún campo a actualizar.
    """
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if properties is not None:
        body["properties"] = properties
    if not body:
        raise ValueError("Debe indicar al menos un campo de metadatos a actualizar")
    request = self._service.files().update(
        fileId=file_id,
        body=body,
        fields=FILE_FIELDS,
        supportsAllDrives=True,
    )
    return self._execute(request)


DriveClient.find_by_name_in_parent = find_by_name_in_parent
DriveClient.upload = upload
DriveClient.update_content = update_content
DriveClient.update_metadata = update_metadata


# --- Organización y resolución de rutas --------------------------------------
#
# NOTA DE SEGURIDAD: este bloque implementa mover/renombrar/copiar/papelera/restaurar.
# NO existe borrado permanente: no se llama a files.delete() ni a emptyTrash().


class PathAmbiguousError(DriveClientError):
    """Un segmento de ruta tiene nombres duplicados y requiere desambiguación."""

    def __init__(self, segment: str, candidates: list[dict]):
        self.segment = segment
        self.candidates = candidates
        super().__init__(
            f"El segmento '{segment}' es ambiguo ({len(candidates)} candidatos). "
            f"Desambigüe por id."
        )


def get_file(self, file_id: str) -> dict:
    """Obtiene los metadatos de un archivo por id.

    :param file_id: id del archivo.
    :return: metadatos con ``FILE_FIELDS``.
    """
    request = self._service.files().get(
        fileId=file_id, fields=FILE_FIELDS, supportsAllDrives=True
    )
    return self._execute(request)


def mkdir_p(self, path: str, root: str, drive_id: str | None = None) -> str:
    """Crea una ruta de carpetas anidada, reutilizando las que ya existen.

    :param path: ruta relativa tipo ``a/b/c``.
    :param root: id de la carpeta raíz desde donde crear.
    :param drive_id: id de Shared Drive si aplica.
    :return: id de la carpeta más profunda (``c``).
    """
    parent = root
    for segment in [s for s in path.split("/") if s]:
        matches = [
            f for f in self.search(name=segment, parent=parent,
                                   scope=SCOPE_ALL if drive_id else SCOPE_MYDRIVE,
                                   drive_id=drive_id)
            if mime_map.is_folder(f["mimeType"])
        ]
        if matches:
            parent = matches[0]["id"]
            continue
        body = {
            "name": segment,
            "mimeType": mime_map.GOOGLE_FOLDER,
            "parents": [parent],
        }
        created = self._execute(
            self._service.files().create(
                body=body, fields="id, name, mimeType", supportsAllDrives=True
            )
        )
        parent = created["id"]
    return parent


def move(self, file_id: str, add_parent: str, remove_parent: str | None = None) -> dict:
    """Mueve un archivo a otra carpeta (y/o unidad) ajustando parents.

    :param file_id: id del archivo a mover.
    :param add_parent: id de la carpeta destino.
    :param remove_parent: id del parent a quitar; si ``None`` se resuelve del propio archivo.
    :return: metadatos del archivo tras el movimiento.
    """
    if remove_parent is None:
        current = self.get_file(file_id)
        parents = current.get("parents", [])
        remove_parent = ",".join(parents) if parents else None
    request = self._service.files().update(
        fileId=file_id,
        addParents=add_parent,
        removeParents=remove_parent,
        fields=FILE_FIELDS,
        supportsAllDrives=True,
    )
    return self._execute(request)


def rename(self, file_id: str, new_name: str) -> dict:
    """Renombra un archivo o carpeta.

    :param file_id: id del recurso.
    :param new_name: nuevo nombre.
    :return: metadatos actualizados.
    """
    return self.update_metadata(file_id, name=new_name)


def copy(self, file_id: str, new_name: str | None = None, parent: str | None = None) -> dict:
    """Copia un archivo, opcionalmente con nuevo nombre y carpeta destino.

    :param file_id: id del archivo a copiar.
    :param new_name: nombre de la copia; ``None`` conserva el original con prefijo del servidor.
    :param parent: id de carpeta destino de la copia.
    :return: metadatos del archivo copiado.
    """
    body: dict[str, Any] = {}
    if new_name:
        body["name"] = new_name
    if parent:
        body["parents"] = [parent]
    request = self._service.files().copy(
        fileId=file_id, body=body, fields=FILE_FIELDS, supportsAllDrives=True
    )
    return self._execute(request)


def trash(self, file_id: str) -> dict:
    """Envía un archivo a la papelera (reversible; NO es borrado permanente).

    :param file_id: id del archivo.
    :return: metadatos con ``trashed=True``.
    """
    request = self._service.files().update(
        fileId=file_id, body={"trashed": True}, fields=FILE_FIELDS, supportsAllDrives=True
    )
    return self._execute(request)


def restore(self, file_id: str) -> dict:
    """Restaura un archivo desde la papelera.

    :param file_id: id del archivo.
    :return: metadatos con ``trashed=False``.
    """
    request = self._service.files().update(
        fileId=file_id, body={"trashed": False}, fields=FILE_FIELDS, supportsAllDrives=True
    )
    return self._execute(request)


def resolve_path(self, path: str, drive_id: str | None = None, root: str = "root") -> str:
    """Resuelve una ruta legible a un ``fileId``, desambiguando duplicados.

    Si ``drive_id`` se pasa, la resolución arranca en la raíz de esa Shared Drive; si no,
    arranca en la raíz de Mi unidad (``root``).

    :param path: ruta tipo ``Carpeta/Sub/archivo``.
    :param drive_id: id de Shared Drive donde resolver; ``None`` para Mi unidad.
    :param root: id de la raíz de Mi unidad (por defecto ``root``).
    :return: id del último segmento de la ruta.
    :raises NotFoundError: si un segmento no existe.
    :raises PathAmbiguousError: si un segmento tiene nombres duplicados.
    """
    parent = drive_id if drive_id else root
    segments = [s for s in path.split("/") if s]
    for segment in segments:
        matches = self.search(
            name=segment,
            parent=parent,
            scope=SCOPE_ALL if drive_id else SCOPE_MYDRIVE,
            drive_id=drive_id,
        )
        if not matches:
            raise NotFoundError(f"No existe el segmento '{segment}' en la ruta '{path}'")
        if len(matches) > 1:
            raise PathAmbiguousError(segment, matches)
        parent = matches[0]["id"]
    return parent


DriveClient.get_file = get_file
DriveClient.mkdir_p = mkdir_p
DriveClient.move = move
DriveClient.rename = rename
DriveClient.copy = copy
DriveClient.trash = trash
DriveClient.restore = restore
DriveClient.resolve_path = resolve_path
