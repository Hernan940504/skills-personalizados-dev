"""Tests del generador de notas de repo (repo_note): deps, OpenAPI, proxy, nota completa."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import repo_note  # noqa: E402


class TestDependencies(unittest.TestCase):
    def test_detecta_mysql_redis_sqs_elastic(self):
        gradle = """
        implementation 'mysql:mysql-connector-java'
        implementation 'redis.clients:jedis:3.6.3'
        implementation 'com.amazonaws:aws-java-sdk-sqs:1.12'
        implementation 'co.elastic.clients:elasticsearch-java:8.3.3'
        implementation 'com.ciencuadras:ssm-store:+'
        """
        deps = repo_note.parse_dependencies(gradle)
        self.assertIn("MySQL (Aurora)", deps["datos"])
        self.assertIn("Redis", deps["datos"])
        self.assertIn("ElasticSearch", deps["datos"])
        self.assertIn("SQS", deps["mensajeria"])
        aws = repo_note.aws_resources(gradle)
        self.assertTrue(any("MySQL" in a for a in aws))
        self.assertIn("ssm-store", repo_note.common_libs(gradle))

    def test_detecta_http_y_externos(self):
        gradle = "implementation 'com.squareup.retrofit2:retrofit'\nimplementation 'com.google.firebase:firebase-admin:8.0.1'"
        deps = repo_note.parse_dependencies(gradle)
        self.assertIn("http", deps)
        self.assertIn("Firebase", deps["externo"])

    def test_detect_stack(self):
        gradle = "id 'org.springframework.boot' version '2.7.18'\nsourceCompatibility = '11'"
        s = repo_note.detect_stack(gradle, "build.gradle")
        self.assertIn("Java 11", s)
        self.assertIn("Spring Boot 2.7.18", s)


class TestOpenAPI(unittest.TestCase):
    def test_parse_paths_json(self):
        spec = {
            "paths": {
                "/leads/v1/lead": {
                    "post": {
                        "summary": "Guarda lead",
                        "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/LeadBodyRequest"}}}},
                        "responses": {"200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/ResponseDTO"}}}}},
                    }
                }
            }
        }
        eps = repo_note.parse_openapi_paths(spec)
        self.assertEqual(len(eps), 1)
        self.assertEqual(eps[0]["method"], "POST")
        self.assertEqual(eps[0]["request"], "LeadBodyRequest")
        self.assertEqual(eps[0]["response"], "ResponseDTO")

    def test_detecta_proxy(self):
        spec = {"paths": {"/auth/{proxy+}": {"get": {}, "post": {}}}}
        eps = repo_note.parse_openapi_paths(spec)
        self.assertTrue(repo_note.is_proxy_spec(eps))

    def test_mini_yaml_openapi(self):
        yaml = (
            "openapi: 3.0.0\n"
            "paths:\n"
            "  /publications/v1/promote:\n"
            "    post:\n"
            "      summary: Marca inmueble\n"
            "  /publications/v1/delete:\n"
            "    post:\n"
            "      operationId: deleteProperty\n"
        )
        spec = repo_note._mini_yaml_openapi(yaml)
        eps = repo_note.parse_openapi_paths(spec)
        paths = {e["path"] for e in eps}
        self.assertIn("/publications/v1/promote", paths)
        self.assertIn("/publications/v1/delete", paths)


class TestBuildNote(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_nota_completa_con_openapi_y_gradle(self):
        (self.d / "build.gradle").write_text(
            "id 'org.springframework.boot' version '2.4.5'\nsourceCompatibility = '11'\n"
            "implementation 'mysql:mysql-connector-java'\nimplementation 'redis.clients:jedis'\n"
            "implementation 'com.amazonaws:aws-java-sdk-sqs'\nimplementation 'com.ciencuadras:ssm-store:+'",
            encoding="utf-8")
        (self.d / "README.md").write_text(
            "# demo-ms\n## Descripción\nMicroservicio de demostración que hace X.\n", encoding="utf-8")
        (self.d / "api_spec.yaml").write_text(
            "openapi: 3.0.0\npaths:\n  /demo/v1/do:\n    post:\n      summary: Hace algo\n",
            encoding="utf-8")
        out = self.d / "nota.md"
        repo_note.build_note  # sanity
        note = repo_note.build_note(self.d, "segurosbolivar/demo-ms",
                                    ecs="ciencuadras-prod-java-demo-ms", tags=["demo"], project="ciencuadras")
        self.assertIn("title: Repo — demo-ms", note)
        self.assertIn("Spring Boot 2.4.5", note)
        self.assertIn("Microservicio de demostración", note)
        self.assertIn("/demo/v1/do", note)
        self.assertIn("MySQL (Aurora)", note)
        self.assertIn("ssm-store", note)
        self.assertIn("ciencuadras-prod-java-demo-ms", note)
        self.assertIn("[[contexto-aws-cuenta-legada-ciencuadras-290296201161]]", note)

    def test_proxy_incrusta_seccion_readme(self):
        (self.d / "build.gradle").write_text("implementation 'com.google.firebase:firebase-admin'", encoding="utf-8")
        (self.d / "api_spec.yaml").write_text(
            "openapi: 3.0.0\npaths:\n  /auth/{proxy+}:\n    get:\n    post:\n", encoding="utf-8")
        (self.d / "README.md").write_text(
            "# auth-ms\n## Descripción\nAuth.\n## Endpoints\n### Login\n"
            "Método: POST\n- PROD: https://api-backend.ciencuadras.com/prod/auth/v1/login\n"
            "```json\n{\"username\":\"x\",\"password\":\"y\"}\n```\n## Autores\nZeus\n",
            encoding="utf-8")
        note = repo_note.build_note(self.d, "segurosbolivar/auth-ms", ecs=None, tags=[], project="ciencuadras")
        self.assertIn("Fuente: README", note)
        self.assertIn("### Login", note)               # sección incrustada tal cual
        self.assertIn("/auth/v1/login", note)
        self.assertIn('"username"', note)               # ejemplo JSON preservado
        self.assertNotIn("## Autores", note)            # cortó antes de Autores
        self.assertIn("Firebase", note)

    def test_extract_readme_endpoints_section(self):
        readme = ("# x\n>## Endpoints\n-- --------\n### Ruta A\nMétodo: GET\n"
                  "-- --------\n>## Versionamiento\nblah\n")
        sec = repo_note.extract_readme_endpoints_section(readme)
        self.assertIn("### Ruta A", sec)
        self.assertNotIn("Versionamiento", sec)

    def test_descripcion_limpia_dos_puntos_y_adornos(self):
        readme = "# x\n>## Descripción:\n-- ----\nHace búsquedas.\n-- ----\n>## Endpoints\n"
        desc = repo_note._extract_description(readme)
        self.assertEqual(desc, "Hace búsquedas.")

    def test_repo_sin_openapi(self):
        (self.d / "package.json").write_text('{"name":"x-lambda"}', encoding="utf-8")
        note = repo_note.build_note(self.d, "segurosbolivar/x-lambda", ecs=None, tags=[], project="ciencuadras")
        self.assertIn("Node", note)


if __name__ == "__main__":
    unittest.main()
