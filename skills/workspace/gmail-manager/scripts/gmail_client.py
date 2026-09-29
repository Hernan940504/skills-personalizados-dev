"""Capa delgada sobre la Gmail API v1 (solo lectura).

Expone las operaciones que necesita el barrido: listar etiquetas, filtrar las de línea de negocio,
buscar mensajes por etiqueta con filtro ``after:`` (paginado) y leer metadata + snippet de un
mensaje (sin traer el cuerpo completo ni adjuntos). Reintentos con backoff en errores transitorios.

El objeto ``service`` de Google se inyecta (permite tests con dobles). La construcción real vive en
``build_service`` para no requerir credenciales en tests.
"""

from __future__ import annotations

import logging
import random
import time

logger = logging.getLogger("gmail.client")

BUSINESS_LABEL_PREFIX = "Tribu Servicios Bolivar/"
_RETRYABLE = {429, 500, 502, 503, 504}
_MAX_RETRIES = 5


def build_service(creds):
    """Construye el service de Gmail v1 a partir de credenciales."""
    from googleapiclient.discovery import build

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _http_error_type():
    """Devuelve la clase HttpError si la librería está disponible, o None (p.ej. en tests)."""
    try:
        from googleapiclient.errors import HttpError

        return HttpError
    except ImportError:
        return None


def _execute(request):
    """Ejecuta un request de la API con reintentos y backoff+jitter en errores transitorios."""
    http_error = _http_error_type()
    for attempt in range(_MAX_RETRIES):
        try:
            return request.execute()
        except Exception as exc:  # noqa: BLE001 - se filtra por tipo/estado abajo
            if http_error is None or not isinstance(exc, http_error):
                raise
            status = getattr(exc.resp, "status", None)
            code = int(status) if status is not None else None
            if code in _RETRYABLE and attempt < _MAX_RETRIES - 1:
                sleep = (2 ** attempt) + random.random()
                logger.warning("reintento %s tras HTTP %s (%.1fs)", attempt + 1, code, sleep)
                time.sleep(sleep)
                continue
            raise
    raise RuntimeError("agotados los reintentos")


def get_profile(service) -> dict:
    """Devuelve el perfil (emailAddress, messagesTotal) del usuario autenticado."""
    return _execute(service.users().getProfile(userId="me"))


def list_labels(service) -> list[dict]:
    """Lista todas las etiquetas de la cuenta (``{id, name, type}``)."""
    resp = _execute(service.users().labels().list(userId="me"))
    return resp.get("labels", [])


def business_labels(labels: list[dict], prefix: str = BUSINESS_LABEL_PREFIX) -> list[dict]:
    """Filtra las etiquetas hijas del prefijo de línea de negocio."""
    return [l for l in labels if l.get("name", "").startswith(prefix)]


def search_message_ids(service, label_id: str, after_epoch: int, *, max_results: int = 100):
    """Itera los ids de mensajes de una etiqueta con ``after:`` (generador, paginado).

    :yields: ``message_id`` (str) de cada mensaje que cumple el filtro.
    """
    page_token = None
    query = f"after:{after_epoch}"
    while True:
        req = service.users().messages().list(
            userId="me", labelIds=[label_id], q=query,
            maxResults=max_results, pageToken=page_token,
        )
        resp = _execute(req)
        for msg in resp.get("messages", []):
            yield msg["id"]
        page_token = resp.get("nextPageToken")
        if not page_token:
            break


def get_message_meta(service, message_id: str) -> dict:
    """Lee metadata (From, Subject, Date, To) + snippet de un mensaje (sin cuerpo completo).

    :return: ``{id, threadId, sender, subject, date, to, snippet, thread_url}``.
    """
    req = service.users().messages().get(
        userId="me", id=message_id, format="metadata",
        metadataHeaders=["From", "Subject", "Date", "To", "Cc"],
    )
    msg = _execute(req)
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    thread_id = msg.get("threadId", "")
    return {
        "id": msg.get("id", message_id),
        "threadId": thread_id,
        "sender": headers.get("from", ""),
        "subject": headers.get("subject", "(sin asunto)"),
        "date": headers.get("date", ""),
        "to": headers.get("to", "") + " " + headers.get("cc", ""),
        "snippet": msg.get("snippet", ""),
        "thread_url": f"https://mail.google.com/mail/u/0/#all/{thread_id}" if thread_id else "",
    }


def _decode_b64url(data: str) -> str:
    """Decodifica un cuerpo base64url de Gmail a texto UTF-8 (tolerante a errores)."""
    import base64

    try:
        return base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_plain_text(payload: dict) -> str:
    """Recorre el árbol MIME del mensaje y devuelve el texto plano (prefiere text/plain)."""
    mime = payload.get("mimeType", "")
    body = payload.get("body", {})
    if mime == "text/plain" and body.get("data"):
        return _decode_b64url(body["data"])
    # multipart: recorrer partes, preferir text/plain sobre text/html
    parts = payload.get("parts", []) or []
    plain, html = "", ""
    for part in parts:
        text = _extract_plain_text(part)
        if part.get("mimeType") == "text/plain" and text:
            plain += text + "\n"
        elif part.get("mimeType") == "text/html" and text and not plain:
            html += text + "\n"
        elif text:
            plain += text + "\n"
    if plain.strip():
        return plain
    if html.strip():
        # quitar tags HTML de forma simple
        import re

        return re.sub(r"<[^>]+>", " ", html)
    return ""


def get_thread(service, thread_id: str) -> dict:
    """Lee un hilo completo: metadata de todos sus mensajes + cuerpo de texto de cada uno.

    :return: ``{threadId, subject, participants, messages:[{sender,date,body}], thread_url}``.
    """
    req = service.users().threads().get(userId="me", id=thread_id, format="full")
    thread = _execute(req)
    messages = []
    participants: list[str] = []
    subject = "(sin asunto)"
    for msg in thread.get("messages", []):
        headers = {h["name"].lower(): h["value"]
                   for h in msg.get("payload", {}).get("headers", [])}
        if subject == "(sin asunto)" and headers.get("subject"):
            subject = headers["subject"]
        sender = headers.get("from", "")
        if sender and sender not in participants:
            participants.append(sender)
        messages.append({
            "sender": sender,
            "date": headers.get("date", ""),
            "to": headers.get("to", "") + " " + headers.get("cc", ""),
            "subject": headers.get("subject", subject),
            "snippet": msg.get("snippet", ""),
            "body": _extract_plain_text(msg.get("payload", {})),
        })
    return {
        "threadId": thread_id,
        "subject": subject,
        "participants": participants,
        "messages": messages,
        "thread_url": f"https://mail.google.com/mail/u/0/#all/{thread_id}",
    }
