# Camera and screen capture

Capture is opt-in. DOOM opens the webcam or focused screen only when the
request contains an affirmative visual intent; negated requests and technical
questions about cameras do not activate it. Webcam requests collect three
separate JPEG shots. Files are stored in a mode-`0700` runtime directory,
attached only to the requested Codex turn, and removed when the turn ends or
is cancelled. Failed attempts are discarded and child FFmpeg processes are
closed.

Never use visual capture for passwords, tokens, or other secrets. Check the
preview before sending a visual request.
