# Troubleshooting

Run `./free-hands doctor`, then inspect `systemctl --user status
free-hands.service` and `journalctl --user -u free-hands.service`.

- No dictation: verify Handy and `handy/free-hands-transcription` can reach the
  socket.
- No answer: verify Codex authentication and `codex app-server --stdio`.
- No voice: verify PipeWire and one of Piper, Kokoro, or eSpeak NG.
- No camera: verify FFmpeg, `/dev/video*`, and user permissions. Technical
  camera questions do not intentionally activate capture.
- Stale widget: reinstall `omarchy/local.free-hands` and restart Quickshell.
- Migration issue: stop the service, preserve the old `voz-codex` directories,
  and report the exact doctor output without private data.
