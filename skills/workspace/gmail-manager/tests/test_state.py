"""Tests del estado incremental (12m inicial, incremental con solape, idempotencia, poda)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import state  # noqa: E402


class TestState(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "state.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_primer_barrido_usa_12_meses(self):
        st = {"labels": {}}
        now = 1_000_000_000
        after = state.since_epoch_for(st, "L", since_months=12, now=now)
        # ~365 días atrás (12*30)
        self.assertEqual(after, int(now - 12 * 30 * 86400))

    def test_incremental_usa_ultima_ejecucion_con_solape(self):
        st = {"labels": {"L": {"last_run_epoch": 1_000_000_000, "seen": []}}}
        after = state.since_epoch_for(st, "L", now=1_000_100_000)
        self.assertEqual(after, 1_000_000_000 - state.OVERLAP_SECONDS)

    def test_idempotencia_seen(self):
        st = {"labels": {}}
        self.assertFalse(state.is_seen(st, "L", "m1"))
        state.mark_seen(st, "L", "m1")
        self.assertTrue(state.is_seen(st, "L", "m1"))
        # marcar de nuevo no duplica
        state.mark_seen(st, "L", "m1")
        self.assertEqual(st["labels"]["L"]["seen"].count("m1"), 1)

    def test_poda_seen_al_tope(self):
        st = {"labels": {}}
        for i in range(state.SEEN_MAX + 50):
            state.mark_seen(st, "L", f"m{i}")
        self.assertEqual(len(st["labels"]["L"]["seen"]), state.SEEN_MAX)
        # se conservan los más recientes
        self.assertIn(f"m{state.SEEN_MAX + 49}", st["labels"]["L"]["seen"])

    def test_complete_run_fija_epoch(self):
        st = {"labels": {}}
        state.complete_run(st, "L", now=1234567890)
        self.assertEqual(st["labels"]["L"]["last_run_epoch"], 1234567890)

    def test_persistencia_roundtrip(self):
        st = {"labels": {"L": {"last_run_epoch": 111, "seen": ["a"]}}}
        state.save_state(self.path, st)
        loaded = state.load_state(self.path)
        self.assertEqual(loaded, st)

    def test_load_corrupto_devuelve_vacio(self):
        self.path.write_text("no es json", encoding="utf-8")
        self.assertEqual(state.load_state(self.path), {"labels": {}})


if __name__ == "__main__":
    unittest.main()
