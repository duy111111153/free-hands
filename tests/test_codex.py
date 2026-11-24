import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from voz_codex.codex import CodexClient


class CodexTests(unittest.TestCase):
    def test_full_access_requires_explicit_opt_in(self):
        with patch.dict("os.environ", {}, clear=True):
            client = CodexClient("codex app-server")
            self.assertEqual(client.sandbox_mode, "read-only")
            self.assertEqual(client.sandbox_policy, {"type": "readOnly"})
        with patch.dict("os.environ", {"FREE_HANDS_FULL_ACCESS": "1"}):
            client = CodexClient("codex app-server")
            self.assertEqual(client.sandbox_policy, {"type": "dangerFullAccess"})

    def test_answer_keeps_all_parts_and_ignores_commentary(self):
        client = CodexClient("codex app-server", effort="medium")
        client.thread_id = "chat"
        client.loaded_thread_id = "chat"
        client.proc = Mock()

        def notice(method, **params):
            return {"method": method, "params": {"threadId": "chat", **params}}

        def message(item_id, phase, text):
            return notice("item/completed", turnId="turn", item={
                "id": item_id, "type": "agentMessage", "phase": phase, "text": text,
            })

        client._event = Mock(side_effect=[
            {"id": 1, "result": {"turn": {"id": "turn"}}},
            notice("item/agentMessage/delta", turnId="turn", itemId="2", delta="Voy a consultar otros chats."),
            message("1", "partial_answer", "Primera parte."),
            message("2", "commentary", "Estoy revisando."),
            notice("item/started", turnId="turn", item={"id": "3", "type": "agentMessage", "phase": "final_answer"}),
            notice("item/agentMessage/delta", turnId="turn", itemId="3", delta="Última frase."),
            message("3", "final_answer", "Última frase."),
            notice("turn/completed", turn={"id": "turn", "status": "completed"}),
        ])
        preview = []
        self.assertEqual(
            client.ask("Prueba", preview.append, images=tuple(Path(f"shot-{i}.jpg") for i in range(1, 4))),
            ("turn", "Primera parte.\n\nÚltima frase."),
        )
        self.assertEqual(preview, ["Última frase."])
        params = json.loads(client.proc.stdin.write.call_args.args[0])["params"]
        self.assertEqual(params["effort"], "low")
        self.assertEqual(params["input"][1:], [
            {"type": "localImage", "path": f"shot-{i}.jpg"} for i in range(1, 4)
        ])
