# Configuration

The optional TOML file is `$XDG_CONFIG_HOME/free-hands/config.toml` (normally
`~/.config/free-hands/config.toml`). Example:

```toml
agent_name = "DOOM"
codex_command = "codex app-server --stdio"
model = "gpt-5.6-luna"
model_reasoning_effort = "medium"
speech_gain = 2.0
piper_voice = "alex"
project = "default"
```

Runtime data and the private socket live below `$XDG_DATA_HOME/free-hands` and
`$XDG_RUNTIME_DIR/free-hands`. Directories are mode `0700`; the control socket
is mode `0600`. Do not put tokens or passwords in this file.
