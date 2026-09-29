"""Tests de daily note y tareas: creación, add con timestamp, list global y filtros, done."""

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import vault  # noqa: E402


class TestDaily(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        vault.init_vault(self.vault_dir)
        self.client = vault.VaultClient(self.vault_dir)

    def tearDown(self):
        self._tmp.cleanup()

    def test_daily_crea_secciones(self):
        res = self.client.daily(day=date(2026, 9, 25))
        self.assertTrue(res["created"])
        text = (self.vault_dir / "daily" / "2026-09-25.md").read_text(encoding="utf-8")
        self.assertIn("## Trabajado", text)
        self.assertIn("## Pendientes", text)
        self.assertIn("## Notas", text)

    def test_daily_no_sobrescribe(self):
        self.client.daily(day=date(2026, 9, 25))
        self.client.daily_add("primera entrada", day=date(2026, 9, 25))
        res = self.client.daily(day=date(2026, 9, 25))
        self.assertFalse(res["created"])
        text = (self.vault_dir / "daily" / "2026-09-25.md").read_text(encoding="utf-8")
        self.assertIn("primera entrada", text)

    def test_daily_add_inserta_en_trabajado(self):
        self.client.daily_add("revisé rightsizing", day=date(2026, 9, 25))
        text = (self.vault_dir / "daily" / "2026-09-25.md").read_text(encoding="utf-8")
        self.assertIn("revisé rightsizing", text)
        # La entrada va bajo "## Trabajado".
        trabajado = text.split("## Trabajado")[1].split("## Pendientes")[0]
        self.assertIn("revisé rightsizing", trabajado)

    def test_daily_add_con_project_enlaza(self):
        self.client.project_create("Ciencuadras")
        self.client.daily_add("avance CC", day=date(2026, 9, 25), project="Ciencuadras")
        text = (self.vault_dir / "daily" / "2026-09-25.md").read_text(encoding="utf-8")
        self.assertIn("[[_contexto-ciencuadras]]", text)


class TestTasks(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        vault.init_vault(self.vault_dir)
        self.client = vault.VaultClient(self.vault_dir)

    def tearDown(self):
        self._tmp.cleanup()

    def test_task_add_global(self):
        self.client.task_add("comprar dominio")
        text = (self.vault_dir / "pendientes.md").read_text(encoding="utf-8")
        self.assertIn("- [ ] comprar dominio", text)

    def test_task_add_proyecto(self):
        self.client.project_create("Ciencuadras")
        self.client.task_add("validar CIDR", project="Ciencuadras")
        text = (self.vault_dir / "proyectos" / "ciencuadras" / "_contexto-ciencuadras.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("- [ ] validar CIDR", text)

    def test_task_add_proyecto_inexistente_falla(self):
        with self.assertRaises(vault.NotFoundError):
            self.client.task_add("x", project="NoExiste")

    def test_task_add_proyecto_deja_newline_final(self):
        # Insertar en una sección que es la última del archivo debe dejar newline final.
        self.client.project_create("P1")
        self.client.task_add("primera", project="P1")
        text = (self.vault_dir / "proyectos" / "p1" / "_contexto-p1.md").read_text(encoding="utf-8")
        self.assertTrue(text.endswith("\n"))

    def test_task_list_recolecta_todo_el_vault(self):
        self.client.task_add("tarea global")
        self.client.project_create("P1")
        self.client.task_add("tarea proyecto", project="P1")
        res = self.client.task_list()
        textos = {t["text"] for t in res["tasks"]}
        self.assertIn("tarea global", textos)
        self.assertIn("tarea proyecto", textos)

    def test_task_list_filtra_por_proyecto(self):
        self.client.task_add("global")
        self.client.project_create("P1")
        self.client.task_add("del proyecto", project="P1")
        res = self.client.task_list(project="P1")
        textos = {t["text"] for t in res["tasks"]}
        self.assertEqual(textos, {"del proyecto"})

    def test_task_done_marca_completada(self):
        self.client.task_add("cerrar esto")
        self.client.task_done("cerrar esto")
        text = (self.vault_dir / "pendientes.md").read_text(encoding="utf-8")
        self.assertIn("- [x] cerrar esto", text)

    def test_task_list_excluye_cerradas_por_defecto(self):
        self.client.task_add("abierta")
        self.client.task_add("a cerrar")
        self.client.task_done("a cerrar")
        abiertas = {t["text"] for t in self.client.task_list()["tasks"]}
        self.assertIn("abierta", abiertas)
        self.assertNotIn("a cerrar", abiertas)
        con_cerradas = {t["text"] for t in self.client.task_list(include_done=True)["tasks"]}
        self.assertIn("a cerrar", con_cerradas)

    def test_task_done_sin_coincidencia_falla(self):
        with self.assertRaises(vault.NotFoundError):
            self.client.task_done("no-existe")


if __name__ == "__main__":
    unittest.main()
