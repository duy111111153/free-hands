"""On-demand capture of the focused Hyprland monitor."""

import json
import os
import re
import select
import shutil
import subprocess
import threading
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from unicodedata import normalize


_CAMERA = r"(?:camara(?: web)?|(?:web|wep|gueb)\s*cam(?:era)?)"
_SCREEN = r"(?:pantallas?|monitor(?:es)?|escritorio|display|pantallazo|screenshot)"
_SOURCE = re.compile(r"\b(?:(?P<camera>" + _CAMERA + r")|(?P<screen>" + _SCREEN + r"))\b")
_ACTION = (
    r"mir(?:a|es?|ar)|observ(?:a|es?|ar)|revis(?:a|es?|ar)|chequ(?:ea|ees?|ear)|"
    r"fij(?:ate|es|ar(?:te)?)|ech(?:a(?:le|r)?|es?)|peg(?:a(?:le)?|ues?)|"
    r"analiz(?:a|as?|ar|es?)|describ(?:e(?:me)?|as?|ir)|le(?:e(?:me)?|as?|er)|"
    r"inspeccion(?:a|es?|ar)|examin(?:a|es?|ar)|interpret(?:a|es?|ar)|"
    r"comprueb(?:a|es?)|compr(?:obar|obemos)|verifi(?:ca|ques?|car)|"
    r"captur(?:a|es?|ar)|tom(?:a|es?|ar)|sac(?:a|as?|ar|ques?)|"
    r"muestr(?:a(?:me)?|es?)|mostr(?:ar|arme)|ensena(?:me|r|s)?|"
    r"acced(?:e|es|as?|er)|conect(?:a(?:te)?|es?|ar(?:te)?)|"
    r"abr(?:e(?:la)?|as?|ir)|activ(?:a(?:la)?|es?|ar)|enciend(?:e|as?)|encender|"
    r"prend(?:e|as?|er)|us(?:a|es?|ar)|ve(?:r|as?|amos|me)|verme"
)
_COMMAND = re.compile(r"\b(?:" + _ACTION + r")\b")
_CLAUSE = re.compile(
    r"[,;.!?¡¿…\n]+|\b(?:pero|sino|aunque)\b|\by\s+(?=(?:no|nunca|" + _ACTION + r")\b)"
)
_NEGATION = re.compile(
    r"\b(?:no|nunca|sin)\s+(?:(?:quiero(?: que)?|puedes?|"
    r"debes?|necesitas|hace falta|por favor|vuelvas a|hace falta que)\s+)*"
    r"(?:" + _ACTION + r"|quiero|necesito|te estoy mostrando)\b"
)
_HOW_TO = re.compile(
    r"\b(?:como|tutorial para|manual para|guia para)\s+"
    r"(?:(?:puedo|puedes|podria|se puede|debo|logro|hacer para|hago para)\s+)?"
    r"(?:configurar|instalar|reparar|habilitar|deshabilitar|" + _ACTION + r")\b"
)
_SHOWING = re.compile(
    r"\b(?:te\s+(?:estoy\s+)?(?:mostrando|ensenando|muestro|enseno)|"
    r"estoy\s+(?:mostrando|ensenando|sosteniendo))\b"
)
_QUESTION = re.compile(r"\b(?:que|cual(?:es)?|donde|cuantos?)\b")
_VISIBLE = re.compile(
    r"\b(?:ves|miras|observas|distingues|detectas|identificas|reconoces|notas|"
    r"alcanzas a (?:ver|distinguir|leer|identificar)|"
    r"estas\s+(?:viendo|mirando|observando|distinguiendo|leyendo)|"
    r"se\s+(?:ve|muestra|lee|alcanza a ver)|me veo|hay|aparece|sale|dice|figura|"
    r"esta\s+(?:mostrando|saliendo|apareciendo))\b"
)
_LOCATION = re.compile(
    r"\b(?:en|por|ante|frente a|delante de|a traves de|desde)\s+"
    r"(?:(?:la|el|mi|tu|esta|este|mis|las|los)\s+)*$"
)
_POINTING = re.compile(r"\b(?:est[eoas]|es[eoas]|aqui|ahi|ahora|ahorita|en vivo)\b")
_COORDINATED = re.compile(
    r"^\s+(?:y(?:\s+tambien)?|e|mas|junto con|ademas de)\s+"
    r"(?:(?:en|por|desde)\s+)?(?:(?:mi|mis|la|el|las|los)\s+)*$"
)
_OTHER_MEDIA = re.compile(r"\b(?:foto|imagen|video|archivo|captura|enlace)\b")
_IMPLICIT_LOOK = re.compile(
    r"\b(?:mira|observa|fijate|chequea|revisa|analiza)\s+(?:esto|aqui|ahi)\b"
)
_CAPTURE_NOUN = re.compile(r"\b(?:haz|toma|saca|captura|manda|dame)\b.{0,30}\b(?:pantallazo|screenshot)\b")


