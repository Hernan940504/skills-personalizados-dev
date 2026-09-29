"""Tests del flujo por hilo: clasificación por criticidad máxima, limpieza y resumen sin basura."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import classifier  # noqa: E402


def _thread(subject, messages):
    return {
        "threadId": "t1", "subject": subject, "thread_url": "https://mail/x",
        "participants": [m["sender"] for m in messages],
        "messages": messages,
    }


class TestClassifyThread(unittest.TestCase):
    def test_toma_criticidad_maxima_del_hilo(self):
        # Given un hilo cuyo 2º mensaje es un incidente, Then el hilo es alta.
        th = _thread("Re: seguimiento", [
            {"sender": "a@x.com", "subject": "seguimiento", "body": "avance normal", "to": ""},
            {"sender": "b@x.com", "subject": "Re: seguimiento", "body": "hay un incidente en el servicio", "to": ""},
        ])
        cls, best = classifier.classify_thread(th)
        self.assertEqual(cls.level, "alta")
        self.assertIn("incidente", best["body"])

    def test_hilo_trivial_es_media_o_baja(self):
        th = _thread("saludo", [{"sender": "a@x.com", "subject": "saludo", "body": "buenos días", "to": ""}])
        cls, _ = classifier.classify_thread(th)
        self.assertIn(cls.level, ("media", "baja"))


class TestCleanBody(unittest.TestCase):
    def test_quita_citas_y_reenvios(self):
        raw = "Mi mensaje real\n> texto citado anterior\nEl 3 de sep escribió:\nfrom: alguien"
        out = classifier.clean_body(raw)
        self.assertIn("Mi mensaje real", out)
        self.assertNotIn("texto citado anterior", out)
        self.assertNotIn("escribió:", out)

    def test_redacta_y_acota(self):
        out = classifier.clean_body("password: SECRETO123 aquí", max_chars=1000)
        self.assertNotIn("SECRETO123", out)
        self.assertIn("<redacted>", out)

    def test_vacio_devuelve_vacio(self):
        self.assertEqual(classifier.clean_body(""), "")
        self.assertEqual(classifier.clean_body("> solo cita\n> mas cita"), "")


class TestSummarizeThread(unittest.TestCase):
    def test_resumen_con_contenido(self):
        th = _thread("Decisión", [
            {"sender": "a@x.com", "subject": "Decisión", "body": "definimos migrar a producción", "to": ""},
        ])
        cls, best = classifier.classify_thread(th)
        body = classifier.summarize_thread(th, cls, best)
        self.assertIn("## Contenido", body)
        self.assertIn("migrar a producción", body)
        self.assertIn("Enlace: https://mail/x", body)

    def test_sin_contenido_devuelve_vacio(self):
        # Un hilo cuyo cuerpo son solo citas → summarize devuelve "" (no se crea nota).
        th = _thread("x", [{"sender": "a@x.com", "subject": "x", "body": "> solo cita", "to": ""}])
        cls, best = classifier.classify_thread(th)
        self.assertEqual(classifier.summarize_thread(th, cls, best), "")


if __name__ == "__main__":
    unittest.main()
