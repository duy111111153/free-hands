# FREE-HANDS

FREE-HANDS is a private, local-first voice bridge for Omarchy/Linux. Its voice
assistant is DOOM: Handy records the request, Codex App Server answers it, and
local speech reads the response back while the Omarchy widget shows progress.

## What it does

- Alt+Z dictation through Handy and a private Unix socket.
- DOOM voice responses with bilingual pronunciation, pauses, and volume control.
- Local SQLite history, chat continuity, topic routing, RAG, and graph export.
- Explicit, intent-gated screen capture and three-shot webcam capture.
- Temporary previews for the Omarchy widget; capture files are private and
  removed after the requested turn.
- Cancellation, follow-up, notifications, and Codex App Server integration.

FREE-HANDS does not upload audio, screenshots, webcam frames, or local history
automatically. A requested visual turn may attach its temporary images to that
Codex turn. See [Camera and screen](docs/CAMERA_AND_SCREEN.md) and
[Privacy](docs/PRIVACY.md).

## Five-minute installation

```bash
git clone https://github.com/duy111111153/free-hands.git ~/Work/free-hands
cd ~/Work/free-hands
chmod +x free-hands handy/free-hands-transcription
./free-hands doctor
```

Install the user service and Omarchy widget after checking the full
[installation guide](docs/INSTALLATION.md). A working setup needs Omarchy or a
compatible Linux desktop, Python 3.11+, Git, Codex CLI/App Server, Handy,
FFmpeg, PipeWire, and a local speech backend (Piper, Kokoro, or eSpeak NG).

## Development

```bash
python -m unittest discover -s tests -q
python -m compileall -q free_hands
git diff --check
```

The development workflow uses the official ECC Codex plugin when available;
ECC is development guidance only and is not part of the DOOM runtime. Read
[Development with ECC](docs/ECC.md) before changing security-sensitive paths.

## Documentation

[Quickstart](docs/QUICKSTART.md) · [Configuration](docs/CONFIGURATION.md) ·
[Architecture](docs/ARCHITECTURE.md) · [Voice and audio](docs/VOICE_AND_AUDIO.md) ·
[Chat memory](docs/CHAT_MEMORY.md) · [RAG and graph](docs/RAG_AND_GRAPH.md) ·
[Troubleshooting](docs/TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md)

## Status and roadmap

FREE-HANDS is an early, single-user Omarchy integration. The initial public
release focuses on reliable local voice, explicit visual capture, privacy, and
reproducible installation. Future work includes broader desktop packaging,
more device fixtures, and additional speech backends.

## License

Apache-2.0. See [LICENSE](LICENSE).
