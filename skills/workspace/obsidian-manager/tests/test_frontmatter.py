"""Tests de frontmatter: round-trip, merge, subconjunto soportado y errores."""

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import frontmatter  # noqa: E402


class TestParse(unittest.TestCase):
    def test_sin_frontmatter_devuelve_body_intacto(self):
        # Given una nota sin bloque ---, When parse, Then frontmatter vacío y body igual.
        text = "# Título\n\nContenido sin frontmatter."
        fm, body = frontmatter.parse(text)
        self.assertEqual(fm, {})
        self.assertEqual(body, text)

    def test_parse_escalares_y_tipos(self):
        # Given frontmatter con tipos variados, When parse, Then tipos Python correctos.
        text = (
            "---\n"
            "title: Mi nota\n"
            "created: 2026-09-28\n"
            "prioridad: 3\n"
            "ratio: 0.5\n"
            "activo: true\n"
            "---\n"
            "Cuerpo\n"
        )
        fm, body = frontmatter.parse(text)
        self.assertEqual(fm["title"], "Mi nota")
        self.assertEqual(fm["created"], date(2026, 9, 28))
        self.assertEqual(fm["prioridad"], 3)
        self.assertEqual(fm["ratio"], 0.5)
        self.assertIs(fm["activo"], True)
        self.assertEqual(body, "Cuerpo\n")

    def test_parse_lista_inline(self):
        # Given tags inline, When parse, Then lista de strings.
        text = "---\ntags: [proyecto, ciencuadras, aws]\n---\ncuerpo"
        fm, _ = frontmatter.parse(text)
        self.assertEqual(fm["tags"], ["proyecto", "ciencuadras", "aws"])

    def test_parse_lista_en_bloque(self):
        # Given tags en bloque, When parse, Then lista equivalente.
        text = "---\ntags:\n  - proyecto\n  - ciencuadras\n---\ncuerpo"
        fm, _ = frontmatter.parse(text)
        self.assertEqual(fm["tags"], ["proyecto", "ciencuadras"])

    def test_parse_normaliza_crlf(self):
        # Given saltos CRLF, When parse, Then se procesa igual que LF.
        text = "---\r\ntitle: X\r\n---\r\ncuerpo\r\n"
        fm, body = frontmatter.parse(text)
        self.assertEqual(fm["title"], "X")
        self.assertEqual(body, "cuerpo\n")


class TestDump(unittest.TestCase):
    def test_dump_sin_frontmatter_devuelve_solo_body(self):
        self.assertEqual(frontmatter.dump({}, "solo cuerpo"), "solo cuerpo")

    def test_dump_incluye_delimitadores_y_lista(self):
        out = frontmatter.dump({"title": "X", "tags": ["a", "b"]}, "cuerpo")
        self.assertTrue(out.startswith("---\n"))
        self.assertIn("title: X", out)
        self.assertIn("tags: [a, b]", out)
        self.assertIn("\ncuerpo", out)


class TestRoundTrip(unittest.TestCase):
    def test_round_trip_preserva_campos(self):
        # Given una nota, When parse->dump->parse, Then los campos se conservan.
        original = (
            "---\n"
            "title: Contexto Ciencuadras\n"
            "tags: [proyecto, ciencuadras]\n"
            "created: 2026-09-28\n"
            "estado: activo\n"
            "---\n"
            "Cuerpo de la nota\ncon dos líneas\n"
        )
        fm1, body1 = frontmatter.parse(original)
        rebuilt = frontmatter.dump(fm1, body1)
        fm2, body2 = frontmatter.parse(rebuilt)
        self.assertEqual(fm1, fm2)
        self.assertEqual(body1, body2)


class TestMerge(unittest.TestCase):
    def test_merge_pisa_escalares(self):
        base = {"estado": "borrador", "title": "X"}
        out = frontmatter.merge(base, {"estado": "activo"})
        self.assertEqual(out["estado"], "activo")
        self.assertEqual(out["title"], "X")

    def test_merge_une_tags_sin_duplicar(self):
        base = {"tags": ["a", "b"]}
        out = frontmatter.merge(base, {"tags": ["b", "c"]})
        self.assertEqual(out["tags"], ["a", "b", "c"])

    def test_merge_no_muta_argumentos(self):
        base = {"tags": ["a"]}
        frontmatter.merge(base, {"tags": ["b"]})
        self.assertEqual(base["tags"], ["a"])


class TestUnsupported(unittest.TestCase):
    def test_multilinea_bloque_falla(self):
        text = "---\ndescripcion: |\n  linea1\n  linea2\n---\ncuerpo"
        with self.assertRaises(frontmatter.FrontmatterError):
            frontmatter.parse(text)

    def test_clave_duplicada_falla(self):
        text = "---\ntitle: A\ntitle: B\n---\ncuerpo"
        with self.assertRaises(frontmatter.FrontmatterError):
            frontmatter.parse(text)

    def test_linea_sin_dos_puntos_falla(self):
        text = "---\nesto no es valido\n---\ncuerpo"
        with self.assertRaises(frontmatter.FrontmatterError):
            frontmatter.parse(text)


if __name__ == "__main__":
    unittest.main()
