# Architecture

Handy sends text to the local Unix socket. `free_hands.service.Service` routes
the request, applies DOOM's local persona and RAG context, manages explicit
visual capture, and records metadata in SQLite. `CodexClient` talks to Codex
App Server and preserves the active thread. `Speech` narrates the response
through Kokoro, Piper, or eSpeak NG. The Omarchy widget reads a short-lived
task JSON file and never needs database access.

The task snapshot carries separate webcam and screen sessions with independent
frame and shot counters, a chart flag for the private SVG, and a mute flag for
the current turn. Capture publishes images before advancing the corresponding
counter. Mute reaches the speech worker while the Codex request continues.

The graph export is generated under local data storage, not the repository.
The `voz_codex` Python namespace remains a compatibility alias for older local
plugins during migration.
