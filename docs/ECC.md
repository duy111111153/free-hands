# Development with ECC

ECC is the official `affaan-m/ECC` Codex plugin used as development guidance;
it does not run inside DOOM and is optional for the runtime.

## Install and verify

```bash
codex plugin marketplace add affaan-m/ECC
codex plugin add ecc@ecc
codex plugin list --json
```

Use the active `CODEX_HOME` and verify one `ecc@ecc` entry is enabled. Do not
also run the legacy `sync-ecc-to-codex.sh` installer. Record the installed
version, date, and source in the release notes when updating it. Start a new
Codex session and verify `$configure-ecc` is available.

## Workflow and updates

Plan first, implement narrowly, review security-sensitive diffs, then run the
tests and `git diff --check`. Keep only repository-specific rules here; do not
copy all ECC agents or commands into the project. Update with the same official
marketplace commands, verify the enabled version, and remove with the plugin
manager if necessary. Disabling or removing ECC must not change DOOM's config,
history, socket, or runtime behavior.
