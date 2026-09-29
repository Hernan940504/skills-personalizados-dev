"""Tests de vault: init idempotente (y en tareas siguientes: notas, búsqueda, grafo...)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import vault  # noqa: E402


class VaultTestCase(unittest.TestCase):
    """Base con un vault temporal inicializado por test (sin tocar el vault real)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        vault.init_vault(self.vault_dir)
        self.client = vault.VaultClient(self.vault_dir)

    def tearDown(self):
        self._tmp.cleanup()


class TestInit(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"

    def tearDown(self):
        self._tmp.cleanup()

    def test_init_crea_estructura(self):
        # When init, Then existen carpetas y archivos base.
        result = vault.init_vault(self.vault_dir)
        self.assertTrue(result["created"])
        for rel in vault.BASE_DIRS:
            self.assertTrue((self.vault_dir / rel).is_dir(), f"falta {rel}")
        self.assertTrue((self.vault_dir / "index.md").exists())
        self.assertTrue((self.vault_dir / "pendientes.md").exists())
        self.assertTrue((self.vault_dir / ".brain" / "fuentes.json").exists())
        self.assertTrue((self.vault_dir / ".obsidian" / "app.json").exists())

    def test_init_es_idempotente(self):
        # Given un vault ya inicializado, When init de nuevo, Then no sobrescribe.
        vault.init_vault(self.vault_dir)
        (self.vault_dir / "index.md").write_text("MI CONTENIDO", encoding="utf-8")
        result = vault.init_vault(self.vault_dir)
        self.assertTrue(result["already_initialized"])
        self.assertFalse(result["created"])
        self.assertEqual(
            (self.vault_dir / "index.md").read_text(encoding="utf-8"), "MI CONTENIDO"
        )

    def test_operacion_sin_vault_falla(self):
        # Given una ruta sin vault, When VaultClient con require_exists, Then NotFoundError.
        with self.assertRaises(vault.NotFoundError):
            vault.VaultClient(self.vault_dir / "no-existe")


class TestCreateNote(VaultTestCase):
    def test_crea_con_frontmatter_y_slug(self):
        res = self.client.create_note("Análisis de Cámara", body="cuerpo", tags=["aws"])
        self.assertTrue(res["created"])
        self.assertEqual(res["name"], "analisis-de-camara")
        self.assertEqual(res["path"], "inbox/analisis-de-camara.md")
        text = (self.vault_dir / res["path"]).read_text(encoding="utf-8")
        self.assertIn("title: Análisis de Cámara", text)
        self.assertIn("tags: [aws]", text)
        self.assertIn("cuerpo", text)

    def test_conflicto_new_agrega_sufijo(self):
        self.client.create_note("Nota", body="a")
        res = self.client.create_note("Nota", body="b", on_conflict=vault.CONFLICT_NEW)
        self.assertEqual(res["name"], "nota-2")

    def test_conflicto_skip(self):
        self.client.create_note("Nota", body="a")
        res = self.client.create_note("Nota", body="b", on_conflict=vault.CONFLICT_SKIP)
        self.assertTrue(res.get("skipped"))
        self.assertFalse(res["created"])

    def test_conflicto_overwrite_sin_confirmar_falla(self):
        self.client.create_note("Nota", body="a")
        with self.assertRaises(vault.ConflictError):
            self.client.create_note("Nota", body="b", on_conflict=vault.CONFLICT_OVERWRITE)

    def test_conflicto_overwrite_confirmado(self):
        self.client.create_note("Nota", body="a")
        res = self.client.create_note(
            "Nota", body="nuevo", on_conflict=vault.CONFLICT_OVERWRITE, confirmed=True
        )
        self.assertTrue(res["created"])
        text = (self.vault_dir / res["path"]).read_text(encoding="utf-8")
        self.assertIn("nuevo", text)

    def test_create_con_project_enlaza_bidireccional(self):
        # Given un proyecto, When create_note --project, Then la nota enlaza al contexto
        # y el contexto lista la nota (sin doble enlace).
        self.client.project_create("Ciencuadras")
        res = self.client.create_note("Hallazgo", body="x", project="Ciencuadras")
        nota = (self.vault_dir / res["path"]).read_text(encoding="utf-8")
        self.assertIn("[[_contexto-ciencuadras]]", nota)
        self.assertEqual(nota.count("[[_contexto-ciencuadras]]"), 1)  # no duplicado
        self.assertIn("project: ciencuadras", nota)
        contexto = (self.vault_dir / "proyectos" / "ciencuadras" / "_contexto-ciencuadras.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(f"[[{res['name']}]]", contexto)


class TestAppendNote(VaultTestCase):
    def test_append_no_toca_frontmatter(self):
        self.client.create_note("Nota", body="linea1", tags=["x"])
        self.client.append_note("nota", "linea2")
        text = (self.vault_dir / "inbox" / "nota.md").read_text(encoding="utf-8")
        self.assertIn("tags: [x]", text)
        self.assertIn("linea1", text)
        self.assertIn("linea2", text)

    def test_append_nota_inexistente_falla(self):
        with self.assertRaises(vault.NotFoundError):
            self.client.append_note("no-existe", "x")


class TestUpdateNote(VaultTestCase):
    def test_update_frontmatter_conserva_cuerpo(self):
        self.client.create_note("Nota", body="cuerpo original", tags=["a"])
        self.client.update_frontmatter("nota", {"estado": "activo", "tags": ["b"]})
        text = (self.vault_dir / "inbox" / "nota.md").read_text(encoding="utf-8")
        self.assertIn("estado: activo", text)
        self.assertIn("tags: [a, b]", text)  # union sin duplicar
        self.assertIn("cuerpo original", text)

    def test_update_body_sin_confirmar_falla(self):
        self.client.create_note("Nota", body="viejo")
        with self.assertRaises(vault.ConflictError):
            self.client.update_body("nota", "nuevo")

    def test_update_body_confirmado(self):
        self.client.create_note("Nota", body="viejo", tags=["keep"])
        self.client.update_body("nota", "nuevo", confirmed=True)
        text = (self.vault_dir / "inbox" / "nota.md").read_text(encoding="utf-8")
        self.assertIn("nuevo", text)
        self.assertNotIn("viejo", text)
        self.assertIn("tags: [keep]", text)  # frontmatter conservado


if __name__ == "__main__":
    unittest.main()
