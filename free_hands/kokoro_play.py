"""Synthesize and play one phrase at a time with Kokoro."""

import json
import re
import shutil
import subprocess
import sys
import wave
from itertools import chain
from queue import Empty, Queue
from threading import Thread
from time import monotonic
from functools import lru_cache
from pathlib import Path

import numpy as np
import onnxruntime as ort
from kokoro_onnx import Kokoro

from config import clamp_speech_gain
from pronunciation import NAMES


ENGLISH = set(
    "the this that these those you your it it's is are was were will would could should "
    "please thanks thank hello good morning welcome today tomorrow how what where when "
    "open close check click save restart run install download update works ready "
    "and or with from for into on of a an our have has can not all next first "
    "step settings file browser website name example test".split()
)
SPANISH = set(
    "el la los las un una de del en con por para que esto esta está y o si sí "
    "abre revisa funciona gracias puedes una es al pero tu su se lo".split()
)

CUES = {
    "momento": "Un momento.",
    "segundo": "Dame un segundo.",
    "revisar": "Déjame revisar eso.",
    "investigar": "Déjame investigar un momento.",
    "break": "Dame un break, estoy ordenando la respuesta.",
    "chance": "Espérame un chance, ya vuelvo con eso.",
    "deuna": "De una, ya me pongo con eso.",
    "suave_nano": "Suave, ñaño, voy por partes.",
}


def bilingual_phonemes(text, phonemize):
    fragments = re.split(r'([,;:!?“”"–—]|\s+\by\b\s+)', text)
    result = []
    for fragment in fragments:
        words = re.findall(r"[^\W\d_]+(?:'[^\W\d_]+)?", fragment.casefold())
        english = sum(word in ENGLISH for word in words)
        spanish = sum(word in SPANISH for word in words)
        if english >= 2 and english > spanish:
            result.append(phonemize(fragment, "en-us"))
        elif not any(char.isalnum() for char in fragment):
            result.append(fragment.strip())
        else:
            start = 0
            for name in NAMES.finditer(fragment):
                if fragment[start:name.start()].strip():
                    result.append(phonemize(fragment[start:name.start()], "es"))
                result.append(phonemize(name[0], "en-us"))
                start = name.end()
            if fragment[start:].strip():
                result.append(phonemize(fragment[start:], "es"))
    return re.sub(r"\s+([,;:.!?])", r"\1", " ".join(filter(None, result))).strip()


def phrases(text):
    for line in text.splitlines():
        parts = [part.strip() for part in re.split(r"(?<=[.!?…])\s+", line) if part.strip()]
        for index, part in enumerate(parts):
            while len(part) > 235:
                pauses = list(re.finditer(r"[,;:][ \t]+", part[100:215]))
                end = 100 + pauses[-1].end() if pauses else part.rfind(" ", 0, 215)
                if end <= 0:
                    end = 215
                yield part[:end].strip(), 0.04 if pauses else 0.01
                part = part[end:].lstrip()
            pause = 0.18 if part.endswith("…") else (0.07 if index == len(parts) - 1 else 0.03)
            yield part, pause


def load_voice(models: Path):
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.add_session_config_entry("session.intra_op.allow_spinning", "0")
    session = ort.InferenceSession(
        str(models / "kokoro-v1.0.int8.onnx"), options, providers=["CPUExecutionProvider"]
    )
    return Kokoro.from_session(session, str(models / "voices-v1.0.bin"))


