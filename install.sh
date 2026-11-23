#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
chmod +x "$ROOT/free-hands" "$ROOT/handy/free-hands-transcription"
mkdir -p "$HOME/.config/systemd/user"
install -m 0644 "$ROOT/systemd/free-hands.service" "$HOME/.config/systemd/user/free-hands.service"
mkdir -p "$HOME/.config/omarchy/plugins/local.free-hands"
install -m 0644 "$ROOT"/omarchy/local.free-hands/* "$HOME/.config/omarchy/plugins/local.free-hands/"
printf '%s\n' 'FREE-HANDS files installed. Run systemctl --user daemon-reload and enable free-hands.service.'
