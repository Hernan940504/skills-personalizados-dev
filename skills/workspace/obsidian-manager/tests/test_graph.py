"""Tests de grafo: backlinks, outlinks (con rotos) y huérfanas sobre vault real temporal."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import vault  # noqa: E402


class TestGraph(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        vault.init_vault(self.vault_dir)
        self.client = vault.VaultClient(self.vault_dir)
        # a -> b (existe) y a -> zzz (roto). b sin salidas. sola aislada.
        self.client.create_note("a", body="voy a [[b]] y a [[zzz]]")
        self.client.create_note("b", body="hoja")
        self.client.create_note("sola", body="aislada")

    def tearDown(self):
        self._tmp.cleanup()

    def test_backlinks(self):
        res = self.client.backlinks("b")
        self.assertEqual(res["backlinks"], ["a"])

    def test_outlinks_separa_rotos(self):
        res = self.client.outlinks("a")
        self.assertEqual(res["outlinks"], ["b"])
        self.assertEqual(res["broken"], ["zzz"])

    def test_orphans(self):
        res = self.client.orphans()
        # index.md y pendientes.md creados por init también podrían contar; validamos que 'sola' esté.
        self.assertIn("sola", res["orphans"])
        self.assertNotIn("a", res["orphans"])
        self.assertNotIn("b", res["orphans"])

    def test_backlinks_nota_inexistente_falla(self):
        with self.assertRaises(vault.NotFoundError):
            self.client.backlinks("no-existe")


if __name__ == "__main__":
    unittest.main()