def vision_intent(text: str, *, implied: tuple[bool, bool] = (True, False)) -> tuple[bool, bool]:
    """Return (camera, screen) using the action, its source and local negation."""
    plain = "".join(char for char in normalize("NFD", text.casefold()) if char.isascii())
    plain = re.sub(r"[ \t]+", " ", plain)
    requested: set[str] = set()
    denied: set[str] = set()
    implicit = False
    for clause in _CLAUSE.split(plain):
        matches = list(_SOURCE.finditer(clause))
        if _HOW_TO.search(clause):
            continue
        negative = _NEGATION.search(clause)
        if negative or re.match(r"\s*(?:no|nunca|sin)\s+", clause):
            denied.update(match.lastgroup for match in matches if negative is None or match.start() >= negative.start())
            continue

        pointing = bool(_POINTING.search(clause))
        question = bool(_QUESTION.search(clause)) or (
            (pointing or "como me veo" in clause) and bool(re.search(r"\bcomo\b", clause))
        )
        showing = bool(_SHOWING.search(clause))
        if not matches:
            if not _OTHER_MEDIA.search(clause) and (_IMPLICIT_LOOK.search(clause) or (question and showing)):
                implicit = True
            continue

        previous = None
        previous_requested = False
        for match in matches:
            prefix = clause[:match.start()]
            immediate = prefix[previous.end():] if previous else prefix
            located = bool(_LOCATION.search(prefix))
            affirmative = (
                bool(_COMMAND.search(immediate))
                or (located and (showing or (question and _VISIBLE.search(prefix))))
                or (located and question and pointing
                    and bool(re.search(r"\b(?:es|tengo|sostengo|parece|identificas|dirias|crees|reconoces)\b", prefix)))
                or (previous_requested and bool(_COORDINATED.fullmatch(immediate)))
                or (match.lastgroup == "screen" and bool(_CAPTURE_NOUN.search(clause)))
            )
            if affirmative:
                requested.add(match.lastgroup)
            previous, previous_requested = match, affirmative
    if implicit and not _SOURCE.search(plain):
        requested.update(source for source, enabled in zip(("camera", "screen"), implied) if enabled)
    return "camera" in requested - denied, "screen" in requested - denied


def wants_camera(text: str) -> bool:
    return vision_intent(text)[0]


def wants_screen(text: str) -> bool:
    return vision_intent(text)[1]


def wants_both(text: str) -> bool:
    return all(vision_intent(text))


SHOT_INTERVAL = 0.75
SHOT_COUNT = 3
MAX_JPEG = 1_000_000


