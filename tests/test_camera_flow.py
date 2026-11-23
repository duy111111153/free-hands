import unittest
from contextlib import contextmanager, nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from voz_codex import config
from voz_codex.service import Service


SETTINGS = {
    "project": "default",
    "codex_command": "codex app-server --stdio",
    "model": "gpt-5.6-luna",
    "model_reasoning_effort": "medium",
}
ORIGINAL = "Quiero que accedas a mi webcam y ahora me digas qué objeto es este."
SHOWING = "¿Qué iPhone dirías que es este que te estoy mostrando en la webcam?"
LIVE_LOOK = "¿Qué estás viendo en mi webcam ahora mismo?"


class CameraFlowTests(unittest.TestCase):
    def setUp(self):
        folder = Path(self.enterContext(TemporaryDirectory()))
        self.enterContext(patch.multiple(
            config, DATA_HOME=folder, DB_FILE=folder / "history.db",
            RUNTIME_HOME=folder, TASK_FILE=folder / "task.json",
        ))
        self.enterContext(patch.object(config, "load", return_value=SETTINGS))
        self.counter = 0
        self.capture = self.enterContext(patch(
            "voz_codex.service.capture_camera", side_effect=self.fake_capture,
        ))

    @staticmethod
    def fake_capture(folder, on_frame, check_cancel):
        check_cancel()
        paths = tuple(folder / f"shot-{i}.jpg" for i in range(1, 4))
        for i, path in enumerate(paths, 1):
            path.write_bytes(b"fixture")
            on_frame(i, i)
        return paths

    def start(self):
        app = Service()
        self.addCleanup(app.history.db.close)
        app.tracker = True
        app.speech = Mock()
        app.speech.waiting.return_value = nullcontext()
        app.history.thread("camera-chat", "default")
        app.codex.set_thread("camera-chat")

        def ask(prompt, on_delta, cwd, *, images, **kwargs):
            self.counter += 1
            self.assertTrue(all(path.is_file() for path in images))
            return f"turn-{self.counter}", "Parece un cortauñas."

        app.codex.ask = Mock(side_effect=ask)
        return app

    def test_fresh_images_detail_and_refresh_after_restart(self):
        app = self.start()
        result = app.handle({"command": "ingest", "text": ORIGINAL})
        self.assertEqual(result["state"], "done")
        first = app.codex.ask.call_args
        self.assertEqual(len(first.kwargs["images"]), 3)
        self.assertIn("una sola frase corta", first.args[0])
        self.assertFalse(any(image.exists() for image in first.kwargs["images"]))

        app = self.start()
        self.assertEqual(app.history.get_state("last_camera_thread"), "camera-chat")
        result = app.handle({"command": "ingest", "text": "¿Qué más ves?"})
        self.assertEqual(result["thread_id"], "camera-chat")
        detail = app.codex.ask.call_args
        self.assertEqual(detail.kwargs["images"], ())
        self.assertIn("El usuario quiere detalles", detail.args[0])
        self.assertEqual(self.capture.call_count, 1)

        app.handle({"command": "ingest", "text": "¿Qué ves ahora?"})
        self.assertEqual(len(app.codex.ask.call_args.kwargs["images"]), 3)
        self.assertEqual(self.capture.call_count, 2)

    def test_incomplete_capture_is_reported_locally(self):
        app = self.start()
        self.capture.side_effect = None
        self.capture.return_value = ()
        result = app.handle({"command": "ingest", "text": ORIGINAL})
        self.assertEqual(result["state"], "screen_unavailable")
        self.assertIn("tres tomas", app.task["detail"])
        self.assertEqual(self.capture.call_count, 2)
        app.codex.ask.assert_not_called()

    def test_showing_an_object_uses_fresh_photos_and_retries_partial_capture(self):
        app = self.start()
        attempts = []

        def intermittent(folder, on_frame, check_cancel):
            attempts.append(folder)
            paths = self.fake_capture(folder, on_frame, check_cancel)
            return paths[:1] if len(attempts) == 1 else paths

        self.capture.side_effect = intermittent
        self.assertEqual(app.handle({"command": "ingest", "text": SHOWING})["state"], "done")
        self.assertEqual(len(attempts), 2)
        self.assertNotEqual(*attempts)
        self.assertFalse(any(folder.exists() for folder in attempts))
        self.assertEqual(len(app.codex.ask.call_args.kwargs["images"]), 3)
        app.codex.ask.assert_called_once()

    def test_missing_attachment_reply_becomes_an_actionable_error(self):
        app = self.start()
        app.codex.ask.side_effect = None
        app.codex.ask.return_value = ("turn-1", "No estoy recibiendo una imagen actual de tu webcam, ñaño.")
        result = app.handle({"command": "ingest", "text": LIVE_LOOK})
        self.assertEqual(len(app.codex.ask.call_args.kwargs["images"]), 3)
        self.assertEqual(result["state"], "screen_unavailable")
        self.assertEqual(app.task["state"], "error")
        self.assertIn("abre mi webcam otra vez", app.task["detail"])
        app.speech.speak.assert_called_once_with(result["error"])

    def test_screen_context_survives_restart_and_both_sources_stay_ordered(self):
        @contextmanager
        def fake_screen():
            with TemporaryDirectory() as folder:
                path = Path(folder) / "pantalla.jpg"
                path.write_bytes(b"fixture")
                yield path

        with patch("voz_codex.service.screen_image", side_effect=fake_screen) as screen:
            app = self.start()
            app.handle({"command": "ingest", "text": "Léeme lo que dice en mi pantalla"})
            self.capture.assert_not_called()
            app = self.start()
            app.handle({"command": "ingest", "text": "¿Qué estás viendo ahorita?"})
            self.assertEqual(screen.call_count, 2)
            self.capture.assert_not_called()

            app.handle({"command": "ingest", "text": "Revisa mi webcam junto con la pantalla"})
            self.assertEqual(
                [path.name for path in app.codex.ask.call_args.kwargs["images"]],
                ["pantalla.jpg", "shot-1.jpg", "shot-2.jpg", "shot-3.jpg"],
            )
