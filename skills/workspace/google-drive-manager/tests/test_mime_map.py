"""Tests de mime_map: defaults, formatos inválidos y conversión de subida."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import mime_map  # noqa: E402


class TestDefaultExport(unittest.TestCase):
    def test_default_por_tipo(self):
        # Given/When/Then: cada tipo Google tiene su default esperado.
        self.assertEqual(mime_map.default_export(mime_map.GOOGLE_DOC), "docx")
        self.assertEqual(mime_map.default_export(mime_map.GOOGLE_SHEET), "xlsx")
        self.assertEqual(mime_map.default_export(mime_map.GOOGLE_SLIDES), "pptx")
        self.assertEqual(mime_map.default_export(mime_map.GOOGLE_DRAWING), "pdf")

    def test_default_tipo_sin_soporte(self):
        # Given un MIME no exportable, When default_export, Then error.
        with self.assertRaises(mime_map.UnsupportedExportFormatError):
            mime_map.default_export("application/octet-stream")


class TestResolveExport(unittest.TestCase):
    def test_resuelve_default_cuando_fmt_none(self):
        # Given un Doc sin formato, When resolve, Then usa docx.
        mime, ext = mime_map.resolve_export(mime_map.GOOGLE_DOC, None)
        self.assertIn("wordprocessingml", mime)
        self.assertEqual(ext, ".docx")

    def test_resuelve_formato_explicito(self):
        # Given un Sheet a csv, When resolve, Then MIME y extensión csv.
        mime, ext = mime_map.resolve_export(mime_map.GOOGLE_SHEET, "csv")
        self.assertEqual(mime, "text/csv")
        self.assertEqual(ext, ".csv")

    def test_formato_invalido_lista_validos(self):
        # Given un Slides a csv (no soportado), When resolve, Then error con válidos.
        with self.assertRaises(mime_map.UnsupportedExportFormatError) as ctx:
            mime_map.resolve_export(mime_map.GOOGLE_SLIDES, "csv")
        msg = str(ctx.exception)
        self.assertIn("pptx", msg)
        self.assertIn("pdf", msg)

    def test_tipo_no_exportable(self):
        with self.assertRaises(mime_map.UnsupportedExportFormatError):
            mime_map.resolve_export("application/pdf", "pdf")


class TestConvertTarget(unittest.TestCase):
    def test_docx_convierte_a_google_doc(self):
        target = mime_map.convert_target(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        self.assertEqual(target, mime_map.GOOGLE_DOC)

    def test_csv_convierte_a_google_sheet(self):
        self.assertEqual(mime_map.convert_target("text/csv"), mime_map.GOOGLE_SHEET)

    def test_mime_desconocido_devuelve_none(self):
        self.assertIsNone(mime_map.convert_target("application/zip"))


class TestHelpers(unittest.TestCase):
    def test_is_google_native(self):
        self.assertTrue(mime_map.is_google_native(mime_map.GOOGLE_DOC))
        self.assertFalse(mime_map.is_google_native("application/pdf"))

    def test_is_folder(self):
        self.assertTrue(mime_map.is_folder(mime_map.GOOGLE_FOLDER))
        self.assertFalse(mime_map.is_folder(mime_map.GOOGLE_DOC))


if __name__ == "__main__":
    unittest.main()
