from __future__ import annotations

import os
from pathlib import Path


def xdg(name: str, fallback: str) -> Path:
    return Path(os.environ.get(name, fallback)).expanduser()


APP_DIR = "free-hands"
LEGACY_APP_DIR = "voz-codex"
CONFIG_HOME = xdg("XDG_CONFIG_HOME", "~/.config") / APP_DIR
DATA_HOME = xdg("XDG_DATA_HOME", "~/.local/share") / APP_DIR
RUNTIME_HOME = xdg("XDG_RUNTIME_DIR", "/tmp") / APP_DIR
CONFIG_FILE = CONFIG_HOME / "config.toml"
DB_FILE = DATA_HOME / "free-hands.sqlite3"
SOCKET_FILE = RUNTIME_HOME / "control.sock"
TASK_FILE = RUNTIME_HOME / "task.json"
CODEX_SOCKET = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "app-server-control/app-server-control.sock"

MAX_SPEECH_GAIN = 8.0


def clamp_speech_gain(gain: float) -> float:
    try:
        return min(MAX_SPEECH_GAIN, max(0.5, float(gain)))
    except (TypeError, ValueError):
        return 2.0


def ensure_dirs() -> None:
    for path in (CONFIG_HOME, DATA_HOME, RUNTIME_HOME):
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            path.chmod(0o700)
        except OSError:
            pass


def migrate_legacy_state() -> bool:
    """Move legacy local state once, without copying secrets into the repo."""
    legacy_config = CONFIG_HOME.parent / LEGACY_APP_DIR
    legacy_data = DATA_HOME.parent / LEGACY_APP_DIR
    legacy_runtime = RUNTIME_HOME.parent / LEGACY_APP_DIR
    changed = False
    for old, new in ((legacy_config, CONFIG_HOME), (legacy_data, DATA_HOME), (legacy_runtime, RUNTIME_HOME)):
        if old == new or not old.exists() or new.exists():
            continue
        new.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        old.rename(new)
        new.chmod(0o700)
        changed = True
    return changed


def load() -> dict:
    migrate_legacy_state()
    ensure_dirs()
    data = {
        "agent_name": "DOOM",
        "codex_command": "codex app-server --stdio",
        "model": "gpt-5.6-luna",
        # Luna 5.6 medium is the requested implementation profile. Voice and
        # routing remain local so this setting only affects Codex answers.
        "model_reasoning_effort": "medium",
        "overlay_corner": "top-right",
        "speech_command": "",
        "speech_gain": 2.0,
        "piper_voice": "alex",
        "project": "default",
    }
    if CONFIG_FILE.exists():
        try:
            import tomllib
            parsed = tomllib.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            for section in parsed.values():
                if isinstance(section, dict):
                    data.update(section)
            data.update({k: v for k, v in parsed.items() if not isinstance(v, dict)})
        except (OSError, ValueError):
            pass
    return data
