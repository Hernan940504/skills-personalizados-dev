"""Tests de la capa CLI: dispatch, JSON/pretty, exit codes, dry-run y confirmaciones.

Se inyecta un cliente falso vía client_factory; no hay red ni credenciales.
"""

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import drive_cli as cli  # noqa: E402
import drive_client as dc  # noqa: E402
import mime_map as mm  # noqa: E402


class FakeClient:
    """Cliente falso que registra llamadas y devuelve respuestas predefinidas."""

    def __init__(self, **overrides):
        self.calls = []
        self._overrides = overrides

    def _record(self, _call_name, **kwargs):
        self.calls.append((_call_name, kwargs))

    def list_shared_drives(self):
        self._record("list_shared_drives")
        return [{"id": "d1", "name": "Legal"}]

    def search(self, **kwargs):
        self._record("search", **kwargs)
        return self._overrides.get("search", [])

    def get_file(self, file_id):
        self._record("get_file", file_id=file_id)
        return self._overrides.get("get_file", {"id": file_id, "name": "f", "mimeType": "application/pdf"})

    def download_file(self, file_id, dest):
        self._record("download_file", file_id=file_id, dest=dest)
        return dest

    def export_file(self, file_id, mime, dest, fmt=None):
        self._record("export_file", file_id=file_id, mime=mime, dest=dest, fmt=fmt)
        return dest + ".docx"

    def download_folder_recursive(self, folder_id, dest, fmt=None):
        self._record("download_folder_recursive", folder_id=folder_id, dest=dest, fmt=fmt)
        return ["a", "b"]

    def upload(self, *a, **k):
        self._record("upload", args=a, kwargs=k)
        return {"id": "NEW"}

    def update_content(self, file_id, path):
        self._record("update_content", file_id=file_id, path=path)
        return {"id": file_id}

    def update_metadata(self, file_id, name=None, description=None):
        self._record("update_metadata", file_id=file_id, name=name, description=description)
        return {"id": file_id}

    def mkdir_p(self, path, root="root", drive_id=None):
        self._record("mkdir_p", path=path)
        return "FOLDER"

    def move(self, file_id, add_parent, remove_parent=None):
        self._record("move", file_id=file_id)
        return {"id": file_id}

    def rename(self, file_id, new_name):
        self._record("rename", file_id=file_id)
        return {"id": file_id}

    def copy(self, file_id, name=None, parent=None):
        self._record("copy", file_id=file_id)
        return {"id": "COPY"}

    def trash(self, file_id):
        self._record("trash", file_id=file_id)
        return {"id": file_id, "trashed": True}

    def restore(self, file_id):
        self._record("restore", file_id=file_id)
        return {"id": file_id, "trashed": False}


def _run(argv, client=None, raiser=None):
    """Ejecuta el CLI capturando stdout/stderr y devuelve (code, out, err)."""
    if raiser is not None:
        factory = raiser
    else:
        client = client or FakeClient()

        def factory(args):
            return client

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.run(argv, client_factory=factory)
    return code, out.getvalue(), err.getvalue()


