# Installation

## Requirements

Use Omarchy or a compatible Linux desktop with Python 3.11+, Git, Node.js
(needed by some Codex installations), Codex CLI/App Server, Handy, FFmpeg,
PipeWire, and `notify-send`. Piper, Kokoro, or eSpeak NG provides speech.
The recommended baseline is 4 CPU cores, 8 GB RAM, and 2 GB free disk before
voice models.

```bash
git clone https://github.com/duy111111153/free-hands.git ~/Work/free-hands
cd ~/Work/free-hands
chmod +x free-hands handy/free-hands-transcription
./free-hands doctor
```

## Service and widget

```bash
mkdir -p ~/.config/systemd/user
install -m 0644 systemd/free-hands.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now free-hands.service

mkdir -p ~/.config/omarchy/plugins/local.free-hands
install -m 0644 omarchy/local.free-hands/* ~/.config/omarchy/plugins/local.free-hands/
omarchy plugin enable local.free-hands --section right
```

Configure Handy's paste method as `None` or `External Script` and point it to
`handy/free-hands-transcription`. Alt+Z remains Handy's recording control.

## Migration

On first start, FREE-HANDS migrates `~/.config/voz-codex`,
`~/.local/share/voz-codex`, and the matching runtime directory only when the
new destination does not exist. It moves local configuration and SQLite
history; it does not read or copy secrets into the repository. The old
`~/Work/voz-codex` checkout and `local.voz-tracker` plugin are left untouched
so rollback is possible. Copy the widget manually after checking the new
service.

## Voice and permissions

Speech models stay under `$XDG_DATA_HOME/free-hands`. Webcam access is only
requested for an explicit visual instruction. PipeWire and camera permissions
must be granted to the current user. See [Voice and audio](VOICE_AND_AUDIO.md)
and [Camera and screen](CAMERA_AND_SCREEN.md).

## Uninstall

```bash
systemctl --user disable --now free-hands.service
rm -f ~/.config/systemd/user/free-hands.service
omarchy plugin disable local.free-hands 2>/dev/null || true
rm -rf ~/.config/omarchy/plugins/local.free-hands
```

Delete `$XDG_CONFIG_HOME/free-hands`, `$XDG_DATA_HOME/free-hands`, and
`$XDG_RUNTIME_DIR/free-hands` only if you also want to remove local settings,
history, and cached graph data.
