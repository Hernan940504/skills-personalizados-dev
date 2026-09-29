"""Tests del cliente Gmail (paginación/filtrado con dobles) y del CLI scan en dry-run."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import gmail_client as gc  # noqa: E402


class TestBusinessLabels(unittest.TestCase):
    def test_filtra_por_prefijo(self):
        labels = [
            {"id": "1", "name": "Tribu Servicios Bolivar/Ciencuadras"},
            {"id": "2", "name": "INBOX"},
            {"id": "3", "name": "Tribu Servicios Bolivar/RC"},
            {"id": "4", "name": "Datadog"},
        ]
        biz = gc.business_labels(labels)
        names = sorted(l["name"] for l in biz)
        self.assertEqual(names, [
            "Tribu Servicios Bolivar/Ciencuadras", "Tribu Servicios Bolivar/RC",
        ])


class _FakeMessages:
    def __init__(self, pages):
        self._pages = pages
        self._i = 0

    def list(self, **kwargs):
        return self

    def execute(self):
        page = self._pages[self._i]
        self._i += 1
        return page


class _FakeUsers:
    def __init__(self, pages):
        self._m = _FakeMessages(pages)

    def messages(self):
        return self._m


class _FakeService:
    def __init__(self, pages):
        self._u = _FakeUsers(pages)

    def users(self):
        return self._u


class TestSearchPaginado(unittest.TestCase):
    def test_itera_todas_las_paginas(self):
        pages = [
            {"messages": [{"id": "a"}, {"id": "b"}], "nextPageToken": "t1"},
            {"messages": [{"id": "c"}]},  # sin nextPageToken → fin
        ]
        svc = _FakeService(pages)
        ids = list(gc.search_message_ids(svc, "L", 123))
        self.assertEqual(ids, ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
