"""Tests de ingesta: texto, markdown (fusión frontmatter), binario, stdin, project/link, dry-run."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import vault  # noqa: E402


class TestIngest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_dir = Path(self._tmp.name) / "vault"
        vault.init_vault(self.vault_dir)
        self.client = vault.VaultClient(self.vault_dir)
        self.ext = Path(self._tmp.name) / "externos"
        self.ext.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def test_ingesta_stdin(self):
        res = self.client.ingest(stdin_text="captura rápida", title="Idea suelta")
        self.assertTrue(res["created"])
        text = (self.vault_dir / res["path"]).read_text(encoding="utf-8")
        self.assertIn("captura rápida", text)
        self.assertIn("source: stdin", text)

    def test_ingesta_markdown_fusiona_frontmatter(self):
        md = self.ext / "doc.md"
        md.write_text("---\ntags: [origen]\nautor: Hernan\n---\nContenido MD", encoding="utf-8")
        res = self.client.ingest(source_path=str(md), tags=["ingesta"])
        text = (self.vault_dir / res["path"]).read_text(encoding="utf-8")
        self.assertIn("Contenido MD", text)
        self.assertIn("autor: Hernan", text)      # frontmatter existente preservado
        self.assertIn("origen", text)              # tag original
        self.assertIn("ingesta", text)             # tag añadido
        self.assertIn("source:", text)

    def test_ingesta_binario_copia_y_crea_indice(self):
        pdf = self.ext / "informe.pdf"
        pdf.write_bytes(b"%PDF-1.4\x00\x00binario")
        res = self.client.ingest(source_path=str(pdf))
        # Adjunto copiado.
        self.assertTrue((self.vault_dir / "referencias" / "adjuntos" / "informe.pdf").exists())
        # Nota-índice con embed.
        text = (self.vault_dir / res["path"]).read_text(encoding="utf-8")
        self.assertIn("![[informe.pdf]]", text)
        self.assertEqual(res["attachment"], "referencias/adjuntos/informe.pdf")

    def test_ingesta_con_project_enlaza_contexto(self):
        # Given un proyecto existente, When ingest --project, Then la nota enlaza al contexto
        # y el contexto lista la nota.
        self.client.project_create("Ciencuadras")
        res = self.client.ingest(stdin_text="hallazgo", title="Nota CC", project="Ciencuadras")
        nota = (self.vault_dir / res["path"]).read_text(encoding="utf-8")
        self.assertIn("[[_contexto-ciencuadras]]", nota)
        contexto = (self.vault_dir / "proyectos" / "ciencuadras" / "_contexto-ciencuadras.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(f"[[{res['name']}]]", contexto)

    def test_ingesta_drawio_va_como_adjunto_no_como_cuerpo(self):
        # Un .drawio es XML (texto) pero debe tratarse como adjunto, no embeberse como cuerpo.
        drawio = self.ext / "diagrama.drawio"
        drawio.write_text("<mxfile><diagram>contenido xml</diagram></mxfile>", encoding="utf-8")
        res = self.client.ingest(source_path=str(drawio), title="Diagrama")
        self.assertTrue((self.vault_dir / "referencias" / "adjuntos" / "diagrama.drawio").exists())
        text = (self.vault_dir / res["path"]).read_text(encoding="utf-8")
        self.assertIn("![[diagrama.drawio]]", text)
        self.assertNotIn("<mxfile>", text)  # el XML NO va en el cuerpo de la nota

    def test_ingesta_con_links(self):
        self.client.create_note("Destino")
        res = self.client.ingest(stdin_text="x", title="Origen", links=["destino"])
        text = (self.vault_dir / res["path"]).read_text(encoding="utf-8")
        self.assertIn("[[destino]]", text)

    def test_dry_run_no_escribe(self):
        antes = list((self.vault_dir / "inbox").glob("*.md"))
        res = self.client.ingest(stdin_text="x", title="NoEscribe", dry_run=True)
        despues = list((self.vault_dir / "inbox").glob("*.md"))
        self.assertTrue(res["dry_run"])
        self.assertEqual(len(antes), len(despues))

    def test_sin_fuente_ni_stdin_falla(self):
        with self.assertRaises(ValueError):
            self.client.ingest()

    def test_archivo_inexistente_falla(self):
        with self.assertRaises(vault.NotFoundError):
            self.client.ingest(source_path=str(self.ext / "no-existe.txt"))


if __name__ == "__main__":
    unittest.main()
