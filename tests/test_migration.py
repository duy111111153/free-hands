import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from free_hands import config


class MigrationTests(unittest.TestCase):
    def test_legacy_xdg_directories_move_once(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            new_config = base / "config" / "free-hands"
            new_data = base / "data" / "free-hands"
            new_runtime = base / "runtime" / "free-hands"
            old_config = new_config.parent / "voz-codex"
            old_data = new_data.parent / "voz-codex"
            old_runtime = new_runtime.parent / "voz-codex"
            old_config.mkdir(parents=True)
            old_data.mkdir(parents=True)
            old_runtime.mkdir(parents=True)
            (old_config / "config.toml").write_text("agent_name = 'DOOM'", encoding="utf-8")
            (old_data / "history.sqlite3").write_text("local", encoding="utf-8")

            with patch.multiple(config, CONFIG_HOME=new_config, DATA_HOME=new_data,
                                RUNTIME_HOME=new_runtime):
                self.assertTrue(config.migrate_legacy_state())
                self.assertEqual((new_config / "config.toml").read_text(), "agent_name = 'DOOM'")
                self.assertTrue((new_data / "history.sqlite3").is_file())
                self.assertFalse(old_runtime.exists())
                self.assertFalse(config.migrate_legacy_state())


if __name__ == "__main__":
    unittest.main()
