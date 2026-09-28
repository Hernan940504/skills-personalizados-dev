"""Tests de drive_client: núcleo de reintentos y clasificación de errores.

Los tests de listados, descarga, subida y organización se agregan en el mismo archivo
a medida que avanzan las tareas. Sin red ni credenciales reales: se usa un doble de
``service`` y un ``HttpError`` simulado.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import drive_client as dc  # noqa: E402


class FakeResp:
    """Doble de httplib2.Response con atributo status."""

    def __init__(self, status):
        self.status = status


class FakeHttpError(Exception):
    """Doble de googleapiclient.errors.HttpError con resp.status y reason."""

    def __init__(self, status, reason="error"):
        super().__init__(f"{status} {reason}")
        self.resp = FakeResp(status)
        self.reason = reason


class FakeRequest:
    """Request que falla ``fail_times`` veces con un error dado y luego devuelve ``result``."""

    def __init__(self, error=None, fail_times=0, result=None):
        self._error = error
        self._fail_times = fail_times
        self._result = result if result is not None else {"ok": True}
        self.calls = 0

    def execute(self):
        self.calls += 1
        if self.calls <= self._fail_times:
            raise self._error
        return self._result


def _client():
    """Cliente con sleep no-op y delays cortos para tests deterministas."""
    return dc.DriveClient(
        service=object(),
        max_retries=3,
        base_delay=0.0,
        cap_delay=0.0,
        sleep=lambda _: None,
    )


class TestExecuteRetries(unittest.TestCase):
    def test_exito_directo(self):
        # Given una request que no falla, When _execute, Then devuelve resultado.
        req = FakeRequest(result={"value": 1})
        self.assertEqual(_client()._execute(req), {"value": 1})
        self.assertEqual(req.calls, 1)

    def test_reintenta_y_luego_exito(self):
        # Given 503 dos veces y luego OK, When _execute, Then reintenta y devuelve OK.
        req = FakeRequest(error=FakeHttpError(503), fail_times=2, result={"ok": 1})
        client = _client()
        self.assertEqual(client._execute(req), {"ok": 1})
        self.assertEqual(req.calls, 3)

    def test_agota_reintentos_429_quota(self):
        # Given 429 siempre, When _execute, Then QuotaExceededError tras agotar.
        req = FakeRequest(error=FakeHttpError(429), fail_times=99)
        with self.assertRaises(dc.QuotaExceededError):
            _client()._execute(req)
        self.assertEqual(req.calls, 4)  # 1 inicial + 3 reintentos

    def test_500_reintenta(self):
        req = FakeRequest(error=FakeHttpError(500), fail_times=1, result={"ok": 1})
        self.assertEqual(_client()._execute(req), {"ok": 1})
        self.assertEqual(req.calls, 2)


class TestErrorClassification(unittest.TestCase):
    def test_404_not_found(self):
        req = FakeRequest(error=FakeHttpError(404), fail_times=1)
        with self.assertRaises(dc.NotFoundError):
            _client()._execute(req)

    def test_403_permiso(self):
        req = FakeRequest(error=FakeHttpError(403, reason="insufficientPermissions"), fail_times=1)
        with self.assertRaises(dc.PermissionDeniedError):
            _client()._execute(req)

    def test_403_quota_se_clasifica_como_quota(self):
        req = FakeRequest(error=FakeHttpError(403, reason="userRateLimitExceeded"), fail_times=1)
        with self.assertRaises(dc.QuotaExceededError):
            _client()._execute(req)

    def test_403_no_reintenta(self):
        # Un 403 no es transitorio: debe fallar en el primer intento.
        req = FakeRequest(error=FakeHttpError(403, reason="insufficientPermissions"), fail_times=99)
        with self.assertRaises(dc.PermissionDeniedError):
            _client()._execute(req)
        self.assertEqual(req.calls, 1)

    def test_error_generico(self):
        req = FakeRequest(error=FakeHttpError(400, reason="badRequest"), fail_times=1)
        with self.assertRaises(dc.DriveClientError):
            _client()._execute(req)


# --- Dobles para listados ----------------------------------------------------


class FakeListRequest:
    """Request de list que devuelve una página predefinida."""

    def __init__(self, page):
        self._page = page

    def execute(self):
        return self._page


class FakeListResource:
    """Recurso .list() que sirve páginas secuenciales y captura los params recibidos."""

    def __init__(self, pages, item_key):
        self._pages = pages
        self._item_key = item_key
        self.calls = []

    def list(self, **params):
        self.calls.append(params)
        # Selecciona la página según el pageToken recibido.
        token = params.get("pageToken")
        if token is None:
            idx = 0
        else:
            idx = int(token)
        return FakeListRequest(self._pages[idx])


class FakeService:
    """Doble del service de Drive con files() y drives()."""

    def __init__(self, files_pages=None, drives_pages=None):
        self._files = FakeListResource(files_pages or [{}], "files")
        self._drives = FakeListResource(drives_pages or [{}], "drives")

    def files(self):
        return self._files

    def drives(self):
        return self._drives


def _client_with(service):
    return dc.DriveClient(service=service, max_retries=1, base_delay=0.0, sleep=lambda _: None)


class TestPagination(unittest.TestCase):
    def test_concatena_tres_paginas(self):
        # Given 3 páginas encadenadas por nextPageToken, When search, Then concatena las 3.
        pages = [
            {"files": [{"id": "1"}], "nextPageToken": "1"},
            {"files": [{"id": "2"}], "nextPageToken": "2"},
            {"files": [{"id": "3"}]},
        ]
        service = FakeService(files_pages=pages)
        result = _client_with(service).search()
        self.assertEqual([f["id"] for f in result], ["1", "2", "3"])

    def test_cero_resultados_lista_vacia(self):
        service = FakeService(files_pages=[{"files": []}])
        self.assertEqual(_client_with(service).search(name="nope"), [])

    def test_max_results_corta_y_no_pagina_de_mas(self):
        # Given páginas que sumarían 3, When max_results=2, Then devuelve 2 y no sigue paginando.
        pages = [
            {"files": [{"id": "1"}, {"id": "2"}], "nextPageToken": "1"},
            {"files": [{"id": "3"}]},
        ]
        service = FakeService(files_pages=pages)
        result = _client_with(service).search(max_results=2)
        self.assertEqual([f["id"] for f in result], ["1", "2"])
        self.assertEqual(len(service.files().calls), 1)  # no pidió la 2ª página

    def test_max_results_none_trae_todo(self):
        pages = [
            {"files": [{"id": "1"}], "nextPageToken": "1"},
            {"files": [{"id": "2"}]},
        ]
        service = FakeService(files_pages=pages)
        result = _client_with(service).search(max_results=None)
        self.assertEqual(len(result), 2)


class TestAllDrivesFlags(unittest.TestCase):
    def test_search_all_incluye_flags_y_corpora(self):
        # Given ámbito all, When search, Then van supportsAllDrives, includeItems y corpora=allDrives.
        service = FakeService(files_pages=[{"files": []}])
        _client_with(service).search(scope=dc.SCOPE_ALL)
        params = service.files().calls[0]
        self.assertTrue(params["supportsAllDrives"])
        self.assertTrue(params["includeItemsFromAllDrives"])
        self.assertEqual(params["corpora"], "allDrives")

    def test_search_mydrive_corpora_user(self):
        service = FakeService(files_pages=[{"files": []}])
        _client_with(service).search(scope=dc.SCOPE_MYDRIVE)
        self.assertEqual(service.files().calls[0]["corpora"], "user")

    def test_search_drive_id_corpora_drive(self):
        service = FakeService(files_pages=[{"files": []}])
        _client_with(service).search(drive_id="D123")
        params = service.files().calls[0]
        self.assertEqual(params["corpora"], "drive")
        self.assertEqual(params["driveId"], "D123")


class TestQueryBuilder(unittest.TestCase):
    def test_filtros_construyen_q(self):
        q = dc._build_query(
            name_contains="informe",
            parent="P1",
            mime_type="application/pdf",
            owner="a@b.com",
        )
        self.assertIn("name contains 'informe'", q)
        self.assertIn("'P1' in parents", q)
        self.assertIn("mimeType = 'application/pdf'", q)
        self.assertIn("'a@b.com' in owners", q)
        self.assertIn("trashed = false", q)

    def test_escapa_comillas_en_valor(self):
        # Given un nombre con comilla, When build, Then queda escapada (no rompe la query).
        q = dc._build_query(name="O'Brien")
        self.assertIn("name = 'O\\'Brien'", q)

    def test_include_trashed_omite_clausula(self):
        q = dc._build_query(name="x", include_trashed=True)
        self.assertNotIn("trashed", q)


class TestSharedDrives(unittest.TestCase):
    def test_lista_shared_drives_pagina(self):
        pages = [
            {"drives": [{"id": "d1", "name": "Legal"}], "nextPageToken": "1"},
            {"drives": [{"id": "d2", "name": "Finanzas"}]},
        ]
        service = FakeService(drives_pages=pages)
        result = _client_with(service).list_shared_drives()
        self.assertEqual([d["name"] for d in result], ["Legal", "Finanzas"])


# --- Dobles para descarga/export ---------------------------------------------

import tempfile  # noqa: E402
import mime_map as mm  # noqa: E402


class FakeMediaRequest:
    """Marca qué tipo de request es (media/export) y sus params, sin descargar nada real."""

    def __init__(self, kind, **params):
        self.kind = kind
        self.params = params


class FakeDownloader:
    """Doble de MediaIoBaseDownload: escribe un contenido fijo en un solo chunk."""

    def __init__(self, fh, request, content=b"data"):
        self._fh = fh
        self._request = request
        self._content = content
        self._done = False

    def next_chunk(self):
        if not self._done:
            self._fh.write(self._content)
            self._done = True
        return (None, True)


class FakeFilesResourceDL:
    """Recurso files() para descarga/export/list, capturando llamadas."""

    def __init__(self, pages_by_parent=None):
        self._pages_by_parent = pages_by_parent or {}
        self.get_media_calls = []
        self.export_calls = []

    def get_media(self, **params):
        self.get_media_calls.append(params)
        return FakeMediaRequest("media", **params)

    def export_media(self, **params):
        self.export_calls.append(params)
        return FakeMediaRequest("export", **params)

    def list(self, **params):
        # Devuelve los hijos según el parent embebido en q.
        q = params.get("q", "")
        parent = None
        for token in q.split(" and "):
            if "in parents" in token:
                parent = token.split("'")[1]
        page = {"files": self._pages_by_parent.get(parent, [])}
        return FakeListRequest(page)


class FakeServiceDL:
    def __init__(self, pages_by_parent=None):
        self._files = FakeFilesResourceDL(pages_by_parent)

    def files(self):
        return self._files


def _client_dl(service):
    return dc.DriveClient(
        service=service,
        max_retries=1,
        base_delay=0.0,
        sleep=lambda _: None,
        downloader_factory=lambda fh, req: FakeDownloader(fh, req),
    )


class TestDownloadExport(unittest.TestCase):
    def test_descarga_binario_usa_get_media(self):
        service = FakeServiceDL()
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "archivo.bin")
            client = _client_dl(service)
            written = client.download_file("F1", dest)
            self.assertTrue(os.path.exists(written))
            self.assertEqual(service.files().get_media_calls[-1]["fileId"], "F1")
            self.assertTrue(service.files().get_media_calls[-1]["supportsAllDrives"])

    def test_export_google_usa_export_media_y_extension(self):
        service = FakeServiceDL()
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "doc")
            client = _client_dl(service)
            written = client.export_file("D1", mm.GOOGLE_DOC, dest)  # default docx
            self.assertTrue(written.endswith(".docx"))
            self.assertTrue(os.path.exists(written))
            call = service.files().export_calls[-1]
            self.assertIn("wordprocessingml", call["mimeType"])

    def test_export_formato_invalido_falla(self):
        service = FakeServiceDL()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(mm.UnsupportedExportFormatError):
                _client_dl(service).export_file("S1", mm.GOOGLE_SLIDES, os.path.join(tmp, "x"), "csv")

    def test_download_any_binario_vs_google(self):
        service = FakeServiceDL()
        with tempfile.TemporaryDirectory() as tmp:
            client = _client_dl(service)
            bin_meta = {"id": "B", "name": "foto.png", "mimeType": "image/png"}
            client.download_any(bin_meta, tmp)
            self.assertEqual(len(service.files().get_media_calls), 1)
            doc_meta = {"id": "D", "name": "informe", "mimeType": mm.GOOGLE_DOC}
            client.download_any(doc_meta, tmp)
            self.assertEqual(len(service.files().export_calls), 1)

    def test_descarga_recursiva_recrea_arbol(self):
        # Given root con un archivo y una subcarpeta con otro archivo.
        pages = {
            "ROOT": [
                {"id": "f1", "name": "a.pdf", "mimeType": "application/pdf"},
                {"id": "sub", "name": "Sub", "mimeType": mm.GOOGLE_FOLDER},
            ],
            "sub": [
                {"id": "f2", "name": "b.pdf", "mimeType": "application/pdf"},
            ],
        }
        service = FakeServiceDL(pages_by_parent=pages)
        with tempfile.TemporaryDirectory() as tmp:
            client = _client_dl(service)
            written = client.download_folder_recursive("ROOT", os.path.join(tmp, "out"))
            self.assertEqual(len(written), 2)
            self.assertTrue(os.path.exists(os.path.join(tmp, "out", "a.pdf")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "out", "Sub", "b.pdf")))


# --- Dobles para upload/update -----------------------------------------------


class FakeUploader:
    """Doble de MediaFileUpload que registra si es resumable y el mimetype."""

    instances = []

    def __init__(self, path, mimetype=None, resumable=False, chunksize=None):
        self.path = path
        self.mimetype = mimetype
        self.resumable = resumable
        self.chunksize = chunksize
        FakeUploader.instances.append(self)


class FakeMutRequest:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


class FakeFilesResourceUP:
    """Recurso files() para create/update/list, capturando llamadas."""

    def __init__(self, existing_by_name=None):
        self._existing_by_name = existing_by_name or {}
        self.create_calls = []
        self.update_calls = []

    def list(self, **params):
        q = params.get("q", "")
        name = None
        for token in q.split(" and "):
            if token.startswith("name = "):
                name = token.split("'")[1]
        return FakeListRequest({"files": self._existing_by_name.get(name, [])})

    def create(self, **params):
        self.create_calls.append(params)
        return FakeMutRequest({"id": "NEW", "name": params["body"]["name"]})

    def update(self, **params):
        self.update_calls.append(params)
        return FakeMutRequest({"id": params["fileId"], "name": "updated"})


class FakeServiceUP:
    def __init__(self, existing_by_name=None):
        self._files = FakeFilesResourceUP(existing_by_name)

    def files(self):
        return self._files


def _client_up(service):
    FakeUploader.instances = []
    return dc.DriveClient(
        service=service,
        max_retries=1,
        base_delay=0.0,
        sleep=lambda _: None,
        uploader_factory=lambda path, mimetype=None, resumable=False, chunksize=None: FakeUploader(
            path, mimetype=mimetype, resumable=resumable, chunksize=chunksize
        ),
    )


def _make_file(tmp, name, size_bytes):
    path = os.path.join(tmp, name)
    with open(path, "wb") as fh:
        fh.write(b"0" * size_bytes)
    return path


class TestUpload(unittest.TestCase):
    def test_pequeno_usa_simple(self):
        # Given archivo <=5MB, When upload, Then uploader no resumable.
        service = FakeServiceUP()
        with tempfile.TemporaryDirectory() as tmp:
            path = _make_file(tmp, "small.txt", 10)
            _client_up(service).upload(path, parent="P")
            self.assertFalse(FakeUploader.instances[-1].resumable)

    def test_grande_usa_resumable(self):
        # Given archivo >5MB, When upload, Then uploader resumable con chunksize.
        service = FakeServiceUP()
        with tempfile.TemporaryDirectory() as tmp:
            path = _make_file(tmp, "big.bin", dc.RESUMABLE_THRESHOLD_BYTES + 1)
            _client_up(service).upload(path, parent="P")
            self.assertTrue(FakeUploader.instances[-1].resumable)
            self.assertIsNotNone(FakeUploader.instances[-1].chunksize)

    def test_create_incluye_supports_all_drives(self):
        service = FakeServiceUP()
        with tempfile.TemporaryDirectory() as tmp:
            path = _make_file(tmp, "f.txt", 5)
            _client_up(service).upload(path, parent="P")
            self.assertTrue(service.files().create_calls[-1]["supportsAllDrives"])

    def test_conflicto_sin_estrategia_lanza(self):
        # Given ya existe el nombre, When upload sin on_conflict, Then ConflictError.
        service = FakeServiceUP(existing_by_name={"dup.txt": [{"id": "E1"}]})
        with tempfile.TemporaryDirectory() as tmp:
            path = _make_file(tmp, "dup.txt", 5)
            with self.assertRaises(dc.ConflictError):
                _client_up(service).upload(path, parent="P")

    def test_conflicto_replace_reusa_fileid(self):
        # Given ya existe, When upload replace, Then update() sobre el fileId existente (no create).
        service = FakeServiceUP(existing_by_name={"dup.txt": [{"id": "E1"}]})
        with tempfile.TemporaryDirectory() as tmp:
            path = _make_file(tmp, "dup.txt", 5)
            _client_up(service).upload(path, parent="P", on_conflict=dc.CONFLICT_REPLACE)
            self.assertEqual(len(service.files().create_calls), 0)
            self.assertEqual(service.files().update_calls[-1]["fileId"], "E1")

    def test_convert_setea_mime_google(self):
        service = FakeServiceUP()
        with tempfile.TemporaryDirectory() as tmp:
            path = _make_file(tmp, "hoja.csv", 5)
            _client_up(service).upload(path, parent="P", convert=True)
            body = service.files().create_calls[-1]["body"]
            self.assertEqual(body["mimeType"], mm.GOOGLE_SHEET)


class TestUpdate(unittest.TestCase):
    def test_update_content_reusa_fileid(self):
        service = FakeServiceUP()
        with tempfile.TemporaryDirectory() as tmp:
            path = _make_file(tmp, "n.txt", 5)
            _client_up(service).update_content("FID", path)
            self.assertEqual(service.files().update_calls[-1]["fileId"], "FID")
            self.assertEqual(len(service.files().create_calls), 0)

    def test_update_metadata_setea_campos(self):
        service = FakeServiceUP()
        client = _client_up(service)
        client.update_metadata("FID", name="nuevo", description="desc")
        body = service.files().update_calls[-1]["body"]
        self.assertEqual(body["name"], "nuevo")
        self.assertEqual(body["description"], "desc")

    def test_update_metadata_sin_campos_falla(self):
        service = FakeServiceUP()
        with self.assertRaises(ValueError):
            _client_up(service).update_metadata("FID")


# --- Dobles para organización/rutas ------------------------------------------


class FakeFilesResourceORG:
    """Recurso files() para organización: list/create/update/copy/get."""

    def __init__(self, tree_by_parent=None, file_meta=None):
        self._tree = tree_by_parent or {}
        self._file_meta = file_meta or {}
        self.create_calls = []
        self.update_calls = []
        self.copy_calls = []

    def list(self, **params):
        q = params.get("q", "")
        name = parent = None
        for token in q.split(" and "):
            if token.startswith("name = "):
                name = token.split("'")[1]
            if "in parents" in token:
                parent = token.split("'")[1]
        items = [f for f in self._tree.get(parent, []) if f["name"] == name]
        return FakeListRequest({"files": items})

    def create(self, **params):
        self.create_calls.append(params)
        new_id = f"NEW{len(self.create_calls)}"
        return FakeMutRequest({"id": new_id, "name": params["body"]["name"],
                               "mimeType": params["body"].get("mimeType", "")})

    def update(self, **params):
        self.update_calls.append(params)
        return FakeMutRequest({"id": params["fileId"], "name": "x"})

    def copy(self, **params):
        self.copy_calls.append(params)
        return FakeMutRequest({"id": "COPY", "name": params["body"].get("name", "copia")})

    def get(self, **params):
        return FakeMutRequest(self._file_meta.get(params["fileId"], {"id": params["fileId"], "parents": ["OLD"]}))


class FakeServiceORG:
    def __init__(self, tree_by_parent=None, file_meta=None):
        self._files = FakeFilesResourceORG(tree_by_parent, file_meta)

    def files(self):
        return self._files


def _client_org(service):
    return dc.DriveClient(service=service, max_retries=1, base_delay=0.0, sleep=lambda _: None)


class TestOrganize(unittest.TestCase):
    def test_mkdir_p_crea_solo_faltantes(self):
        # Given a existe bajo root, b y c no. When mkdir_p a/b/c, Then crea 2 (b y c).
        tree = {"root": [{"id": "A", "name": "a", "mimeType": mm.GOOGLE_FOLDER}]}
        service = FakeServiceORG(tree_by_parent=tree)
        deepest = _client_org(service).mkdir_p("a/b/c", root="root")
        self.assertEqual(len(service.files().create_calls), 2)
        self.assertTrue(deepest.startswith("NEW"))

    def test_move_ajusta_parents_con_supports_all_drives(self):
        service = FakeServiceORG(file_meta={"F": {"id": "F", "parents": ["OLD"]}})
        _client_org(service).move("F", add_parent="DEST")
        call = service.files().update_calls[-1]
        self.assertEqual(call["addParents"], "DEST")
        self.assertEqual(call["removeParents"], "OLD")
        self.assertTrue(call["supportsAllDrives"])

    def test_trash_marca_trashed_true(self):
        service = FakeServiceORG()
        _client_org(service).trash("F")
        self.assertEqual(service.files().update_calls[-1]["body"], {"trashed": True})

    def test_restore_marca_trashed_false(self):
        service = FakeServiceORG()
        _client_org(service).restore("F")
        self.assertEqual(service.files().update_calls[-1]["body"], {"trashed": False})

    def test_copy_con_nombre_y_parent(self):
        service = FakeServiceORG()
        _client_org(service).copy("F", new_name="copia.txt", parent="DEST")
        body = service.files().copy_calls[-1]["body"]
        self.assertEqual(body["name"], "copia.txt")
        self.assertEqual(body["parents"], ["DEST"])
        self.assertTrue(service.files().copy_calls[-1]["supportsAllDrives"])


class TestResolvePath(unittest.TestCase):
    def test_resuelve_ruta_simple(self):
        tree = {
            "root": [{"id": "P", "name": "Proyectos", "mimeType": mm.GOOGLE_FOLDER}],
            "P": [{"id": "Y", "name": "2026", "mimeType": mm.GOOGLE_FOLDER}],
        }
        service = FakeServiceORG(tree_by_parent=tree)
        self.assertEqual(_client_org(service).resolve_path("Proyectos/2026"), "Y")

    def test_segmento_faltante_lanza_notfound(self):
        service = FakeServiceORG(tree_by_parent={"root": []})
        with self.assertRaises(dc.NotFoundError):
            _client_org(service).resolve_path("NoExiste")

    def test_segmento_duplicado_lanza_ambiguo(self):
        tree = {"root": [
            {"id": "A1", "name": "Dup", "mimeType": mm.GOOGLE_FOLDER},
            {"id": "A2", "name": "Dup", "mimeType": mm.GOOGLE_FOLDER},
        ]}
        service = FakeServiceORG(tree_by_parent=tree)
        with self.assertRaises(dc.PathAmbiguousError) as ctx:
            _client_org(service).resolve_path("Dup")
        self.assertEqual(len(ctx.exception.candidates), 2)

    def test_resuelve_en_shared_drive_arranca_en_drive_id(self):
        tree = {"D1": [{"id": "C", "name": "Contratos", "mimeType": mm.GOOGLE_FOLDER}]}
        service = FakeServiceORG(tree_by_parent=tree)
        self.assertEqual(_client_org(service).resolve_path("Contratos", drive_id="D1"), "C")


class TestNoPermanentDelete(unittest.TestCase):
    def test_cliente_no_expone_delete_ni_emptytrash(self):
        # El cliente no debe tener métodos de borrado permanente.
        self.assertFalse(hasattr(dc.DriveClient, "delete"))
        self.assertFalse(hasattr(dc.DriveClient, "empty_trash"))

    def test_codigo_fuente_sin_files_delete(self):
        # Defensa en profundidad: el código fuente no INVOCA borrado permanente.
        # Se ignoran líneas de comentario (empiezan con #) para no chocar con la nota de seguridad.
        src_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "drive_client.py")
        with open(src_path, encoding="utf-8") as fh:
            code_lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
        code = "".join(code_lines)
        self.assertNotIn("files().delete(", code)
        self.assertNotIn(".emptyTrash(", code)
        self.assertNotIn("emptyTrash(", code)


if __name__ == "__main__":
    unittest.main()
