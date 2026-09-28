"""Manejo de credenciales y token OAuth 2.0 para Google Drive (installed app).

Responsabilidades:

- Resolver rutas de ``credentials.json`` y ``token.json`` y los scopes desde variables
  de entorno, con defaults fuera del repo (``~/.config/gdrive-skill/``).
- Cargar/renovar el token y, si no existe, correr el flujo OAuth de escritorio (loopback).
- Persistir el token con permisos restrictivos (0600).

Reglas de seguridad:

- Nunca se registra en logs el contenido de tokens ni credenciales.
- Sin secretos hardcodeados.

Las dependencias de Google se importan de forma diferida dentro de las funciones para que
el módulo sea importable en tests sin las librerías instaladas, y para poder inyectar dobles.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("gdrive.auth")

# Scopes documentados. ``drive.file`` (menor privilegio) solo ve archivos creados por la app;
# ``drive`` (default aquí) permite organizar archivos existentes que la app no creó.
SCOPE_DRIVE_FILE = "https://www.googleapis.com/auth/drive.file"
SCOPE_DRIVE = "https://www.googleapis.com/auth/drive"

_DEFAULT_CONFIG_DIR = Path.home() / ".config" / "gdrive-skill"


class AuthRequiredError(RuntimeError):
    """No hay credenciales válidas y no es posible renovarlas sin re-autenticar."""


@dataclass(frozen=True)
class AuthSettings:
    """Configuración de autenticación resuelta desde el entorno.

    :param credentials_path: ruta al ``credentials.json`` del cliente OAuth.
    :param token_path: ruta donde se persiste el ``token.json``.
    :param scopes: lista de scopes OAuth solicitados.
    """

    credentials_path: Path
    token_path: Path
    scopes: list[str]


def load_settings(env: dict[str, str] | None = None) -> AuthSettings:
    """Resuelve rutas y scopes desde variables de entorno con defaults seguros.

    :param env: mapping de entorno; por defecto ``os.environ``.
    :return: ``AuthSettings`` con rutas absolutas y scopes.
    """
    env = env if env is not None else dict(os.environ)
    credentials_path = Path(
        env.get("GDRIVE_CREDENTIALS_PATH", str(_DEFAULT_CONFIG_DIR / "credentials.json"))
    ).expanduser()
    token_path = Path(
        env.get("GDRIVE_TOKEN_PATH", str(_DEFAULT_CONFIG_DIR / "token.json"))
    ).expanduser()
    raw_scopes = env.get("GDRIVE_SCOPES", SCOPE_DRIVE).strip()
    scopes = [s for s in raw_scopes.split() if s]
    return AuthSettings(
        credentials_path=credentials_path, token_path=token_path, scopes=scopes
    )


def _persist_token(token_path: Path, creds) -> None:
    """Guarda el token en disco con permisos 0600, creando el directorio si falta.

    :param token_path: ruta de destino del token.
    :param creds: objeto de credenciales con método ``to_json()``.
    """
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    try:
        os.chmod(token_path, 0o600)
    except OSError:
        # En sistemas de archivos que no soportan chmod, no es fatal; se avisa sin datos sensibles.
        logger.warning("no se pudo aplicar permisos 0600 a token en %s", token_path.name)


def get_credentials(
    settings: AuthSettings,
    *,
    credentials_factory=None,
    flow_factory=None,
    request_factory=None,
    allow_interactive: bool = True,
):
    """Obtiene credenciales válidas: reutiliza, renueva o corre el flujo OAuth.

    Las factories permiten inyectar dobles en tests; en producción se resuelven a las
    librerías oficiales de Google.

    :param settings: configuración de rutas y scopes.
    :param credentials_factory: callable que carga credenciales desde el token guardado.
    :param flow_factory: callable que crea el flujo OAuth desde ``credentials.json``.
    :param request_factory: callable que crea el transporte para refrescar el token.
    :param allow_interactive: si ``False``, no lanza el flujo interactivo y falla en su lugar.
    :return: credenciales válidas listas para construir el servicio de Drive.
    :raises AuthRequiredError: si no hay token válido y no se puede/permite re-autenticar.
    """
    credentials_factory = credentials_factory or _default_credentials_factory
    flow_factory = flow_factory or _default_flow_factory
    request_factory = request_factory or _default_request_factory

    creds = None
    if settings.token_path.exists():
        creds = credentials_factory(str(settings.token_path), settings.scopes)

    if creds and creds.valid:
        return creds

    if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
        try:
            creds.refresh(request_factory())
        except Exception as exc:  # google.auth.exceptions.RefreshError y afines
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
            f"{settings.credentials_path}. Configure GDRIVE_CREDENTIALS_PATH."
        )

    flow = flow_factory(str(settings.credentials_path), settings.scopes)
    creds = flow.run_local_server(port=0)
    _persist_token(settings.token_path, creds)
    return creds


def _default_credentials_factory(token_path: str, scopes: list[str]):
    """Carga credenciales desde un token guardado usando google-auth."""
    from google.oauth2.credentials import Credentials

    return Credentials.from_authorized_user_file(token_path, scopes)


def _default_flow_factory(credentials_path: str, scopes: list[str]):
    """Crea el flujo OAuth installed-app usando google-auth-oauthlib."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    return InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)


def _default_request_factory():
    """Crea el transporte de refresh usando google-auth."""
    from google.auth.transport.requests import Request

    return Request()
