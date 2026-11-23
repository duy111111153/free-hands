import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from voz_codex.history import History
from voz_codex.persona import LEXICON_PROJECT, RequestWindow, regional_context, style_instruction, waiting_policy
from voz_codex.rag import refresh


class PersonaTests(unittest.TestCase):
    def test_waiting_policy_avoids_filler_for_simple_turns(self):
        self.assertEqual(waiting_policy("Hola, ¿cómo estás?"), (False, ""))
        self.assertEqual(waiting_policy("Investiga el uso de bacán"), (True, "investigate"))
        self.assertEqual(waiting_policy("hola", True), (True, "repeated"))

    def test_request_window_expires_old_requests(self):
        window = RequestWindow(window_seconds=90)
        results = [window.record(t) for t in (0, 20, 40, 80)]
        self.assertEqual([count for count, _ in results], [1, 2, 3, 4])
        self.assertEqual([new_burst for _, new_burst in results], [False, False, False, True])
        self.assertEqual(window.record(85), (5, False))
        self.assertEqual(window.record(171), (2, False))
        self.assertEqual(window.record(260), (2, False))
        self.assertEqual(window.record(261), (3, False))
        self.assertEqual(window.record(262), (3, False))
        self.assertEqual(window.record(263), (4, True))
        self.assertEqual(window.record(264), (5, False))

    def test_hana_retrieves_relevant_lexicon_only(self):
        with TemporaryDirectory() as folder:
            root = Path(folder) / "lexicon"
            root.mkdir()
            document = Path("voz_codex/data/ecuadorismos.md")
            (root / "ecuadorismos.md").write_text(document.read_text(encoding="utf-8"), encoding="utf-8")
            history = History(Path(folder) / "history.sqlite")
            refresh(history, LEXICON_PROJECT, root)
            context = regional_context(history, "¿Qué significa ñaño y pana?")
            self.assertIn("ñaño", context)
            self.assertIn("pana", context)
            self.assertIn("Tu nombre es HANA", style_instruction("HANA", False, context))
            self.assertIn("Suave, ñaño", style_instruction("HANA", True))
            history.db.close()


if __name__ == "__main__":
    unittest.main()