def loud_pcm(samples, rate: int, gain: float) -> bytes:
    """Boost quiet speech with a smooth RMS envelope and a soft peak ceiling."""
    if not samples.size:
        return b""
    boosted = samples * gain
    width = max(1, rate // 50)
    blocks = np.arange(0, len(boosted), width)
    counts = np.minimum(width, len(boosted) - blocks)
    rms = np.sqrt(np.add.reduceat(boosted * boosted, blocks) / counts)
    attenuation = np.maximum(1, rms / 0.17) ** -0.74
    envelope = np.interp(np.arange(len(boosted)), blocks + (counts - 1) / 2, attenuation)
    boosted *= envelope
    magnitude = np.abs(boosted)
    peaks = magnitude > 0.70
    boosted[peaks] = np.sign(boosted[peaks]) * (0.70 + 0.27 * np.tanh((magnitude[peaks] - 0.70) / 0.27))
    return np.rint(boosted * 32767).astype("<i2").tobytes()


def make_synthesizer(tts, voice, gain: float = 2.0):
    ffmpeg = shutil.which("ffmpeg") if voice == "em_alex" else None
    @lru_cache(maxsize=16)
    def cached(phrase):
        return synthesize(phrase)

    def synthesize(phrase):
        phonemes = bilingual_phonemes(phrase, tts.tokenizer.phonemize)
        phonemes = "".join(char for char in phonemes if char in tts.tokenizer.vocab)
        if not any(char.isalpha() for char in phonemes):
            return b"", 24000
        audio, rate = tts.create(phonemes, voice=voice, speed=1.04, is_phonemes=True)
        boosted = np.asarray(audio, dtype=np.float32) * (gain if gain <= 2.0 else 1.0)
        peak = float(np.max(np.abs(boosted))) if boosted.size else 0.0
        if peak > 0.98:
            boosted *= 0.98 / peak
        pcm = np.rint(np.clip(boosted, -0.98, 0.98) * 32767).astype("<i2").tobytes()
        if ffmpeg and pcm:
            result = subprocess.run(
                [ffmpeg, "-loglevel", "error", "-f", "s16le", "-ar", str(rate),
                 "-ac", "1", "-i", "pipe:0", "-af", "rubberband=pitch=0.96:formant=preserved",
                 "-f", "s16le", "pipe:1"],
                input=pcm, capture_output=True,
            )
            if result.returncode == 0 and result.stdout:
                pcm = result.stdout
        if gain > 2.0:
            return loud_pcm(np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768, rate, gain), rate
        return pcm, rate

    return lambda phrase: cached(phrase) if len(phrase) <= 48 else synthesize(phrase)


def audio_chunks(tts, text, voice, synthesize=None):
    synthesize = synthesize or make_synthesizer(tts, voice)
    pause = 0
    for phrase, following_pause in phrases(text):
        pcm, rate = synthesize(phrase)
        if pcm:
            yield bytes(round(rate * pause) * 2) + pcm, rate
            pause = following_pause


def play_narration(texts, tts, voice, synthesize, on_first=None, *, buffer_long=False):
    """Keep a bounded reserve of speech while PipeWire plays the opening."""
    queue = Queue(maxsize=6)
    errors = []

    def produce():
        try:
            for text in texts:
                for chunk in audio_chunks(tts, text, voice, synthesize):
                    queue.put(chunk)
        except Exception as error:
            errors.append(error)
            # Consume through the end marker before accepting another request.
            for _ in texts:
                pass
        finally:
            queue.put(None)

    producer = Thread(target=produce, daemon=True)
    producer.start()
    chunks = iter(queue.get, None)
    if buffer_long:
        first = next(chunks, None)
        if first is not None:
            reserve = [first]
            seconds = len(first[0]) / (2 * first[1])
            deadline = monotonic() + 5
            while seconds < 7:
                try:
                    chunk = queue.get(timeout=max(0, deadline - monotonic()))
                except Empty:
                    break
                if chunk is None:
                    chunks = iter(())
                    break
                reserve.append(chunk)
                seconds += len(chunk[0]) / (2 * chunk[1])
            chunks = chain(reserve, chunks)
    try:
        result = play(chunks, on_first)
    finally:
        for _ in chunks:
            pass
        producer.join()
    if errors:
        raise errors[0]
    return result


def render(text: str, models: Path, voice: str, gain: float = 2.0) -> tuple[bytes, int]:
    tts = load_voice(models)
    synthesize = make_synthesizer(tts, voice, gain)
    chunks = list(audio_chunks(tts, text, voice, synthesize))
    return (b"".join(pcm for pcm, _ in chunks), chunks[0][1]) if chunks else (b"", 24000)


def cache_cues(models: Path, voice: str, target: Path, gain: float = 2.0) -> None:
    """Render short conversational cues once so response latency stays low."""
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    tts = load_voice(models)
    synthesize = make_synthesizer(tts, voice, gain)
    for name, phrase in CUES.items():
        pcm, rate = synthesize(phrase)
        temporary = target / f"{name}.wav.tmp"
        with wave.open(str(temporary), "wb") as stream:
            stream.setparams((1, 2, rate, 0, "NONE", "not compressed"))
            stream.writeframes(pcm)
        temporary.replace(target / f"{name}.wav")


def play(chunks, on_first=None) -> int:
    chunks = iter(chunks)
    first = next(chunks, None)
    if first is None:
        return 0
    pcm, rate = first
    with subprocess.Popen(
        ["pw-play", "--volume", "1.0", "--raw", "--format", "s16", "--channels", "1",
         "--rate", str(rate), "--latency", "150ms", "-"],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
    ) as player:
        try:
            with player.stdin as stream:
                stream.write(pcm)
                stream.flush()
                if on_first:
                    on_first()
                for pcm, _ in chunks:
                    stream.write(pcm)
                    stream.flush()
        except BrokenPipeError:
            return player.wait() or 1
        return player.wait()


def main() -> int:
    models, voice = Path(sys.argv[1]), sys.argv[2]
    args = sys.argv[3:]
    gain = 2.0
    if "--gain" in args:
        gain = clamp_speech_gain(args[args.index("--gain") + 1])
    if "--cache-cues" in args:
        target = Path(args[args.index("--cache-cues") + 1])
        cache_cues(models, voice, target, gain)
        return 0
    if "--serve" in args:
        tts = load_voice(models)
        synthesize = make_synthesizer(tts, voice, gain)
        synthesize("Hola.")
        print("ready", flush=True)
        lines = iter(sys.stdin)

        def narration_texts(first):
            yield first
            for line in lines:
                text = json.loads(line)
                if text is None:
                    return
                yield text

        for line in lines:
            try:
                payload = json.loads(line)
                if payload is None:
                    continue
                texts = narration_texts(payload["narration"]) if isinstance(payload, dict) else iter((payload,))
                result = play_narration(
                    texts, tts, voice, synthesize, on_first=lambda: print("audio", flush=True),
                    buffer_long=payload.get("buffer_long", False) if isinstance(payload, dict) else len(payload) > 900,
                )
            except Exception as error:
                print(f"Kokoro: {error}", file=sys.stderr)
                result = 1
            print(f"done {result}", flush=True)
        return 0
    text = sys.stdin.read().strip()
    if text:
        tts = load_voice(models)
        synthesize = make_synthesizer(tts, voice, gain)
        return play_narration(iter((text,)), tts, voice, synthesize)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
