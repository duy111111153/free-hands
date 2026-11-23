# Contributing

FREE-HANDS changes should preserve DOOM's local-first behavior. Use synthetic
fixtures for tests. Never commit audio, webcam frames, screenshots, Codex
exports, databases, credentials, model files, or personal paths.

Before opening a pull request, run:

```bash
python -m unittest discover -s tests -q
python -m compileall -q free_hands
git diff --check
```

Changes touching camera, screen, audio, sockets, systemd, or migration code
must include a regression test or a clear explanation of why a test is not
possible. Keep external commands argument-array based and preserve private
permissions on runtime directories and temporary files.

Use the plan/review/verify workflow described in [docs/ECC.md](docs/ECC.md).
