"""Tests de búsqueda: texto, tag, links-to, filtro de carpeta y truncado."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import vault  # noqa: E402


class TestSearch(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        vault.init_vault(self.vault_dir)
        self.client = vault.VaultClient(self.vault_dir)
        # Notas de prueba. El wikilink usa el nombre real del archivo (slug).
        self.client.create_note("Alpha", body="habla de rightsizing y AWS", tags=["infra"])
        self.client.create_note("Beta", body="Enlaza a [[alpha]] aquí", tags=["proyecto"])
        self.client.create_note("Gamma", body="sin relación", tags=["infra"])

    def tearDown(self):
        self._tmp.cleanup()

    def test_busqueda_por_texto_con_snippet(self):
        res = self.client.search(text="rightsizing")
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["results"][0]["name"], "alpha")
        self.assertIn("rightsizing", res["results"][0]["snippet"])

    def test_busqueda_por_tag(self):
        res = self.client.search(tag="infra")
        names = {r["name"] for r in res["results"]}
        self.assertEqual(names, {"alpha", "gamma"})

    def test_busqueda_links_to_backlinks(self):
        res = self.client.search(links_to="alpha")
        self.assertEqual([r["name"] for r in res["results"]], ["beta"])

    def test_criterios_and(self):
        # tag infra AND texto 'AWS' -> solo alpha.
        res = self.client.search(tag="infra", text="AWS")
        self.assertEqual([r["name"] for r in res["results"]], ["alpha"])

    def test_cero_resultados_lista_vacia(self):
        res = self.client.search(text="no-existe-esto")
        self.assertEqual(res["count"], 0)
        self.assertEqual(res["results"], [])

    def test_filtro_por_carpeta(self):
        self.client.create_note("EnProyectos", body="AWS", folder="proyectos")
        res = self.client.search(text="AWS", folder="proyectos")
        self.assertEqual([r["name"] for r in res["results"]], ["enproyectos"])

    def test_truncado_marca_flag(self):
        for i in range(5):
            self.client.create_note(f"Doc{i}", body="comun palabra")
        res = self.client.search(text="comun", limit=2)
        self.assertTrue(res["truncated"])
        self.assertEqual(res["count"], 2)
        self.assertGreaterEqual(res["total_matches"], 5)


if __name__ == "__main__":
    unittest.main()
