# Security model

FREE-HANDS is a single-user local integration. The daemon accepts commands
only over a user-owned Unix socket, uses private runtime/data directories, and
passes external commands as argument arrays. User text is never executed as a
shell command. Visual capture is gated by intent, temporary, and deleted after
the turn. Do not run the service with elevated privileges.

Review changes to `screen.py`, `speech.py`, `service.py`, `config.py`, systemd,
and widget QML with extra care. See the repository-level [security policy](../SECURITY.md)
for reporting instructions.
