"""Tests del CLI: dispatch, JSON vs --pretty, exit codes, dry-run y bloqueo de destructivas."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import obsidian_cli as cli  # noqa: E402
import vault  # noqa: E402


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        vault.init_vault(self.vault_dir)
        self.factory = lambda args: vault.VaultClient(self.vault_dir)

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, argv):
        """Ejecuta el CLI capturando stdout/stderr; devuelve (code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.run(argv, client_factory=self.factory)
        return code, out.getvalue(), err.getvalue()


class TestInit(unittest.TestCase):
    def test_init_por_cli(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli.run(["init", str(Path(tmp.name) / "v")])
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(out.getvalue())["created"])
        finally:
            tmp.cleanup()


class TestNoteCli(CliTestCase):
    def test_create_devuelve_json(self):
        code, out, _ = self._run(["note", "create", "Mi Nota", "--body", "hola", "--tag", "x"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertTrue(data["created"])
        self.assertEqual(data["name"], "mi-nota")

    def test_pretty_indenta(self):
        code, out, _ = self._run(["--pretty", "note", "create", "P"])
        self.assertEqual(code, 0)
        self.assertIn("\n  ", out)  # indentación

    def test_flag_global_despues_del_subcomando(self):
        # --pretty aceptado tras el subcomando (parser padre).
        code, out, _ = self._run(["note", "create", "Q", "--pretty"])
        self.assertEqual(code, 0)
        self.assertIn("\n  ", out)

    def test_update_body_sin_yes_es_conflicto(self):
        self._run(["note", "create", "Editable", "--body", "viejo"])
        code, _out, err = self._run(["note", "update", "editable", "--body", "nuevo"])
        self.assertEqual(code, cli.EXIT_CONFLICT)
        self.assertEqual(json.loads(err)["error"]["type"], "ConflictError")

    def test_update_body_con_yes(self):
        self._run(["note", "create", "Editable", "--body", "viejo"])
        code, _out, _err = self._run(["--yes", "note", "update", "editable", "--body", "nuevo"])
        self.assertEqual(code, 0)


class TestErrorsCli(CliTestCase):
    def test_nota_inexistente_exit_4(self):
        code, _out, err = self._run(["graph", "backlinks", "no-existe"])
        self.assertEqual(code, cli.EXIT_NOT_FOUND)
        self.assertEqual(json.loads(err)["error"]["type"], "NotFoundError")

    def test_ingest_sin_fuente_ni_stdin_no_aplica(self):
        # 'ingest' exige un argumento posicional; sin él, argparse sale con SystemExit(2).
        with self.assertRaises(SystemExit):
            self._run(["ingest"])


class TestDryRunCli(CliTestCase):
    def test_trash_dry_run_no_borra(self):
        self._run(["note", "create", "Temporal", "--body", "x"])
        code, out, _ = self._run(["--dry-run", "trash", "temporal"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["dry_run"])
        self.assertTrue((self.vault_dir / "inbox" / "temporal.md").exists())

    def test_trash_sin_yes_es_conflicto(self):
        self._run(["note", "create", "Temporal", "--body", "x"])
        code, _out, err = self._run(["trash", "temporal"])
        self.assertEqual(code, cli.EXIT_CONFLICT)


class TestFlowsCli(CliTestCase):
    def test_task_add_list_done(self):
        self._run(["task", "add", "hacer algo"])
        code, out, _ = self._run(["task", "list"])
        self.assertEqual(code, 0)
        self.assertIn("hacer algo", {t["text"] for t in json.loads(out)["tasks"]})
        self._run(["task", "done", "hacer algo"])
        code, out, _ = self._run(["task", "list"])
        self.assertNotIn("hacer algo", {t["text"] for t in json.loads(out)["tasks"]})

    def test_daily_add(self):
        code, out, _ = self._run(["daily", "--add", "trabajé en el skill", "--date", "2026-09-25"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["added"])

    def test_project_create_y_list(self):
        self._run(["project", "create", "Ciencuadras"])
        code, out, _ = self._run(["project", "list"])
        self.assertEqual(code, 0)
        self.assertIn("ciencuadras", {p["project"] for p in json.loads(out)["projects"]})

    def test_sources_list_vacio(self):
        code, out, _ = self._run(["sources", "list"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["count"], 0)


if __name__ == "__main__":
    unittest.main()
