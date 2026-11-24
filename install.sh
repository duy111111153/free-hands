#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
launcher="$HOME/.local/bin/free-hands"
mkdir -p "$HOME/.local/bin"
if [ -e "$launcher" ] || [ -L "$launcher" ]; then
    if [ ! -L "$launcher" ] || [ "$(readlink -- "$launcher")" != "$ROOT/free-hands" ]; then
        printf '%s\n' "An existing launcher at $launcher points elsewhere. Move it before continuing." >&2
        exit 1
    fi
else
    ln -s "$ROOT/free-hands" "$launcher"
fi
mkdir -p "$HOME/.config/systemd/user"
install -m 0644 "$ROOT/systemd/free-hands.service" "$HOME/.config/systemd/user/free-hands.service"
install -m 0644 "$ROOT/systemd/handy.service" "$HOME/.config/systemd/user/handy.service"
mkdir -p "$HOME/.local/share/com.pais.handy/hooks"
install -m 0700 "$ROOT/handy/transcription" "$HOME/.local/share/com.pais.handy/hooks/transcription"
install -m 0700 "$ROOT/handy/free-hands-transcription" "$HOME/.local/share/com.pais.handy/hooks/free-hands-transcription"
mkdir -p "$HOME/.config/omarchy/plugins/local.free-hands/i18n"
install -m 0644 "$ROOT"/omarchy/local.free-hands/TaskWidget.qml "$ROOT"/omarchy/local.free-hands/manifest.json "$HOME/.config/omarchy/plugins/local.free-hands/"
install -m 0644 "$ROOT"/omarchy/local.free-hands/i18n/*.json "$HOME/.config/omarchy/plugins/local.free-hands/i18n/"
printf '%s\n' 'FREE-HANDS files installed. Run systemctl --user daemon-reload and enable free-hands.service.'
