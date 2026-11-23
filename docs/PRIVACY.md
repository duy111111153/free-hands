# Privacy

History, RAG indexes, graph exports, logs, audio, screenshots, webcam frames,
and model files are local data. They are excluded by `.gitignore` and are not
automatically sent to third-party services. A requested visual turn may send
its temporary images to the configured Codex service as attachments; this is
the only expected image transfer.

To erase local data, stop the service and remove the three `free-hands`
directories under XDG config, data, and runtime. Keep a backup first if chat
continuity matters.
