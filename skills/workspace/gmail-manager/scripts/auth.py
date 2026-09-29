"""Manejo de credenciales y token OAuth 2.0 para Gmail (solo lectura).

Reutiliza el patrón de ``google-drive-manager``: resuelve rutas y scope desde el entorno con
defaults fuera del repo (``~/.config/gmail-skill/``), carga/renueva el token y, si no existe,
corre el flujo OAuth installed-app.

Soporta dos formas del client OAuth:
- **Desktop app** (``installed``): usa ``run_local_server(port=0)`` (loopback con puerto aleatorio).
- **Web** con redirect ``http://localhost:8080/callback`` autorizado: usa un servidor local en ese
  puerto/ruta exactos (el client disponible en este entorno es de este tipo).

Reglas de seguridad:
- Scope exclusivamente de solo lectura (``gmail.readonly``).
- Nunca se registra el contenido de tokens ni credenciales.
- Token persistido con permisos 0600, fuera del repo.

Las dependencias de Google se importan de forma diferida para poder testear sin las librerías.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger("gmail.auth")

SCOPE_GMAIL_READONLY = "https://www.googleapis.com/auth/gmail.readonly"
_DEFAULT_CONFIG_DIR = Path.home() / ".config" / "gmail-skill"
_WEB_REDIRECT_URI = "http://localhost:8080/callback"


class AuthRequiredError(RuntimeError):
    """No hay credenciales válidas y no es posible renovarlas sin re-autenticar."""


@dataclass(frozen=True)
class AuthSettings:
    """Configuración de autenticación resuelta desde el entorno."""

    credentials_path: Path
    token_path: Path
    scopes: list[str]


def load_settings(env: dict[str, str] | None = None) -> AuthSettings:
    """Resuelve rutas y scope desde variables de entorno con defaults seguros.

    :param env: mapping de entorno; por defecto ``os.environ``.
    :return: ``AuthSettings`` con rutas absolutas y el scope de solo lectura.
    """
    env = env if env is not None else dict(os.environ)
    credentials_path = Path(
        env.get("GMAIL_CREDENTIALS_PATH", str(_DEFAULT_CONFIG_DIR / "credentials.json"))
    ).expanduser()
    token_path = Path(
        env.get("GMAIL_TOKEN_PATH", str(_DEFAULT_CONFIG_DIR / "token.json"))
    ).expanduser()
    return AuthSettings(
        credentials_path=credentials_path,
        token_path=token_path,
        scopes=[SCOPE_GMAIL_READONLY],
    )


def _persist_token(token_path: Path, creds) -> None:
    """Guarda el token en disco con permisos 0600, creando el directorio si falta."""
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    try:
        os.chmod(token_path, 0o600)
    except OSError:
        logger.warning("no se pudo aplicar permisos 0600 al token %s", token_path.name)


def _client_type(credentials_path: Path) -> str:
    """Devuelve 'web' o 'installed' según la clave raíz del client OAuth."""
    data = json.loads(credentials_path.read_text(encoding="utf-8"))
    if "installed" in data:
        return "installed"
    if "web" in data:
        return "web"
    raise AuthRequiredError(
        "El credentials.json no es un client OAuth válido (falta 'installed'/'web')."
    )


class _CallbackHandler(BaseHTTPRequestHandler):
    """Captura el authorization code del redirect web en /callback."""

    code_holder: dict = {}

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        type(self).code_holder["code"] = parse_qs(parsed.query).get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            "<h2>Gmail autorizado. Puedes cerrar esta ventana.</h2>".encode("utf-8")
        )

    def log_message(self, *args):
        return


def get_credentials(
    settings: AuthSettings,
    *,
    credentials_factory=None,
    flow_factory=None,
    web_flow_factory=None,
    request_factory=None,
    allow_interactive: bool = True,
):
    """Obtiene credenciales válidas: reutiliza, renueva o corre el flujo OAuth.

    Las factories permiten inyectar dobles en tests.

    :param settings: configuración de rutas y scope.
    :param credentials_factory: carga credenciales desde el token guardado.
    :param flow_factory: crea el flujo installed-app (Desktop).
    :param web_flow_factory: crea el flujo web (redirect localhost:8080/callback).
    :param request_factory: crea el transporte para refrescar el token.
    :param allow_interactive: si ``False``, no lanza el flujo interactivo.
    :return: credenciales válidas para construir el servicio de Gmail.
    :raises AuthRequiredError: si no hay token válido y no se puede/permite re-autenticar.
    """
    credentials_factory = credentials_factory or _default_credentials_factory
    flow_factory = flow_factory or _default_flow_factory
    web_flow_factory = web_flow_factory or _default_web_flow_factory
    request_factory = request_factory or _default_request_factory

    creds = None
    if settings.token_path.exists():
        creds = credentials_factory(str(settings.token_path), settings.scopes)

    if creds and creds.valid:
        return creds

    if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
        try:
            creds.refresh(request_factory())
        except Exception as exc:
            raise AuthRequiredError(
                "No se pudo renovar el token (refresh revocado o inválido). "
                "Ejecute el comando `auth` para re-autenticar."
            ) from exc
        _persist_token(settings.token_path, creds)
        return creds

    if not allow_interactive:
        raise AuthRequiredError(
            "No hay token válido. Ejecute el comando `auth` para autenticar."
        )

    if not settings.credentials_path.exists():
        raise AuthRequiredError(
            f"No se encontró el archivo de credenciales OAuth en "
            f"{settings.credentials_path}. Configure GMAIL_CREDENTIALS_PATH."
        )

    kind = _client_type(settings.credentials_path)
    if kind == "installed":
        flow = flow_factory(str(settings.credentials_path), settings.scopes)
        creds = flow.run_local_server(port=0)
    else:
        creds = web_flow_factory(str(settings.credentials_path), settings.scopes)

    _persist_token(settings.token_path, creds)
    return creds


def _default_credentials_factory(token_path: str, scopes: list[str]):
    """Carga credenciales desde un token guardado usando google-auth."""
    from google.oauth2.credentials import Credentials

    return Credentials.from_authorized_user_file(token_path, scopes)


def _default_flow_factory(credentials_path: str, scopes: list[str]):
    """Crea el flujo OAuth installed-app (Desktop) usando google-auth-oauthlib."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    return InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)


def _default_web_flow_factory(credentials_path: str, scopes: list[str]):
    """Corre el flujo OAuth para un client web con redirect localhost:8080/callback."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(credentials_path, scopes=scopes)
    flow.redirect_uri = _WEB_REDIRECT_URI
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    print("AUTH_URL=" + auth_url, flush=True)

    _CallbackHandler.code_holder = {}
    server = HTTPServer(("localhost", 8080), _CallbackHandler)
    server.handle_request()
    server.server_close()

    code = _CallbackHandler.code_holder.get("code")
    if not code:
        raise AuthRequiredError("No se recibió el authorization code del redirect.")
    flow.fetch_token(code=code)
    return flow.credentials


def _default_request_factory():
    """Crea el transporte de refresh usando google-auth."""
    from google.auth.transport.requests import Request

    return Request()