@lru_cache(maxsize=8)
def _mjpeg_size(device: str, identity: tuple[int, int, int]) -> str | None:
    # Cache the negotiated format, never a frame. A reconnected device can
    # acquire a new inode even when its /dev/video path stays the same.
    try:
        formats = subprocess.check_output(
            ["v4l2-ctl", "-d", device, "--list-formats-ext"],
            timeout=1, stderr=subprocess.DEVNULL, text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    native = False
    sizes = []
    for line in formats.splitlines():
        if re.match(r"^\s*\[\d+\]:", line):
            native = "'MJPG'" in line
        if native and (match := re.search(r"Size: Discrete (\d+)x(\d+)", line)):
            width, height = map(int, match.groups())
            if 320 <= width <= 960 and height <= 720:
                sizes.append((width, height))
    if sizes:
        width, height = min(sizes, key=lambda size: size[0] * size[1])
        return f"{width}x{height}"
    return None


def _camera_commands():
    stable = sorted(Path("/dev/v4l/by-id").glob("*-video-index0"))
    devices = dict.fromkeys(path.resolve() for path in [*stable, *sorted(Path("/dev").glob("video[0-9]*"))])
    base = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin"]
    for device in devices:
        try:
            stat = device.stat()
        except OSError:
            continue
        size = _mjpeg_size(str(device), (stat.st_ino, stat.st_rdev, stat.st_ctime_ns))
        if size:
            yield [*base, "-f", "v4l2", "-input_format", "mjpeg", "-video_size", size,
                   "-i", str(device), "-c:v", "copy", "-f", "image2pipe", "pipe:1"]
        yield [*base, "-f", "v4l2", "-i", str(device), "-vf", "fps=8,scale=640:-2",
               "-threads", "1", "-q:v", "7", "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1"]


def _jpeg_frames(stream, deadline, check_cancel):
    data = bytearray()
    fd = stream.fileno()
    while monotonic() < deadline:
        check_cancel()
        if not select.select([fd], [], [], min(0.15, max(0, deadline - monotonic())))[0]:
            continue
        block = os.read(fd, 65536)
        if not block:
            return
        data.extend(block)
        while True:
            start = data.find(b"\xff\xd8")
            if start < 0:
                del data[:-1]
                break
            del data[:start]
            end = data.find(b"\xff\xd9", 2)
            if end < 0:
                if len(data) > MAX_JPEG:
                    raise ScreenCaptureError("La webcam entregó una imagen demasiado grande.")
                break
            end += 2
            if end <= MAX_JPEG:
                yield bytes(data[:end])
            del data[:end]


def _write_private(path: Path, data: bytes):
    temporary = path.with_suffix(".tmp")
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
        stream.write(data)
    temporary.replace(path)


def capture_camera(folder: Path, on_frame, check_cancel):
    """Use one camera stream and release it before the model sees the shots."""
    if not shutil.which("ffmpeg"):
        raise ScreenCaptureError("FFmpeg no está instalado para abrir la webcam.")
    for command in _camera_commands():
        check_cancel()
        shots = []
        last_preview = float("-inf")
        sequence = 0
        next_shot = None
        try:
            camera = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError:
            continue
        try:
            for frame in _jpeg_frames(camera.stdout, monotonic() + 5, check_cancel):
                check_cancel()
                now = monotonic()
                if next_shot is None:
                    next_shot = now + SHOT_INTERVAL
                took_shot = now >= next_shot
                if took_shot:
                    path = folder / f"shot-{len(shots) + 1}.jpg"
                    _write_private(path, frame)
                    shots.append(path)
                    next_shot += SHOT_INTERVAL
                if took_shot or now - last_preview >= 1 / 6:
                    sequence += 1
                    slot = sequence % 3
                    _write_private(folder / f"preview-{slot}.jpg", frame)
                    on_frame(sequence, len(shots))
                    last_preview = now
                if len(shots) == SHOT_COUNT:
                    return tuple(shots)
        finally:
            camera.terminate()
            try:
                camera.wait(timeout=0.4)
            except subprocess.TimeoutExpired:
                camera.kill()
                camera.wait()
            camera.stdout.close()
        if sequence:
            break
    raise ScreenCaptureError("No pude obtener las tres tomas. Revisa el permiso de la webcam y si otra aplicación la está usando.")


class ScreenCaptureError(RuntimeError):
    pass


@contextmanager
def screen_image():
    with TemporaryDirectory(prefix="voz-pantalla-") as folder:
        path = Path(folder) / "pantalla.jpg"
        try:
            info = subprocess.check_output(
                ["hyprctl", "-j", "monitors"], timeout=2, stderr=subprocess.DEVNULL,
            )
            monitor = next(item for item in json.loads(info) if item.get("focused"))
            logical_long_edge = max(monitor["width"], monitor["height"]) / monitor["scale"]
            scale = min(monitor["scale"], 1280 / logical_long_edge)
            def capture(target, quality=82):
                subprocess.run(["grim", "-o", monitor["name"], "-s", f"{scale:.4f}", "-t", "jpeg",
                                "-q", str(quality), str(target)], check=True, timeout=3,
                               stderr=subprocess.DEVNULL)
            capture(path)
            if not path.stat().st_size:
                raise ValueError("Captura vacía")
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, StopIteration,
                ZeroDivisionError) as error:
            raise ScreenCaptureError("No pude capturar el monitor activo de Hyprland.") from error
        preview = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "free-hands" / "screen-preview.jpg"
        stop = threading.Event()
        preview.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        def publish_screen():
            temporary = preview.with_suffix(".tmp.jpg")
            while not stop.wait(1.0):
                try:
                    capture(temporary, 65)
                    temporary.replace(preview)
                except (OSError, subprocess.SubprocessError):
                    break
        worker = threading.Thread(target=publish_screen, daemon=True)
        worker.start()
        try:
            yield path
        finally:
            stop.set()
            try:
                preview.unlink()
            except FileNotFoundError:
                pass
