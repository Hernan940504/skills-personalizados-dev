"""Tests del núcleo de vault: seguridad de rutas, escritura atómica y slugify."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import vault  # noqa: E402


class TestResolveVaultPath(unittest.TestCase):
    def test_explicito_tiene_prioridad(self):
        p = vault.resolve_vault_path("/tmp/mi-vault", env={"OBSIDIAN_VAULT_PATH": "/otro"})
        self.assertEqual(p, Path("/tmp/mi-vault"))

    def test_env_var(self):
        p = vault.resolve_vault_path(None, env={"OBSIDIAN_VAULT_PATH": "/env/vault"})
        self.assertEqual(p, Path("/env/vault"))

    def test_default_cuando_no_hay_config(self):
        p = vault.resolve_vault_path(None, env={})
        self.assertTrue(str(p).endswith("second-brain"))


class TestSlugify(unittest.TestCase):
    def test_normaliza_acentos_y_espacios(self):
        self.assertEqual(vault.slugify("Análisis de Cámara"), "analisis-de-camara")

    def test_caracteres_especiales(self):
        self.assertEqual(vault.slugify("Nota: v2 (final)!"), "nota-v2-final")

    def test_vacio_devuelve_nota(self):
        self.assertEqual(vault.slugify("!!!"), "nota")


class TestSafePath(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        self.vault_dir.mkdir()
        self.client = vault.VaultClient(self.vault_dir, require_exists=False)

    def tearDown(self):
        self._tmp.cleanup()

    def test_ruta_relativa_valida(self):
        p = self.client._safe_path("inbox/nota.md")
        self.assertTrue(str(p).startswith(str(self.vault_dir.resolve())))

    def test_rechaza_traversal(self):
        with self.assertRaises(vault.UnsafePathError):
            self.client._safe_path("../fuera.md")

    def test_rechaza_absoluta(self):
        with self.assertRaises(vault.UnsafePathError):
            self.client._safe_path("/etc/passwd")

    def test_rechaza_traversal_profundo(self):
        with self.assertRaises(vault.UnsafePathError):
            self.client._safe_path("inbox/../../fuera.md")


class TestAtomicWrite(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        self.vault_dir.mkdir()
        self.client = vault.VaultClient(self.vault_dir, require_exists=False)

    def tearDown(self):
        self._tmp.cleanup()

    def test_escribe_y_normaliza_crlf(self):
        target = self.client._safe_path("inbox/n.md")
        self.client._atomic_write(target, "a\r\nb\r\n")
        self.assertEqual(target.read_text(encoding="utf-8"), "a\nb\n")

    def test_no_deja_tmp(self):
        target = self.client._safe_path("inbox/n.md")
        self.client._atomic_write(target, "contenido")
        tmp = target.with_suffix(".md.tmp")
        self.assertFalse(tmp.exists())

    def test_unique_slug_evita_colision(self):
        (self.vault_dir / "inbox").mkdir()
        (self.vault_dir / "inbox" / "nota.md").write_text("x", encoding="utf-8")
        self.assertEqual(self.client._unique_slug("inbox", "nota"), "nota-2")


class TestRequireExists(unittest.TestCase):
    def test_vault_inexistente_falla(self):
        with self.assertRaises(vault.NotFoundError):
            vault.VaultClient("/ruta/que/no/existe/vault", require_exists=True)


if __name__ == "__main__":
    unittest.main()
