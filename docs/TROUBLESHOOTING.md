# Troubleshooting

Run `./free-hands doctor`, then inspect `systemctl --user status
free-hands.service` and `journalctl --user -u free-hands.service`.

- No dictation: verify Handy and `handy/free-hands-transcription` can reach the
  socket.
- No answer: verify Codex authentication and `codex app-server --stdio`.
- No voice: verify PipeWire and one of Piper, Kokoro, or eSpeak NG.
- No camera: verify FFmpeg, `/dev/video*`, and user permissions. Technical
  camera questions do not intentionally activate capture.
- If a reply mentions Chrome, explicitly say “Abre mi webcam y dime qué ves”.
  The images come from the local capture service. The card shows a preview
  and an advancing four-shot strip when local capture starts.
- No display capture: verify `grim`, `hyprctl -j monitors`, and the service's
  Wayland session environment.
- Stale widget: reinstall `omarchy/local.free-hands` and restart Quickshell.
- Migration issue: stop the service, preserve the old `voz-codex` directories,
  and report the exact doctor output without private data.
