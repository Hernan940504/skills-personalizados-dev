"""Tests de proyectos (note/list) y orquestación de fuentes con runner inyectado (sin subprocess)."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import sources  # noqa: E402
import vault  # noqa: E402


class TestProjects(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        vault.init_vault(self.vault_dir)
        self.client = vault.VaultClient(self.vault_dir)

    def tearDown(self):
        self._tmp.cleanup()

    def test_project_create_genera_contexto(self):
        res = self.client.project_create("Ciencuadras", status="activo")
        self.assertTrue(res["created"])
        text = (self.vault_dir / "proyectos" / "ciencuadras" / "_contexto-ciencuadras.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("estado: activo", text)
        self.assertIn("## Decisiones", text)

    def test_project_create_idempotente(self):
        self.client.project_create("P1")
        res = self.client.project_create("P1")
        self.assertFalse(res["created"])

    def test_project_note_agrega_entrada_fechada(self):
        self.client.project_create("P1")
        self.client.project_note("P1", "decisión importante", section="Decisiones")
        text = (self.vault_dir / "proyectos" / "p1" / "_contexto-p1.md").read_text(encoding="utf-8")
        deciciones = text.split("## Decisiones")[1]
        self.assertIn("decisión importante", deciciones)

    def test_project_note_proyecto_inexistente_falla(self):
        with self.assertRaises(vault.NotFoundError):
            self.client.project_note("NoExiste", "x")

    def test_project_list_lee_estado(self):
        self.client.project_create("Alpha", status="activo")
        self.client.project_create("Beta", status="pausado")
        res = self.client.project_list()
        estados = {p["project"]: p["estado"] for p in res["projects"]}
        self.assertEqual(estados.get("alpha"), "activo")
        self.assertEqual(estados.get("beta"), "pausado")


class TestSources(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        vault.init_vault(self.vault_dir)
        self.client = vault.VaultClient(self.vault_dir)
        self.repo_root = Path(self._tmp.name) / "repo"
        self.repo_root.mkdir()
        # Material externo que el "skill fuente" habría descargado.
        self.material = Path(self._tmp.name) / "material.md"
        self.material.write_text("---\ntags: [origen]\n---\ncontenido descargado", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _write_sources(self, sources_list):
        path = self.vault_dir / ".brain" / "fuentes.json"
        path.write_text(json.dumps({"sources": sources_list}), encoding="utf-8")

    def test_list_sources(self):
        self._write_sources([
            {"name": "drive-proyectos", "description": "Drive", "skill_path": "x/cli.py"}
        ])
        res = sources.list_sources(self.client)
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["sources"][0]["name"], "drive-proyectos")
        self.assertEqual(res["sources"][0]["status"], "declarada")

    def test_sync_invoca_skill_e_ingiere(self):
        # Given una fuente cuyo skill "devuelve" la ruta del material,
        self._write_sources([{
            "name": "drive-proyectos",
            "skill_path": "skills/x/cli.py",
            "command": ["download", "FID"],
            "map": {"content_from": "downloaded", "project": None, "tags": ["drive"]},
        }])

        captured = {}

        def fake_runner(argv):
            captured["argv"] = argv
            return json.dumps({"downloaded": str(self.material)})

        # When sync con runner inyectado (sin subprocess real),
        res = sources.sync(
            self.client, "drive-proyectos", repo_root=self.repo_root, runner=fake_runner
        )
        # Then se ingirió el material y el argv apuntó al skill fuente.
        self.assertEqual(res["count"], 1)
        self.assertIn("skills/x/cli.py", captured["argv"][1])
        note_path = self.vault_dir / res["ingested"][0]["path"]
        self.assertIn("contenido descargado", note_path.read_text(encoding="utf-8"))

    def test_sync_dry_run_no_invoca(self):
        self._write_sources([{
            "name": "s1", "skill_path": "skills/x/cli.py", "command": ["run"], "map": {}
        }])
        called = {"n": 0}

        def runner(argv):
            called["n"] += 1
            return "{}"

        res = sources.sync(self.client, "s1", repo_root=self.repo_root, dry_run=True, runner=runner)
        self.assertTrue(res["dry_run"])
        self.assertEqual(called["n"], 0)

    def test_sync_fuente_inexistente_falla(self):
        self._write_sources([])
        with self.assertRaises(sources.SourceError):
            sources.sync(self.client, "no-existe", repo_root=self.repo_root, runner=lambda a: "{}")

    def test_sync_fallo_de_skill_es_aislado(self):
        self._write_sources([{
            "name": "s1", "skill_path": "skills/x/cli.py", "command": [], "map": {}
        }])

        def failing_runner(argv):
            raise RuntimeError("skill reventó")

        # El fallo se envuelve en SourceError; el vault no se corrompe (no se ingirió nada).
        with self.assertRaises(sources.SourceError):
            sources.sync(self.client, "s1", repo_root=self.repo_root, runner=failing_runner)
        notas = list((self.vault_dir / "inbox").glob("*.md"))
        self.assertEqual(notas, [])

    def test_sync_json_invalido_falla(self):
        self._write_sources([{
            "name": "s1", "skill_path": "skills/x/cli.py", "command": [], "map": {}
        }])
        with self.assertRaises(sources.SourceError):
            sources.sync(self.client, "s1", repo_root=self.repo_root, runner=lambda a: "no json")

    def test_fuentes_json_corrupto_falla(self):
        (self.vault_dir / ".brain" / "fuentes.json").write_text("{ roto", encoding="utf-8")
        with self.assertRaises(sources.SourceError):
            sources.list_sources(self.client)


if __name__ == "__main__":
    unittest.main()
