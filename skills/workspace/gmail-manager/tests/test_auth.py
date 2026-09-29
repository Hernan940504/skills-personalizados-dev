"""Tests de autenticación con dobles (sin red ni credenciales reales)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import auth  # noqa: E402


class _FakeCreds:
    def __init__(self, valid=True, expired=False, refresh_token=None):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refreshed = False

    def refresh(self, _request):
        self.refreshed = True
        self.valid = True

    def to_json(self):
        return '{"token": "fake"}'


class TestLoadSettings(unittest.TestCase):
    def test_defaults_y_scope_readonly(self):
        s = auth.load_settings(env={})
        self.assertTrue(str(s.token_path).endswith("gmail-skill/token.json"))
        self.assertEqual(s.scopes, [auth.SCOPE_GMAIL_READONLY])

    def test_override_por_env(self):
        s = auth.load_settings(env={"GMAIL_TOKEN_PATH": "/tmp/x/token.json"})
        self.assertEqual(str(s.token_path), "/tmp/x/token.json")


class TestGetCredentials(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.token = Path(self._tmp.name) / "token.json"
        self.creds_file = Path(self._tmp.name) / "credentials.json"

    def tearDown(self):
        self._tmp.cleanup()

    def _settings(self):
        return auth.AuthSettings(self.creds_file, self.token, [auth.SCOPE_GMAIL_READONLY])

    def test_token_valido_se_reutiliza(self):
        self.token.write_text("{}", encoding="utf-8")
        valid = _FakeCreds(valid=True)
        creds = auth.get_credentials(
            self._settings(), credentials_factory=lambda p, s: valid,
        )
        self.assertIs(creds, valid)

    def test_token_expirado_se_refresca_y_persiste(self):
        self.token.write_text("{}", encoding="utf-8")
        expired = _FakeCreds(valid=False, expired=True, refresh_token="r")
        creds = auth.get_credentials(
            self._settings(),
            credentials_factory=lambda p, s: expired,
            request_factory=lambda: object(),
        )
        self.assertTrue(creds.refreshed)
        self.assertTrue(self.token.exists())

    def test_sin_token_no_interactivo_falla(self):
        with self.assertRaises(auth.AuthRequiredError):
            auth.get_credentials(self._settings(), allow_interactive=False)

    def test_detecta_tipo_client_web(self):
        self.creds_file.write_text('{"web": {"client_id": "x"}}', encoding="utf-8")
        self.assertEqual(auth._client_type(self.creds_file), "web")

    def test_detecta_tipo_client_installed(self):
        self.creds_file.write_text('{"installed": {"client_id": "x"}}', encoding="utf-8")
        self.assertEqual(auth._client_type(self.creds_file), "installed")


if __name__ == "__main__":
    unittest.main()
