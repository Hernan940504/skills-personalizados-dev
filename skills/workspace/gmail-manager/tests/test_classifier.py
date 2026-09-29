"""Tests del clasificador de criticidad y la redacción de secretos (sin red)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import classifier  # noqa: E402


class TestClassify(unittest.TestCase):
    def test_ruido_es_baja(self):
        # Given un remitente no-reply, When classify, Then baja.
        c = classifier.classify("noreply@atlassian.net", "[JIRA] build passed", "…")
        self.assertEqual(c.level, "baja")

    def test_senal_alta_por_decision(self):
        # Given asunto con 'decisión'/'producción', Then alta.
        c = classifier.classify("jefe@segurosbolivar.com", "Decisión de arquitectura producción",
                                 "definimos el nuevo esquema")
        self.assertEqual(c.level, "alta")

    def test_compromiso_dirigido_es_alta(self):
        # Given un correo que asigna un compromiso al usuario, Then alta + compromiso.
        c = classifier.classify(
            "pm@segurosbolivar.com", "Pendientes",
            "Hernán, necesito que envíes el informe a más tardar el viernes",
            user_email="hernan.betancur@segurosbolivar.com",
            recipients="hernan.betancur@segurosbolivar.com",
        )
        self.assertEqual(c.level, "alta")
        self.assertIsNotNone(c.commitment)

    def test_compromiso_vence_al_ruido(self):
        # Given ruido en el asunto pero compromiso dirigido, Then alta (compromiso gana).
        c = classifier.classify(
            "noreply@x.com", "newsletter",
            "por favor revisa y confirma el acceso",
            user_email="h@x.com", recipients="h@x.com",
        )
        self.assertEqual(c.level, "alta")

    def test_contexto_negocio_es_media(self):
        # Given un correo normal de la línea sin señales de alta, Then media.
        c = classifier.classify("colega@segurosbolivar.com", "Avance semanal",
                                 "seguimos con el desarrollo del cotizador")
        self.assertEqual(c.level, "media")

    def test_senal_fuerte_sola_es_alta(self):
        # Given un incidente (señal fuerte), Then alta aunque sea lo único.
        c = classifier.classify("ops@segurosbolivar.com", "Incidente en el servicio",
                                 "reporte del incidente de anoche")
        self.assertEqual(c.level, "alta")

    def test_una_senal_debil_sola_es_media(self):
        # Given una sola palabra débil ('acceso'), Then media (ya no alta).
        c = classifier.classify("colega@segurosbolivar.com", "Consulta",
                                 "necesito revisar el acceso al panel")
        self.assertEqual(c.level, "media")

    def test_dos_senales_debiles_es_alta(self):
        # Given dos débiles ('producción' + 'migración'), Then alta.
        c = classifier.classify("colega@segurosbolivar.com", "Plan",
                                 "la migración a producción del cotizador")
        self.assertEqual(c.level, "alta")

    def test_compromiso_sin_direccionar_no_es_alta(self):
        # Given verbos de compromiso pero el usuario NO está direccionado, Then no alta.
        c = classifier.classify(
            "pm@segurosbolivar.com", "Tareas del equipo",
            "necesito que Juan envíe el informe",
            user_email="hernan.betancur@segurosbolivar.com", recipients="otro@x.com",
        )
        self.assertNotEqual(c.level, "alta")


class TestRedact(unittest.TestCase):
    def test_redacta_password_y_token(self):
        red = classifier.redact("password: P@ss123 y token=abc.def.ghi")
        self.assertNotIn("P@ss123", red)
        self.assertNotIn("abc.def.ghi", red)
        self.assertIn("<redacted>", red)

    def test_redacta_aws_key_y_private_key(self):
        self.assertIn("<redacted-aws-key>", classifier.redact("AKIAIOSFODNN7EXAMPLE"))
        self.assertIn("<redacted-private-key>",
                      classifier.redact("-----BEGIN RSA PRIVATE KEY-----"))

    def test_redacta_tarjeta(self):
        self.assertIn("<redacted-card>", classifier.redact("pago 4111 1111 1111 1111"))


if __name__ == "__main__":
    unittest.main()
