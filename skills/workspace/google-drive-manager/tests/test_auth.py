"""Tests de auth: settings desde entorno, refresh, flujo nuevo y refresh revocado.

Se inyectan dobles (factories) para no depender de las librerías de Google ni de red.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import auth  # noqa: E402


class FakeCreds:
    """Doble de google.oauth2.credentials.Credentials."""

    def __init__(self, valid=True, expired=False, refresh_token=None, raise_on_refresh=False):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self._raise_on_refresh = raise_on_refresh
        self.refreshed = False

    def refresh(self, request):
        if self._raise_on_refresh:
            raise RuntimeError("refresh revocado")
        self.refreshed = True
        self.valid = True
        self.expired = False

    def to_json(self):
        return '{"token": "REDACTED"}'


class TestLoadSettings(unittest.TestCase):
    def test_defaults_fuera_del_repo(self):
        # Given entorno vacío, When load_settings, Then defaults en ~/.config/gdrive-skill.
        settings = auth.load_settings(env={})
        self.assertTrue(str(settings.credentials_path).endswith("gdrive-skill/credentials.json"))
        self.assertTrue(str(settings.token_path).endswith("gdrive-skill/token.json"))
        self.assertEqual(settings.scopes, [auth.SCOPE_DRIVE])

    def test_env_override_y_scopes_multiples(self):
        env = {
            "GDRIVE_CREDENTIALS_PATH": "/tmp/c.json",
            "GDRIVE_TOKEN_PATH": "/tmp/t.json",
            "GDRIVE_SCOPES": f"{auth.SCOPE_DRIVE_FILE} {auth.SCOPE_DRIVE}",
        }
        settings = auth.load_settings(env=env)
        self.assertEqual(settings.credentials_path, Path("/tmp/c.json"))
        self.assertEqual(settings.scopes, [auth.SCOPE_DRIVE_FILE, auth.SCOPE_DRIVE])


class TestGetCredentials(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.token_path = Path(self.tmp.name) / "token.json"
        self.creds_path = Path(self.tmp.name) / "credentials.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _settings(self):
        return auth.AuthSettings(
            credentials_path=self.creds_path,
            token_path=self.token_path,
            scopes=[auth.SCOPE_DRIVE],
        )

    def test_token_valido_se_reutiliza(self):
        # Given token válido en disco, When get_credentials, Then no corre flujo ni refresh.
        self.token_path.write_text("{}", encoding="utf-8")
        valid = FakeCreds(valid=True)
        creds = auth.get_credentials(
            self._settings(),
            credentials_factory=lambda p, s: valid,
            flow_factory=lambda p, s: self.fail("no debe crear flujo"),
            request_factory=lambda: self.fail("no debe refrescar"),
        )
        self.assertIs(creds, valid)

    def test_token_expirado_se_refresca_y_persiste(self):
        # Given token expirado con refresh_token, When get_credentials, Then refresca y guarda.
        self.token_path.write_text("{}", encoding="utf-8")
        expired = FakeCreds(valid=False, expired=True, refresh_token="rt")
        creds = auth.get_credentials(
            self._settings(),
            credentials_factory=lambda p, s: expired,
            request_factory=lambda: object(),
        )
        self.assertTrue(creds.refreshed)
        self.assertTrue(self.token_path.exists())

    def test_refresh_revocado_lanza_auth_required(self):
        # Given refresh que falla, When get_credentials, Then AuthRequiredError.
        self.token_path.write_text("{}", encoding="utf-8")
        revoked = FakeCreds(valid=False, expired=True, refresh_token="rt", raise_on_refresh=True)
        with self.assertRaises(auth.AuthRequiredError):
            auth.get_credentials(
                self._settings(),
                credentials_factory=lambda p, s: revoked,
                request_factory=lambda: object(),
            )

    def test_sin_token_corre_flujo_nuevo(self):
        # Given sin token pero con credentials.json, When get_credentials, Then corre flujo.
        self.creds_path.write_text("{}", encoding="utf-8")
        new_creds = FakeCreds(valid=True)

        class FakeFlow:
            def run_local_server(self, port=0):
                return new_creds

        creds = auth.get_credentials(
            self._settings(),
            flow_factory=lambda p, s: FakeFlow(),
        )
        self.assertIs(creds, new_creds)
        self.assertTrue(self.token_path.exists())

    def test_no_interactivo_sin_token_falla(self):
        # Given sin token y allow_interactive False, When get_credentials, Then AuthRequiredError.
        with self.assertRaises(auth.AuthRequiredError):
            auth.get_credentials(self._settings(), allow_interactive=False)

    def test_flujo_sin_credentials_json_falla(self):
        # Given sin token y sin credentials.json, When get_credentials interactivo, Then error.
        with self.assertRaises(auth.AuthRequiredError):
            auth.get_credentials(self._settings())

    def test_token_persistido_no_expone_secreto_en_json_de_prueba(self):
        # El doble to_json marca REDACTED: garantiza que persistimos lo que devuelve to_json().
        self.creds_path.write_text("{}", encoding="utf-8")

        class FakeFlow:
            def run_local_server(self, port=0):
                return FakeCreds(valid=True)

        auth.get_credentials(self._settings(), flow_factory=lambda p, s: FakeFlow())
        self.assertIn("REDACTED", self.token_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
