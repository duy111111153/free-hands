# Camera and screen capture

Capture is opt-in. DOOM opens the webcam or focused screen only when the
request contains an affirmative visual intent; negated requests and technical
questions about cameras do not activate it. Say “¿Qué diría que ve en mi webcam?”
or “Revisa mi pantalla” to select a source. Capture runs on Linux through
FFmpeg/V4L2 or Hyprland/grim, independently of Chrome.

Each source takes four JPEGs approximately 750 ms apart. Its task card shows
the preview, a brief flash per shot, four thumbnails as they arrive, and the
response text below. Webcam preview updates up to six times per second. The
screen preview updates at each shot. For a combined request the captures run
in parallel, and Codex receives screen shots first, then webcam shots.

The webcam closes before analysis. Private JPEGs are available to the widget
during analysis and for up to 23 seconds afterward. Cancellation and capture
errors discard temporary files. Codex receives the selected JPEGs as turn
attachments. Move passwords or other sensitive material out of view before
requesting capture.
