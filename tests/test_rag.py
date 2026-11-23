import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from voz_codex.history import History
from voz_codex.rag import refresh


class RagTests(unittest.TestCase):
    def test_rag_indexes_project_idempotently(self):
        with TemporaryDirectory() as folder:
            root = Path(folder) / "project"
            root.mkdir()
            (root / "README.md").write_text("estado del proyecto voz", encoding="utf-8")
            history = History(Path(folder) / "db.sqlite")
            self.assertEqual(refresh(history, "demo", root), 1)
            self.assertEqual(refresh(history, "demo", root), 1)
            self.assertEqual(history.db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0], 1)
            self.assertTrue(history.search_context("demo", "voz")[0]["path"].endswith("README.md"))
            history.db.close()
