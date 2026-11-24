# Voice and audio

DOOM prefers the configured local speech command, then Piper/Kokoro, and falls
back to eSpeak NG. `speech_gain` is clamped to a safe range and speech can be
cancelled with `free-hands cancel`. Temporary WAV data is not logged or
committed. Configure a voice in `config.toml`; use `FREE_HANDS_VOICE` for the
eSpeak fallback (`VOZ_CODEX_VOICE` remains accepted for migration).

Select **Silenciar voz** on a regular task card to stop the current audio and
keep the turn running silently. The next request restores voice automatically.
The equivalent command is `free-hands mute --task-id ID`.
