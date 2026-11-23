import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from voz_codex.screen import _mjpeg_size, capture_camera, vision_intent, wants_both, wants_camera, wants_screen


class ScreenIntentTests(unittest.TestCase):
    def test_visual_language_matrix(self):
        cases = {
            (True, False): (
                "Échale un ojo a mi web cam",
                "Pégale una mirada a la gueb cam",
                "Fíjate en mi cámara web",
                "Veme por la webcam",  # Colloquial imperative
                "¿Cómo me veo en mi cámara ahorita?",
                "¿Qué alcanzas a distinguir por la webcam?",
                "¿Qué tengo aquí frente a la cámara?",
                "Revisa la webcam que está encima del monitor.",
                "Solo la webcam, no abras mi pantalla. Mira por la cámara.",
                "No mires el monitor y observa mi camara",
            ),
            (False, True): (
                "Échale un vistazo al monitor",
                "¿Qué estás viendo ahorita en la pantalla de la compu?",
                "Dime qué error sale en mi escritorio",
                "Léeme lo que dice en pantalla",
                "¿Qué ventana aparece en mi monitor?",
                "¿Cuál botón distingues en el display?",
                "Saca un pantallazo",
                "Dame un screenshot",
                "Mira esto en pantalla",
                "Mira mi pantalla y no abras la webcam.",
                "No uses la cámara y mira mi pantalla",
                "Mira mi webcam y mi pantalla, pero no la webcam.",
            ),
            (True, True): (
                "Mira la webcam y la pantalla",
                "¿Qué ves en el monitor y en la cámara?",
                "Revisa la webcam junto con la pantalla",
                "Mira en mi monitor y luego revisa la webcam",
                "Inspecciona mi escritorio y abre mi webcam",
            ),
            (False, False): (
                "¿Qué webcam me recomiendas comprar?",
                "¿Cómo configuro la pantalla?",
                "Explícame cómo hago para usar una webcam",
                "¿Para qué sirve el HDR de la webcam?",
                "La luz de la cámara se encendió sola",
                "La webcam está encima de mi monitor",
                "¿Puedes ver ese enlace?",
                "Dame más detalles",
                "No quiero que leas mi pantalla",
                "No abras la webcam para ver mi escritorio",
            ),
        }
        for expected, phrases in cases.items():
            for phrase in phrases:
                with self.subTest(phrase=phrase):
                    self.assertEqual(vision_intent(phrase), expected)
        self.assertEqual(vision_intent("Mira esto", implied=(False, True)), (False, True))

    def test_camera_requires_intent_and_respects_negation(self):
        self.assertTrue(wants_camera("Abre mi webcam y dime qué ves"))
        self.assertTrue(wants_camera("Quiero que accedas a mi webcam y ahora me digas qué objeto es este."))
        self.assertTrue(wants_camera("Necesito que actives la cámara y mires esto."))
        self.assertTrue(wants_camera("Conéctate a la cámara web."))
        self.assertTrue(wants_camera("¿Qué iPhone dirías que es este que te estoy mostrando en la webcam?"))
        self.assertTrue(wants_camera("¿Qué es esto que te estoy enseñando?"))
        self.assertTrue(wants_camera("¿Qué estás viendo en mi webcam ahora mismo?"))
        self.assertTrue(wants_camera("¿Qué objeto estás viendo ahorita en mi cámara?"))
        self.assertTrue(wants_camera("Dime qué estás viendo en mi cámara."))
        self.assertTrue(wants_camera("Mira esto"))
        self.assertFalse(wants_camera("¿Qué noticias hay en vivo?"))
        self.assertFalse(wants_camera("Mira esto en pantalla"))
        self.assertFalse(wants_camera("Explícame cómo abrir una webcam"))
        self.assertFalse(wants_camera("No abras la webcam para ver mi escritorio"))
        self.assertFalse(wants_camera("No quiero que accedas a mi webcam."))
        self.assertFalse(wants_camera("¿Cómo puedo acceder a la webcam?"))
        self.assertFalse(wants_camera("¿Qué iPhone dirías que es este que te estoy mostrando en una foto?"))
        self.assertFalse(wants_camera("¿Cómo se ve el HDR en la webcam?"))
        self.assertFalse(wants_camera("No te estoy mostrando nada por la webcam."))
        self.assertFalse(wants_both("No uses la cámara; mira la pantalla"))

    def test_camera_cache_contains_only_device_format(self):
        _mjpeg_size.cache_clear()
        self.addCleanup(_mjpeg_size.cache_clear)
        formats = "[0]: 'YUYV'\nSize: Discrete 320x240\n[1]: 'MJPG'\nSize: Discrete 848x480"
        with patch("voz_codex.screen.subprocess.check_output", return_value=formats) as probe:
            self.assertEqual(_mjpeg_size("/dev/video0", (1, 2, 3)), "848x480")
            self.assertEqual(_mjpeg_size("/dev/video0", (1, 2, 3)), "848x480")
            self.assertEqual(_mjpeg_size("/dev/video0", (1, 2, 4)), "848x480")
        self.assertEqual(probe.call_count, 2)

    def test_camera_publishes_three_private_shots_and_releases_process(self):
        frame = b"\xff\xd8test\xff\xd9"
        process = Mock()
        with (
            TemporaryDirectory() as folder,
            patch("voz_codex.screen.shutil.which", return_value="ffmpeg"),
            patch("voz_codex.screen._camera_commands", return_value=[["ffmpeg"]]),
            patch("voz_codex.screen.subprocess.Popen", return_value=process),
            patch("voz_codex.screen._jpeg_frames", return_value=iter([frame] * 5)),
            patch("voz_codex.screen.monotonic", side_effect=[0, 0, 0.5, 0.75, 1.5, 2.25]),
        ):
            notify = Mock()
            paths = capture_camera(Path(folder), notify, lambda: None)
            self.assertEqual([path.name for path in paths], ["shot-1.jpg", "shot-2.jpg", "shot-3.jpg"])
            self.assertTrue(all(path.read_bytes() == frame and path.stat().st_mode & 0o777 == 0o600 for path in paths))
            self.assertEqual([call.args[1] for call in notify.call_args_list], [0, 0, 1, 2, 3])
        process.terminate.assert_called_once()
        process.stdout.close.assert_called_once()

    def test_simultaneous_camera_and_screen_request(self):
        self.assertTrue(wants_both("Mira la webcam y mi pantalla al mismo tiempo"))
        self.assertTrue(wants_both("Analiza lo que ves en cámara y monitor"))
        self.assertFalse(wants_both("Mira mi pantalla"))
    def test_explicit_requests(self):
        for text in (
            "¿Qué ves en pantalla?",
            "¿Qué me puedes decir de lo que ves en pantalla?",
            "Mira mi pantalla y explícame el error.",
            "Lee lo que hay en mi pantalla.",
        ):
            with self.subTest(text=text):
                self.assertTrue(wants_screen(text))

    def test_other_requests(self):
        for text in (
            "Hola.",
            "¿Hay una forma de bloquear la pantalla?",
            "Por favor no mires mi pantalla.",
            "Explícame qué es una pantalla OLED.",
        ):
            with self.subTest(text=text):
                self.assertFalse(wants_screen(text))
