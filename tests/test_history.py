import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from voz_codex.history import History


class HistoryTests(unittest.TestCase):
    def test_history_search(self):
        with TemporaryDirectory() as folder:
            history = History(Path(folder) / "db.sqlite")
            history.thread("t1", "p1", "Demo")
            history.message("t1", "turn1", "user", "revisar tareas del proyecto")
            self.assertEqual(history.search_threads("tareas")[0]["id"], "t1")
            history.db.close()
