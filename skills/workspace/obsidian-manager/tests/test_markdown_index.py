"""Tests de markdown_index: wikilinks, tags, grafo, alias, rotos y huérfanas."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import markdown_index as mi  # noqa: E402


class TestWikilinks(unittest.TestCase):
    def test_extrae_simple_y_con_alias(self):
        body = "Ver [[Nota A]] y [[Nota B|alias visible]]."
        self.assertEqual(mi.extract_wikilinks(body), ["Nota A", "Nota B"])

    def test_ignora_seccion(self):
        body = "Ref [[Nota A#Seccion]]"
        self.assertEqual(mi.extract_wikilinks(body), ["Nota A"])

    def test_sin_duplicados_preserva_orden(self):
        body = "[[B]] [[A]] [[B]]"
        self.assertEqual(mi.extract_wikilinks(body), ["B", "A"])


class TestTags(unittest.TestCase):
    def test_tags_de_frontmatter_lista(self):
        tags = mi.extract_tags({"tags": ["proyecto", "aws"]}, "cuerpo")
        self.assertEqual(tags, {"proyecto", "aws"})

    def test_tags_inline(self):
        tags = mi.extract_tags({}, "trabajo en #ciencuadras y #aws hoy")
        self.assertEqual(tags, {"ciencuadras", "aws"})

    def test_ignora_encabezado_markdown(self):
        # "# Título" es un heading, no un tag (hay espacio tras #).
        tags = mi.extract_tags({}, "# Título\n\ncontenido")
        self.assertEqual(tags, set())

    def test_ignora_tag_en_code(self):
        body = "texto `#nocuenta` y ```\n#tampoco\n``` pero #si_cuenta"
        tags = mi.extract_tags({}, body)
        self.assertIn("si_cuenta", tags)
        self.assertNotIn("nocuenta", tags)
        self.assertNotIn("tampoco", tags)

    def test_tag_jerarquico(self):
        tags = mi.extract_tags({}, "clasifico con #area/infra")
        self.assertIn("area/infra", tags)


class TestBuildIndex(unittest.TestCase):
    def _notes(self):
        return {
            "A": "---\naliases: [Alfa]\n---\nEnlaza a [[B]] y a [[Inexistente]]",
            "B": "Enlaza a [[A]] via alias [[Alfa]]",
            "C": "Nota aislada sin enlaces",
        }

    def test_outlinks_resueltos(self):
        index = mi.build_index(self._notes())
        self.assertEqual(index.outlinks["A"], ["B"])
        # B enlaza a A directo y por alias Alfa -> ambos resuelven a A (sin duplicar).
        self.assertEqual(index.outlinks["B"], ["A"])

    def test_backlinks_invertidos(self):
        index = mi.build_index(self._notes())
        self.assertEqual(index.backlinks["A"], ["B"])
        self.assertEqual(index.backlinks["B"], ["A"])

    def test_enlace_roto_marcado(self):
        index = mi.build_index(self._notes())
        self.assertIn("Inexistente", index.broken["A"])

    def test_alias_registrado(self):
        index = mi.build_index(self._notes())
        self.assertEqual(index.aliases.get("Alfa"), "A")

    def test_frontmatter_invalido_no_rompe_indice(self):
        notes = {"X": "---\ntitle: A\ntitle: B\n---\ncuerpo [[Y]]", "Y": "ok"}
        index = mi.build_index(notes)  # no debe lanzar
        self.assertIn("X", index.names)
        self.assertEqual(index.outlinks["X"], ["Y"])


class TestResolveLink(unittest.TestCase):
    def test_resuelve_por_nombre_y_alias(self):
        index = mi.build_index({"A": "---\naliases: [Alfa]\n---\n", "B": "cuerpo"})
        self.assertEqual(mi.resolve_link("A", index), "A")
        self.assertEqual(mi.resolve_link("Alfa", index), "A")
        self.assertIsNone(mi.resolve_link("Nope", index))


class TestOrphans(unittest.TestCase):
    def test_detecta_huerfana(self):
        notes = {
            "A": "[[B]]",
            "B": "cuerpo",
            "Sola": "nota sin enlaces entrantes ni salientes",
        }
        index = mi.build_index(notes)
        self.assertEqual(mi.orphans(index), ["Sola"])


if __name__ == "__main__":
    unittest.main()
