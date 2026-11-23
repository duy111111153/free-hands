# Security policy

Please report vulnerabilities privately to the repository owner rather than
opening a public issue. Do not include transcripts, screenshots, webcam files,
audio, tokens, Codex exports, or databases in a report.

The daemon is intended for one local user. Its Unix socket is created below
`$XDG_RUNTIME_DIR/free-hands` with mode `0600`; runtime and data directories
are created with mode `0700`. Visual capture is opt-in through intent detection,
uses private temporary files, and is deleted after the turn.

If a report contains private data, redact it and describe the smallest synthetic
reproduction possible. Include the affected version, operating system, and
whether the issue involves audio, screen/webcam capture, the socket, history,
or installation.
