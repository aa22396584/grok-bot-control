# Maintaining Grok Bot Control

This repository contains a portable workflow plugin and offline decision helpers. Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing behavior.

- Maintain the workflow once under `plugins/grok-bot-control/skills/grok-bot-control/`. Host manifests expose that shared skill; they do not supply computer-use tools or account access.
- Edit `release.json`, then run `python3 scripts/sync_metadata.py` for generated manifests, catalogs, and matching skill versions. Keep the Codex marketplace name stable. Do not edit installed caches.
- Keep helpers standard-library-only, read-only, and offline. Put behavior regressions in the skill's tests and packaging/metadata regressions in root `tests/`.
- Run both unittest suites, metadata/privacy/release checks, reviewer cases, and archive build from [RELEASING.md](docs/RELEASING.md). Run the native host validators available locally.
- Use synthetic fixtures. Runtime state and private deployment configuration belong outside this public repository.
- Report source tests, host installation/discovery, live UI behavior, GitHub release, and official directory acceptance as separate evidence.
- For publication, merge through required CI and tag the matching version on main. Never replace a published version's assets or move its tag.