class TestDispatch(unittest.TestCase):
    def test_drives_json(self):
        code, out, _ = _run(["drives"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertEqual(json.loads(out)["drives"][0]["name"], "Legal")

    def test_pretty_indenta(self):
        code, out, _ = _run(["--pretty", "drives"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("\n", out.strip())  # indentado => multilinea

    def test_search_pasa_filtros(self):
        client = FakeClient(search=[{"id": "1"}])
        code, out, _ = _run(["search", "--name-contains", "informe", "--scope", "mydrive"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        name, kwargs = client.calls[-1]
        self.assertEqual(name, "search")
        self.assertEqual(kwargs["name_contains"], "informe")
        self.assertEqual(kwargs["scope"], "mydrive")


class TestDownload(unittest.TestCase):
    def test_download_binario(self):
        client = FakeClient(get_file={"id": "F", "name": "x", "mimeType": "application/pdf"})
        code, out, _ = _run(["download", "F", "/tmp/x"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("download_file", [c[0] for c in client.calls])

    def test_download_google_exporta(self):
        client = FakeClient(get_file={"id": "D", "name": "doc", "mimeType": mm.GOOGLE_DOC})
        code, out, _ = _run(["download", "D", "/tmp/doc", "--export", "pdf"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("export_file", [c[0] for c in client.calls])

    def test_download_recursive_dry_run_no_ejecuta(self):
        client = FakeClient()
        code, out, _ = _run(["--dry-run", "download", "FOLDER", "/tmp/out", "--recursive"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertTrue(json.loads(out)["dry_run"])
        self.assertEqual(client.calls, [])  # nada se ejecutó


class TestUpdateConfirmations(unittest.TestCase):
    def test_update_content_sin_yes_bloquea(self):
        # Given update --content sin --yes ni --dry-run, Then EXIT_CONFLICT y no ejecuta.
        client = FakeClient()
        code, out, err = _run(["update", "F", "--content", "/tmp/n.txt"], client=client)
        self.assertEqual(code, cli.EXIT_CONFLICT)
        self.assertEqual(client.calls, [])
        self.assertIn("ConfirmationRequired", err)

    def test_update_content_con_yes_ejecuta(self):
        client = FakeClient()
        code, _, _ = _run(["--yes", "update", "F", "--content", "/tmp/n.txt"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("update_content", [c[0] for c in client.calls])

    def test_update_metadata_no_requiere_yes(self):
        client = FakeClient()
        code, _, _ = _run(["update", "F", "--name", "nuevo"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("update_metadata", [c[0] for c in client.calls])

    def test_update_sin_campos_es_usage_error(self):
        code, _, err = _run(["update", "F"])
        self.assertEqual(code, cli.EXIT_USAGE)


class TestOrganizeConfirmations(unittest.TestCase):
    def test_trash_sin_yes_bloquea(self):
        client = FakeClient()
        code, _, err = _run(["organize", "trash", "F"], client=client)
        self.assertEqual(code, cli.EXIT_CONFLICT)
        self.assertEqual(client.calls, [])

    def test_trash_dry_run_no_ejecuta(self):
        client = FakeClient()
        code, out, _ = _run(["--dry-run", "organize", "trash", "F"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertTrue(json.loads(out)["dry_run"])
        self.assertEqual(client.calls, [])

    def test_trash_con_yes_ejecuta(self):
        client = FakeClient()
        code, _, _ = _run(["--yes", "organize", "trash", "F"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("trash", [c[0] for c in client.calls])

    def test_mkdir_ok(self):
        client = FakeClient()
        code, out, _ = _run(["organize", "mkdir", "a/b/c"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertEqual(json.loads(out)["folder_id"], "FOLDER")

    def test_move_ok(self):
        client = FakeClient()
        code, _, _ = _run(["organize", "move", "F", "DEST"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("move", [c[0] for c in client.calls])


class TestExitCodes(unittest.TestCase):
    def _raiser_factory(self, exc):
        def factory(args):
            class Boom:
                def __getattr__(self, _):
                    def _raise(*a, **k):
                        raise exc
                    return _raise
            return Boom()
        return factory

    def test_permission_denied_exit_3(self):
        code, _, err = _run(["drives"], raiser=self._raiser_factory(dc.PermissionDeniedError("no")))
        self.assertEqual(code, cli.EXIT_PERMISSION)

    def test_not_found_exit_4(self):
        code, _, _ = _run(["drives"], raiser=self._raiser_factory(dc.NotFoundError("no")))
        self.assertEqual(code, cli.EXIT_NOT_FOUND)

    def test_quota_exit_5(self):
        code, _, _ = _run(["drives"], raiser=self._raiser_factory(dc.QuotaExceededError("no")))
        self.assertEqual(code, cli.EXIT_QUOTA)

    def test_conflict_exit_6(self):
        code, _, _ = _run(["drives"], raiser=self._raiser_factory(dc.ConflictError("dup")))
        self.assertEqual(code, cli.EXIT_CONFLICT)

    def test_auth_required_exit_7(self):
        import auth
        code, _, _ = _run(["drives"], raiser=self._raiser_factory(auth.AuthRequiredError("auth")))
        self.assertEqual(code, cli.EXIT_AUTH)

    def test_ambiguous_path_exit_4(self):
        code, _, _ = _run(["drives"], raiser=self._raiser_factory(dc.PathAmbiguousError("seg", [1, 2])))
        self.assertEqual(code, cli.EXIT_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()


class TestGlobalFlagsPosition(unittest.TestCase):
    def test_pretty_despues_del_subcomando(self):
        # --pretty tras el subcomando debe indentar igual que antes.
        code, out, _ = _run(["drives", "--pretty"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("\n", out.strip())

    def test_pretty_antes_del_subcomando(self):
        code, out, _ = _run(["--pretty", "drives"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("\n", out.strip())

    def test_yes_despues_del_subcomando_en_trash(self):
        client = FakeClient()
        code, _, _ = _run(["organize", "trash", "F", "--yes"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("trash", [c[0] for c in client.calls])

    def test_dry_run_despues_en_trash_no_ejecuta(self):
        client = FakeClient()
        code, out, _ = _run(["organize", "trash", "F", "--dry-run"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertTrue(json.loads(out)["dry_run"])
        self.assertEqual(client.calls, [])


class TestSearchLimit(unittest.TestCase):
    def test_search_reporta_count(self):
        client = FakeClient(search=[{"id": "1"}, {"id": "2"}])
        code, out, _ = _run(["search", "--name-contains", "x"], client=client)
        self.assertEqual(code, cli.EXIT_OK)
        payload = json.loads(out)
        self.assertEqual(payload["count"], 2)

    def test_search_all_pasa_max_results_none(self):
        client = FakeClient(search=[])
        _run(["search", "--all"], client=client)
        _, kwargs = client.calls[-1]
        self.assertIsNone(kwargs["max_results"])

    def test_search_limit_por_defecto_200(self):
        client = FakeClient(search=[])
        _run(["search"], client=client)
        _, kwargs = client.calls[-1]
        self.assertEqual(kwargs["max_results"], 200)

    def test_search_limit_explicito(self):
        client = FakeClient(search=[])
        _run(["search", "--limit", "50"], client=client)
        _, kwargs = client.calls[-1]
        self.assertEqual(kwargs["max_results"], 50)
